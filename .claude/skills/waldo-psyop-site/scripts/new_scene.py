#!/usr/bin/env python3
"""Scaffold a new scene: copy the image, write a case.json skeleton, register it.

Usage: new_scene.py IMAGE [--id ID] [--repo .] [--force]

- Derives the scene id from the file name unless --id is given (for example
  waldo_beach.jpg -> "beach"). Ids must match ^[a-z0-9][a-z0-9-]{0,39}$.
- Refuses to touch an existing scenes/<id>/ unless --force is given. --force
  replaces the image and case.json; it never deletes evidence/ files.
- Copies the image to scenes/<id>/scene.<ext>. JPEG, PNG, and WebP keep their
  format (.jpg/.png/.webp); anything else is converted to .png. A JPEG with an
  EXIF rotation is re-encoded upright so the pixels match what browsers show.
- Writes scenes/<id>/case.json with every required key, the real image size,
  and "TODO" placeholders (validate_case.py rejects every TODO), plus an empty
  scenes/<id>/evidence/ folder.
- Appends {"id": ID} to scenes/index.json (creating it with defaults if missing).

Exits non-zero on any failure.
"""
import argparse
import json
import os
import re
import shutil
import sys

from _common import ID_RE

NOISE = {"waldo", "wheres", "where", "s", "wally", "the", "scene", "img", "image", "final", "copy"}

DEFAULT_MANIFEST = {
    "site": {
        "title": "WALDO IS A PSYOP",
        "subtitle": "The case files. Every scene. Every stripe. Every \"coincidence.\"",
        "intro": [
            "They tell you to FIND him. Have you ever asked yourself ==why he keeps needing to be found?== "
            "One scene is a coincidence. Two is a pattern. I have a whole folder.",
            "Pick a case file. Look at the evidence. Then look at it ~~again~~ AGAIN. I'm just asking questions.",
        ],
        "footer": "This is a parody. Waldo is a fictional character created by Martin Handford. No actual "
                  "investigation occurred. No real person in any picture is identified or targeted.",
    },
    "scenes": [],
}

FOOTER = ("This is a parody. Waldo is a fictional character created by Martin Handford. "
          "No actual investigation occurred.")


def derive_id(path):
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    words = [w for w in re.split(r"[^a-z0-9]+", stem) if w]
    kept = [w for w in words if w not in NOISE] or words or ["scene"]
    slug = "-".join(kept)[:40].strip("-")
    if not slug or not slug[0].isalnum():
        slug = "scene"
    return slug


def skeleton(src, w, h):
    r = {"x": 0, "y": 0, "w": min(10, w), "h": min(10, h)}
    return {
        "image": {"src": src, "width": w, "height": h,
                  "alt": "TODO: one plain sentence describing the scene for screen readers"},
        "site": {
            "title": "TODO: in-character title (ALL CAPS)",
            "subtitle": "TODO: subtitle",
            "caseNumber": "TODO: e.g. CASE #WDE-0000-X",
            "banner": "TODO: mirror-site warning bar",
            "marquee": "TODO: ticker items separated by ★",
            "heroCaption": "TODO: EXHIBIT 0 caption",
            "intro": ["TODO: intro letter paragraph (inline markup allowed)"],
            "hitCounterBase": 1956,
            "lastUpdated": "TODO: e.g. Night 31, 8:30 AM",
            "censusInstructions": "TODO: e.g. Click every striped thing in the scene above.",
        },
        "claims": [{
            "id": "P01", "num": 1,
            "title": "TODO: claim title (ALL CAPS)",
            "region": dict(r),
            "facts": [{"text": "TODO: fact 1 (literally visible)", "region": dict(r)},
                      {"text": "TODO: fact 2 (literally visible, next to fact 1)", "region": dict(r)}],
            "leap": "TODO: one wrong-but-tempting step (inline markup allowed)",
            "update": {"time": "4:12 AM", "text": "TODO: timestamped self-interruption"},
            "note": "TODO: sticky-note scrawl",
            "stamp": "CLASSIFIED",
            "asset": "evidence/TODO.png",
            "alt": "TODO: alt text for the crop",
            "caption": "TODO: polaroid caption",
            "paranoia": 1,
            "links": [{"to": "P01", "label": "TODO: STRING LABEL"}],
        }],
        "lineupReference": {"claim": "P01", "name": "TODO: reference name, e.g. THE STAMP (reference)",
                            "has": ["TODO"], "missing": []},
        "lineup": [{"id": "L1", "name": "TODO: SUSPECT 1: \"NICKNAME\"", "region": dict(r),
                    "asset": "evidence/TODO-suspect-1.png", "alt": "TODO",
                    "has": ["TODO"], "missing": ["TODO"]}],
        "stripes": [{"id": "S01", "label": "TODO: what the striped thing is", "region": dict(r)}],
        "censusComments": ["TODO: census log line"],
        "guestbook": [{"name": "TODO", "date": "TODO", "text": "TODO: a normal reader pushes back",
                       "reply": "TODO: webmaster replies in character", "claim": "P01"}],
        "updates": [{"time": "TODO", "text": "TODO", "claim": "P01"}],
        "receipts": [{"item": "TODO", "price": "TODO", "note": "TODO", "claim": "P01"}],
        "verdict": {"lines": ["TODO: verdict line"], "button": "Request Further Investigation"},
        "cipher": {"cipher": "TODO: ROT13 of plain", "plain": "TODO: LEAD: ... SEE PROOF #N.", "claim": "P01"},
        "footer": FOOTER,
    }


def copy_image(src_path, dest_dir):
    """Copy or convert the image into dest_dir/scene.<ext>. Return (filename, width, height)."""
    from PIL import Image, ImageOps

    with Image.open(src_path) as im:
        fmt = (im.format or "").upper()
        orientation = im.getexif().get(0x0112, 1) if hasattr(im, "getexif") else 1
        ext = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(fmt)
        for old in (".jpg", ".png", ".webp"):
            p = os.path.join(dest_dir, "scene" + old)
            if os.path.exists(p):
                os.remove(p)
        if ext == ".jpg" and orientation not in (None, 1):
            out = ImageOps.exif_transpose(im).convert("RGB")
            name = "scene.jpg"
            out.save(os.path.join(dest_dir, name), quality=92, optimize=True)
        elif ext:
            name = "scene" + ext
            shutil.copyfile(src_path, os.path.join(dest_dir, name))
        else:
            im.seek(0)
            out = im.convert("RGBA" if "A" in im.getbands() or "transparency" in im.info else "RGB")
            name = "scene.png"
            out.save(os.path.join(dest_dir, name), optimize=True)
    with Image.open(os.path.join(dest_dir, name)) as im:
        return name, im.size[0], im.size[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", help="the Where's Waldo scene image")
    ap.add_argument("--id", help="scene id slug (default: derived from the file name)")
    ap.add_argument("--repo", default=".", help="repository root (default .)")
    ap.add_argument("--force", action="store_true", help="replace an existing scene's image and case.json")
    a = ap.parse_args()

    if not os.path.isfile(a.image):
        print(f"ERROR: image not found: {a.image}")
        return 1
    sid = a.id or derive_id(a.image)
    if not ID_RE.match(sid):
        print(f"ERROR: scene id {sid!r} must match ^[a-z0-9][a-z0-9-]{{0,39}}$")
        return 1
    try:
        from PIL import Image
        with Image.open(a.image) as im:
            im.verify()
    except ImportError:
        print("ERROR: Pillow is required (pip install pillow)")
        return 1
    except Exception as e:  # noqa: BLE001 - any decode failure means "not an image"
        print(f"ERROR: {a.image} is not a readable image: {e}")
        return 1

    repo = os.path.abspath(a.repo)
    scenes_dir = os.path.join(repo, "scenes")
    scene_dir = os.path.join(scenes_dir, sid)
    # A folder holding only a dropped-in image (no case.json yet) is not a finished scene.
    has_case = os.path.isfile(os.path.join(scene_dir, "case.json"))
    if has_case and not a.force:
        print(f"ERROR: scenes/{sid}/ already exists. Pick another --id, or pass --force to replace "
              "its image and case.json.")
        return 1

    os.makedirs(os.path.join(scene_dir, "evidence"), exist_ok=True)
    src = a.image
    tmpdir = None
    if os.path.abspath(src).startswith(scene_dir + os.sep):
        # The image was dropped straight into scenes/<id>/; stage a copy so copy_image can replace it.
        import tempfile
        tmpdir = tempfile.mkdtemp(prefix="waldo-scene-")
        src = os.path.join(tmpdir, os.path.basename(a.image))
        shutil.copyfile(a.image, src)
    try:
        name, w, h = copy_image(src, scene_dir)
    except OSError as e:
        print(f"ERROR: cannot copy image: {e}")
        return 1
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
    with open(os.path.join(scene_dir, "case.json"), "w", encoding="utf-8") as f:
        json.dump(skeleton(name, w, h), f, indent=2, ensure_ascii=False)
        f.write("\n")

    manifest_path = os.path.join(scenes_dir, "index.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: scenes/index.json is not valid JSON: {e}")
            return 1
        created = False
    else:
        manifest, created = json.loads(json.dumps(DEFAULT_MANIFEST)), True
    manifest.setdefault("scenes", [])
    if not any(isinstance(s, dict) and s.get("id") == sid for s in manifest["scenes"]):
        manifest["scenes"].append({"id": sid})
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    rel = os.path.relpath(scene_dir, os.getcwd())
    skill = os.path.relpath(os.path.dirname(os.path.abspath(__file__)), os.getcwd())
    print(f"Scene '{sid}' scaffolded: {rel}/{name} ({w}x{h}px), {rel}/case.json (skeleton), {rel}/evidence/")
    print(f"{'Created' if created else 'Updated'} scenes/index.json "
          f"({len(manifest['scenes'])} scene(s) listed; gallery order = list order).")
    print("Next steps:")
    print(f"  1. python3 {skill}/survey.py {rel}            # view overview.png and every tile")
    print(f"  2. python3 {skill}/zoom.py {rel} X Y W H      # confirm each hook; record {rel}/hooks.md")
    print(f"  3. Replace every TODO in {rel}/case.json (one voice, regions from hooks.md only)")
    print(f"  4. python3 {skill}/make_crops.py {rel} --facts --sheet .waldo-work/{sid}/crops-sheet.png")
    print(f"  5. python3 {skill}/validate_case.py {rel} && python3 {skill}/validate_site.py")
    print(f"  6. python3 -m http.server 8000  ->  http://localhost:8000/scene.html?id={sid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
