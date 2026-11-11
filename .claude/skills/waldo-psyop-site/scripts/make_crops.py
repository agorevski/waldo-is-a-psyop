#!/usr/bin/env python3
"""Cut evidence crops from a scene image using the regions in its case.json.

Usage:
  make_crops.py SCENE_DIR_OR_CASE_JSON [--root DIR] [--scale 6] [--only P01,L2]
                [--sheet .waldo-work/<id>/crops-sheet.png] [--facts] [--no-write] [--force]

Accepts a scene folder (scenes/<id>) or its case.json. image.src and every
asset path are resolved relative to the scene folder (override with --root).
Writes each claim's and lineup suspect's `region` to its `asset` path, upscaled
by --scale (default 6) with LANCZOS, capped at --max-side px (default 1600). --sheet writes a labelled contact sheet so
you can check every crop visually; --facts adds each fact region to the sheet.
--no-write skips writing assets (use it to inspect regions only). Existing
asset files are left alone unless --force is given, so hand-made composite
crops (e.g. several suspects side by side) are never overwritten by accident.
Exits non-zero if case.json or the scene image cannot be read.
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw

from _common import resolve_case


def crop(im, r, scale, max_side=0):
    c = im.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]))
    # Never upscale a big region past max_side: a 1500px region at 6x is a multi-MB PNG.
    if max_side:
        scale = max(1.0, min(scale, max_side / max(r["w"], r["h"])))
    return c.resize((max(1, round(r["w"] * scale)), max(1, round(r["h"] * scale))), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case", help="scene folder (scenes/<id>) or its case.json")
    ap.add_argument("--root", help="folder that case.json paths are relative to (default: the scene folder)")
    ap.add_argument("--scale", type=int, default=6)
    ap.add_argument("--max-side", type=int, default=1600,
                    help="cap the longest side of each written crop (keeps aspect; 0 = no cap)")
    ap.add_argument("--only", help="comma-separated ids to process")
    ap.add_argument("--sheet", help="write a labelled contact sheet PNG here")
    ap.add_argument("--facts", action="store_true", help="include fact regions on the sheet")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite existing asset files")
    a = ap.parse_args()
    case_path, scene_dir = resolve_case(a.case)
    root = a.root or scene_dir
    only = set(a.only.split(",")) if a.only else None

    try:
        with open(case_path, encoding="utf-8") as f:
            d = json.load(f)
        im = Image.open(os.path.join(root, d["image"]["src"])).convert("RGB")
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: cannot load {case_path} or its image: {e}")
        return 1

    tiles = []
    for e in d.get("claims", []) + d.get("lineup", []):
        if only and e["id"] not in only:
            continue
        out = crop(im, e["region"], a.scale, a.max_side)
        if not a.no_write:
            path = os.path.join(root, e["asset"])
            if os.path.exists(path) and not a.force:
                print(f"{e['id']}: {e['asset']} exists, skipped (use --force to overwrite)")
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                out.save(path, optimize=True)
                print(f"{e['id']}: {e['asset']} {out.size[0]}x{out.size[1]}")
        tiles.append((f"{e['id']} {e.get('title') or e.get('name', '')}", out))
        if a.facts:
            for j, fact in enumerate(e.get("facts", [])):
                tiles.append((f"{e['id']}.fact{j}: {fact['text']}", crop(im, fact["region"], a.scale)))

    if a.sheet and tiles:
        tw, th, lh, cols = 360, 300, 46, 4
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * (th + lh)), "white")
        draw = ImageDraw.Draw(sheet)
        for i, (label, t) in enumerate(tiles):
            t = t.copy()
            t.thumbnail((tw - 10, th - 10))
            x, y = (i % cols) * tw, (i // cols) * (th + lh)
            sheet.paste(t, (x + 5, y + 5))
            words, line, lines = label.split(), "", []
            for w in words:
                if len(line) + len(w) + 1 > 52:
                    lines.append(line)
                    line = w
                else:
                    line = f"{line} {w}".strip()
            lines.append(line)
            draw.text((x + 5, y + th), "\n".join(lines[:3]), fill="black")
        os.makedirs(os.path.dirname(os.path.abspath(a.sheet)), exist_ok=True)
        sheet.save(a.sheet)
        print(f"contact sheet: {a.sheet} ({len(tiles)} tiles). Open it and verify every crop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
