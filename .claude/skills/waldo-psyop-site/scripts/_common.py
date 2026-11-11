"""Shared helpers for the waldo-psyop-site scripts (not a command-line tool).

Python 3 standard library plus Pillow only.
"""
import json
import os
import re

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
IMAGE_EXTS = (".jpg", ".png", ".webp")
WORK_DIR = ".waldo-work"  # scratch output (survey tiles, zooms, contact sheets); never commit it


def resolve_case(path):
    """Accept a scene folder or a case.json path. Return (case_path, scene_dir)."""
    if os.path.isdir(path):
        case_path = os.path.join(path, "case.json")
    else:
        case_path = path
    return case_path, os.path.dirname(os.path.abspath(case_path))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_scene_image(path):
    """Accept an image, a scene folder, or a case.json. Return (image_path, label)."""
    if os.path.isfile(path) and not path.endswith(".json"):
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem == "scene":  # scenes/<id>/scene.jpg -> label it <id>
            stem = os.path.basename(os.path.dirname(os.path.abspath(path))) or stem
        return path, stem
    case_path, scene_dir = resolve_case(path)
    label = os.path.basename(scene_dir)
    if os.path.isfile(case_path):
        src = load_json(case_path).get("image", {}).get("src")
        if src and os.path.isfile(os.path.join(scene_dir, src)):
            return os.path.join(scene_dir, src), label
    for ext in IMAGE_EXTS:
        p = os.path.join(scene_dir, "scene" + ext)
        if os.path.isfile(p):
            return p, label
    raise FileNotFoundError(f"no scene image found for {path}")


def font(size):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


STEPS = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000]


def pick_steps(scale, min_major_px=50, min_minor_px=8, force_major=None):
    major = force_major or next((s for s in STEPS if s * scale >= min_major_px), STEPS[-1])
    if force_major:
        while major * scale < min_major_px:
            major *= 2
    minor = next((s for s in STEPS if s < major and major % s == 0 and s * scale >= min_minor_px),
                 major)
    return major, minor


def ruled(src, box, scale, title=None, outline=None, force_major=None):
    """Return an upscaled crop of `src` with rulers labelled in SOURCE-pixel coordinates.

    box = (x0, y0, x1, y1) in source pixels. Source pixel x maps to canvas
    margin + (x - x0) * scale, so labels line up with pixel edges. `outline`
    is an optional (x, y, w, h) source region drawn as a bright rectangle.
    """
    from PIL import Image, ImageDraw

    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    W, H = max(1, round(w * scale)), max(1, round(h * scale))
    crop = src.crop(box).convert("RGB")
    crop = crop.resize((W, H), Image.LANCZOS if scale != 1 else Image.NEAREST)

    f, ft = font(14), font(16)
    m, top = 52, 52 + (26 if title else 0)
    canvas = Image.new("RGB", (W + 2 * m, H + top + m), "white")
    canvas.paste(crop, (m, top))

    major, minor = pick_steps(scale, force_major=force_major)
    grid = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    d = ImageDraw.Draw(canvas)

    def px(x):
        return m + (x - x0) * scale

    def py(y):
        return top + (y - y0) * scale

    start = (x0 // minor) * minor
    for x in range(start, x1 + 1, minor):
        if x < x0:
            continue
        u = px(x)
        big = x % major == 0
        ln = 12 if big else 5
        d.line([(u, top - ln), (u, top)], fill="black")
        d.line([(u, top + H), (u, top + H + ln)], fill="black")
        if big:
            g.line([(u, top), (u, top + H)], fill=(255, 0, 255, 90), width=1)
            d.text((u, top - 14), str(x), fill="black", font=f, anchor="md")
            d.text((u, top + H + 14), str(x), fill="black", font=f, anchor="ma")
    start = (y0 // minor) * minor
    for y in range(start, y1 + 1, minor):
        if y < y0:
            continue
        v = py(y)
        big = y % major == 0
        ln = 12 if big else 5
        d.line([(m - ln, v), (m, v)], fill="black")
        d.line([(m + W, v), (m + W + ln, v)], fill="black")
        if big:
            g.line([(m, v), (m + W, v)], fill=(255, 0, 255, 90), width=1)
            d.text((m - 14, v), str(y), fill="black", font=f, anchor="rm")
            d.text((m + W + 14, v), str(y), fill="black", font=f, anchor="lm")

    canvas = Image.alpha_composite(canvas.convert("RGBA"), grid).convert("RGB")
    d = ImageDraw.Draw(canvas)
    d.rectangle([m - 1, top - 1, m + W, top + H], outline="black")
    if outline:
        ox, oy, ow, oh = outline
        r = [px(ox), py(oy), px(ox + ow), py(oy + oh)]
        d.rectangle([r[0] - 2, r[1] - 2, r[2] + 2, r[3] + 2], outline="black", width=2)
        d.rectangle(r, outline=(0, 230, 255), width=3)
    if title:
        d.text((m, 8), title, fill="black", font=ft)
    return canvas
