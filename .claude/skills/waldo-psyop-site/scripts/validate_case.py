#!/usr/bin/env python3
"""Validate one scene's case.json against the waldo-psyop data contract.

Usage: validate_case.py SCENE_DIR_OR_CASE_JSON [--root SCENE_DIR]

Accepts a scene folder (scenes/<id>) or its case.json. Every path in case.json
(image.src, claims[].asset, lineup[].asset) is resolved relative to the scene
folder (override with --root). Checks required keys, regions, exactly 2 facts
per claim, claim references, assets, image size, image.alt,
site.censusInstructions, the optional lineupReference, the shape of optional
claims[].crossLinks (targets are checked by validate_site.py), and flags every leftover
"TODO" placeholder as an error so a skeleton can never ship. Exits 1 if any
error is found.
"""
import argparse
import json
import os
import sys

from _common import ID_RE, resolve_case

SITE_KEYS = ["title", "subtitle", "caseNumber", "banner", "marquee", "heroCaption",
             "intro", "hitCounterBase", "lastUpdated", "censusInstructions"]
CLAIM_KEYS = ["id", "num", "title", "region", "facts", "leap", "update", "note", "stamp",
              "asset", "alt", "caption", "paranoia", "links"]
LINEUP_KEYS = ["id", "name", "region", "asset", "alt", "has", "missing"]
TOP_KEYS = ["image", "site", "claims", "lineup", "stripes", "censusComments", "guestbook",
            "updates", "receipts", "verdict", "cipher", "footer"]

errors, warnings = [], []
TODO = "TODO"


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def need(obj, keys, where):
    if not isinstance(obj, dict):
        err(f"{where}: expected an object")
        return False
    missing = [k for k in keys if k not in obj]
    if missing:
        err(f"{where}: missing keys {missing}")
    return not missing


def check_region(r, where, W, H):
    if not isinstance(r, dict) or set(r) < {"x", "y", "w", "h"}:
        err(f"{where}: region must have x, y, w, h")
        return False
    ok = True
    for k in "xywh":
        v = r[k]
        if not isinstance(v, int) or isinstance(v, bool):
            err(f"{where}: region.{k}={v!r} is not an integer")
            ok = False
    if not ok:
        return False
    x, y, w, h = r["x"], r["y"], r["w"], r["h"]
    if w <= 0 or h <= 0:
        err(f"{where}: region has non-positive size {w}x{h}")
        ok = False
    if x < 0 or y < 0 or x + w > W or y + h > H:
        err(f"{where}: region {x},{y},{w},{h} is out of bounds for {W}x{H}")
        ok = False
    return ok


def check_asset(path, where, root, region=None):
    if not isinstance(path, str) or not path:
        err(f"{where}: asset path missing")
        return
    if path.startswith("/") or "\\" in path or ".." in path.split("/") or "://" in path:
        err(f"{where}: path {path!r} must be relative to the scene folder (e.g. 'evidence/x.png')")
        return
    full = os.path.join(root, path)
    if not os.path.isfile(full):
        err(f"{where}: asset not found: {path}")
        return
    if region is None:
        return
    try:
        from PIL import Image
    except ImportError:
        return
    with Image.open(full) as im:
        cw, ch = im.size
    ra, ca = region["w"] / region["h"], cw / ch
    if abs(ra - ca) / ra > 0.08:
        warn(f"{where}: crop {path} aspect {ca:.2f} differs from region aspect {ra:.2f}; "
             "fine if it is an intentional composite, otherwise re-run make_crops.py --force")


def find_todos(node, where="case.json"):
    if isinstance(node, str):
        if TODO in node:
            err(f"{where}: unfinished placeholder {node[:60]!r}")
    elif isinstance(node, dict):
        for k, v in node.items():
            find_todos(v, f"{where}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            find_todos(v, f"{where}[{i}]")


def nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def validate(case_arg, root=None):
    """Validate one case.json. Return (errors, warnings, summary)."""
    errors.clear()
    warnings.clear()
    case_path, scene_dir = resolve_case(case_arg)
    root = root or scene_dir
    try:
        with open(case_path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        err(f"cannot read {case_path}: {e}")
        return list(errors), list(warnings), "unreadable"
    summary = _validate(d, root)
    return list(errors), list(warnings), summary


def _validate(d, root):
    if not ID_RE.match(os.path.basename(os.path.abspath(root))):
        warn(f"scene folder name {os.path.basename(os.path.abspath(root))!r} is not a valid scene id "
             "(^[a-z0-9][a-z0-9-]{0,39}$)")
    need(d, TOP_KEYS, "case.json")

    img = d.get("image", {})
    W, H = img.get("width"), img.get("height")
    if not isinstance(W, int) or not isinstance(H, int):
        err("image: width/height must be integers")
        W = H = 10 ** 9
    if not nonempty_str(img.get("alt")):
        err("image.alt: required, non-empty alt text for the hero image")
    if "src" in img:
        check_asset(img["src"], "image.src", root)
        try:
            from PIL import Image
            p = os.path.join(root, img["src"])
            if os.path.isfile(p):
                with Image.open(p) as im:
                    if im.size != (W, H):
                        err(f"image: declared {W}x{H} but {img['src']} is {im.size[0]}x{im.size[1]}")
        except ImportError:
            warn("Pillow not installed; skipped image-size and crop-aspect checks")

    site = d.get("site", {})
    need(site, SITE_KEYS, "site")
    if not isinstance(site.get("intro", []), list):
        err("site.intro must be a list of paragraphs")
    if "censusInstructions" in site and not nonempty_str(site["censusInstructions"]):
        err("site.censusInstructions: must be non-empty text")

    claims = d.get("claims", [])
    ids = [c.get("id") for c in claims if isinstance(c, dict)]
    claim_ids = set(ids)
    if len(ids) != len(claim_ids):
        err(f"claims: duplicate ids {sorted({i for i in ids if ids.count(i) > 1})}")
    if not 10 <= len(claims) <= 12:
        warn(f"claims: {len(claims)} claims (target is 10-12)")

    for i, c in enumerate(claims):
        w = f"claims[{i}] ({c.get('id', '?') if isinstance(c, dict) else '?'})"
        need(c, CLAIM_KEYS, w)
        if not isinstance(c, dict):
            continue
        if c.get("num") != i + 1:
            warn(f"{w}: num={c.get('num')!r}, expected {i + 1} (claims render in order)")
        rok = check_region(c.get("region"), f"{w}.region", W, H)
        facts = c.get("facts", [])
        if not isinstance(facts, list) or len(facts) != 2:
            err(f"{w}: must have exactly 2 facts (has {len(facts) if isinstance(facts, list) else 'none'})")
        else:
            for j, fact in enumerate(facts):
                if need(fact, ["text", "region"], f"{w}.facts[{j}]"):
                    check_region(fact["region"], f"{w}.facts[{j}].region", W, H)
        p = c.get("paranoia")
        if not isinstance(p, int) or not 1 <= p <= 5:
            err(f"{w}: paranoia={p!r} must be an integer 1-5")
        need(c.get("update", {}), ["time", "text"], f"{w}.update")
        for k, link in enumerate(c.get("links", [])):
            if need(link, ["to", "label"], f"{w}.links[{k}]") and link["to"] not in claim_ids:
                err(f"{w}.links[{k}]: unknown claim '{link['to']}'")
        cross = c.get("crossLinks", [])
        if not isinstance(cross, list):
            err(f"{w}.crossLinks: must be a list")
            cross = []
        for k, x in enumerate(cross):
            xw = f"{w}.crossLinks[{k}]"
            if need(x, ["scene", "claim", "label"], xw):
                if not isinstance(x["scene"], str) or not ID_RE.match(x["scene"]):
                    err(f"{xw}: scene {x['scene']!r} is not a valid scene id")
                elif x["scene"] == os.path.basename(root):
                    err(f"{xw}: points at its own scene; use links[] for same-scene links")
                if not nonempty_str(x["claim"]) or not nonempty_str(x["label"]):
                    err(f"{xw}: claim and label must be non-empty text")
        check_asset(c.get("asset"), w, root, c["region"] if rok else None)

    if "lineupReference" in d:
        ref = d["lineupReference"]
        if need(ref, ["claim", "name", "has", "missing"], "lineupReference"):
            if ref["claim"] not in claim_ids:
                err(f"lineupReference.claim: unknown claim '{ref['claim']}'")
            for k in ("has", "missing"):
                if not isinstance(ref[k], list):
                    err(f"lineupReference.{k}: must be a list")

    lineup_ids = []
    for i, s in enumerate(d.get("lineup", [])):
        w = f"lineup[{i}] ({s.get('id', '?') if isinstance(s, dict) else '?'})"
        need(s, LINEUP_KEYS, w)
        if not isinstance(s, dict):
            continue
        lineup_ids.append(s.get("id"))
        rok = check_region(s.get("region"), f"{w}.region", W, H)
        check_asset(s.get("asset"), w, root, s["region"] if rok else None)
    if len(lineup_ids) != len(set(lineup_ids)):
        err("lineup: duplicate ids")

    stripe_ids = []
    for i, s in enumerate(d.get("stripes", [])):
        w = f"stripes[{i}] ({s.get('id', '?') if isinstance(s, dict) else '?'})"
        if need(s, ["id", "label", "region"], w):
            stripe_ids.append(s["id"])
            check_region(s["region"], f"{w}.region", W, H)
    if len(stripe_ids) != len(set(stripe_ids)):
        err("stripes: duplicate ids")

    if not d.get("censusComments"):
        err("censusComments: must be a non-empty list")

    for section, keys in (("guestbook", ["name", "date", "text", "reply", "claim"]),
                          ("updates", ["time", "text", "claim"]),
                          ("receipts", ["item", "price", "note", "claim"])):
        for i, e in enumerate(d.get(section, [])):
            w = f"{section}[{i}]"
            if need(e, keys, w) and e["claim"] not in claim_ids:
                err(f"{w}: unknown claim '{e['claim']}'")

    v = d.get("verdict", {})
    if need(v, ["lines", "button"], "verdict") and not v["lines"]:
        err("verdict.lines must be non-empty")

    cph = d.get("cipher", {})
    if need(cph, ["cipher", "plain", "claim"], "cipher") and cph["claim"] not in claim_ids:
        err(f"cipher.claim: unknown claim '{cph['claim']}'")

    footer = d.get("footer", "")
    if "parody" not in footer.lower():
        err("footer: must be the parody disclaimer")

    find_todos(d)
    return f"{len(claims)} claims, {len(lineup_ids)} suspects, {len(stripe_ids)} stripes"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case", help="scene folder (scenes/<id>) or its case.json")
    ap.add_argument("--root", help="folder that case.json paths are relative to (default: the scene folder)")
    a = ap.parse_args()
    errs, warns, summary = validate(a.case, a.root)
    for m in warns:
        print(f"WARN:  {m}")
    for m in errs:
        print(f"ERROR: {m}")
    print(f"{summary}: {len(errs)} error(s), {len(warns)} warning(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
