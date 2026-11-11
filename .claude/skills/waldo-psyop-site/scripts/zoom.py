#!/usr/bin/env python3
"""Zoom into one region of a scene image to confirm and refine a hook.

Usage:
  zoom.py IMAGE x y w h [--scale 8] [--pad 20] [--out FILE]

IMAGE is the scene image, a scene folder (scenes/<id>), or its case.json.
x y w h is the candidate region in SOURCE pixels. The output shows the region
plus --pad source pixels of context on every side, upscaled by --scale, with
rulers labelled in source-pixel coordinates and the requested region outlined
in cyan. If the outline does not hug the object, read better numbers off the
rulers and run it again. Default output: .waldo-work/<id>/zoom-x-y-w-h.png.
Exits non-zero if the image cannot be read or the region is out of bounds.
"""
import argparse
import os
import sys

from _common import WORK_DIR, find_scene_image, ruled


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", help="scene image, scene folder, or case.json")
    for k in "xywh":
        ap.add_argument(k, type=int)
    ap.add_argument("--scale", type=float, default=8, help="zoom factor (default 8)")
    ap.add_argument("--pad", type=int, default=20, help="context in source pixels (default 20)")
    ap.add_argument("--out", help="output PNG path")
    a = ap.parse_args()

    from PIL import Image
    try:
        path, label = find_scene_image(a.image)
        src = Image.open(path)
        src.load()
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}")
        return 1
    W, H = src.size
    if a.w <= 0 or a.h <= 0 or a.x < 0 or a.y < 0 or a.x + a.w > W or a.y + a.h > H:
        print(f"ERROR: region {a.x},{a.y},{a.w},{a.h} is out of bounds for {W}x{H}")
        return 1
    if a.scale <= 0 or a.pad < 0:
        print("ERROR: --scale must be > 0 and --pad >= 0")
        return 1

    box = (max(0, a.x - a.pad), max(0, a.y - a.pad), min(W, a.x + a.w + a.pad), min(H, a.y + a.h + a.pad))
    img = ruled(src, box, a.scale, outline=(a.x, a.y, a.w, a.h),
                title=f"region x={a.x} y={a.y} w={a.w} h={a.h}  @ {a.scale:g}x  (cyan = region)")
    out = a.out or os.path.join(WORK_DIR, label, f"zoom-{a.x}-{a.y}-{a.w}-{a.h}.png")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
