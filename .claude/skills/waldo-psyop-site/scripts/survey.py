#!/usr/bin/env python3
"""Survey a scene image: a gridded overview plus zoomed, ruled, overlapping tiles.

Usage:
  survey.py SCENE_DIR_OR_IMAGE [--tile 300] [--overlap 60] [--scale 3] [--out DIR]

SCENE_DIR_OR_IMAGE is a scene folder (scenes/<id>), its case.json, or an image.
Writes, to --out (default: .waldo-work/<id>/survey under the current directory):

  overview.png   the whole image with a labelled pixel grid every 100 px
  tile-rRR-cCC-x<X>-y<Y>.png
                 overlapping tiles of --tile source pixels, upscaled by --scale,
                 with rulers on all four sides and faint grid lines. Every
                 label is in SOURCE-pixel coordinates, so you can read a hook's
                 x, y, w, h straight off the tile.

Then refine each candidate region with zoom.py. Prints every written file.
Exits non-zero if the image cannot be read. Never commit .waldo-work/.
"""
import argparse
import os
import sys

from _common import WORK_DIR, find_scene_image, ruled


def starts(total, tile, step):
    if total <= tile:
        return [0]
    out = list(range(0, total - tile, step))
    out.append(total - tile)
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene", help="scene folder, case.json, or image file")
    ap.add_argument("--tile", type=int, default=300, help="tile size in source pixels (default 300)")
    ap.add_argument("--overlap", type=int, default=60, help="tile overlap in source pixels (default 60)")
    ap.add_argument("--scale", type=float, default=3, help="tile zoom factor (default 3)")
    ap.add_argument("--out", help="output folder (default .waldo-work/<id>/survey)")
    a = ap.parse_args()
    if a.tile <= 0 or not 0 <= a.overlap < a.tile or a.scale <= 0:
        ap.error("need --tile > 0, 0 <= --overlap < --tile, and --scale > 0")

    from PIL import Image
    try:
        path, label = find_scene_image(a.scene)
        src = Image.open(path)
        src.load()
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}")
        return 1
    W, H = src.size
    out = a.out or os.path.join(WORK_DIR, label, "survey")
    os.makedirs(out, exist_ok=True)
    written = []

    ov_scale = min(1.0, 2000 / max(W, H))
    ov = ruled(src, (0, 0, W, H), ov_scale, force_major=100,
               title=f"{os.path.basename(path)}  {W}x{H}px  overview, grid every 100 px")
    p = os.path.join(out, "overview.png")
    ov.save(p)
    written.append(p)

    step = a.tile - a.overlap
    for r, y in enumerate(starts(H, a.tile, step)):
        for c, x in enumerate(starts(W, a.tile, step)):
            box = (x, y, min(W, x + a.tile), min(H, y + a.tile))
            t = ruled(src, box, a.scale,
                      title=f"tile r{r:02d} c{c:02d}  source x {box[0]}-{box[2]}, y {box[1]}-{box[3]}  @ {a.scale:g}x")
            p = os.path.join(out, f"tile-r{r:02d}-c{c:02d}-x{x}-y{y}.png")
            t.save(p)
            written.append(p)

    print(f"{path}: {W}x{H}px")
    for p in written:
        print(p)
    print(f"{len(written)} file(s) written to {out}. View overview.png first, then every tile.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
