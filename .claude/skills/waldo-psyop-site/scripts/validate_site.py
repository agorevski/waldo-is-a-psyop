#!/usr/bin/env python3
"""Validate the whole multi-scene site: manifest, every scene, and the page shells.

Usage: validate_site.py [--repo .] [--no-shells]

1. scenes/index.json: valid JSON; site.title, site.subtitle, site.intro (list),
   site.footer (the parody disclaimer); scenes is a non-empty list of {"id": ...}
   with valid, unique ids, each with a scenes/<id>/case.json. Scene folders
   that are not listed are reported as warnings. No "TODO" placeholders.
2. Every listed scene: validate_case.py (all its checks, including TODOs).
3. The grand theory (manifest "theory"): required once two or more scenes
   are listed. It must cover exactly the listed scenes, have 3-6 motifs that
   each span at least 2 scenes, 5-9 chain steps that together cite every scene,
   2-6 verdict lines, and a refinement log with layers 1, 2, 3 in order. Every
   evidence reference and every claims[].crossLinks target must resolve.
4. If scene.html / index.html exist (each is skipped when absent): check_render_contract.py in scene and
   gallery mode (skip with --no-shells).

Exits 1 on any error. CI (.github/workflows/pages.yml) runs this script.
"""
import argparse
import json
import os
import sys

import check_render_contract as crc
import validate_case
from _common import ID_RE


def find_todos(node, where, errors):
    if isinstance(node, str):
        if "TODO" in node:
            errors.append(f"{where}: unfinished placeholder {node[:60]!r}")
    elif isinstance(node, dict):
        for k, v in node.items():
            find_todos(v, f"{where}.{k}", errors)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            find_todos(v, f"{where}[{i}]", errors)


def check_manifest(repo):
    errors, warnings, ids = [], [], []
    scenes_dir = os.path.join(repo, "scenes")
    path = os.path.join(scenes_dir, "index.json")
    try:
        with open(path, encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [f"scenes/index.json: cannot read: {e}"], warnings, ids
    if not isinstance(m, dict):
        return ["scenes/index.json: expected an object"], warnings, ids

    site = m.get("site")
    if not isinstance(site, dict):
        errors.append("scenes/index.json: missing 'site' object")
    else:
        for k in ("title", "subtitle", "footer"):
            if not isinstance(site.get(k), str) or not site[k].strip():
                errors.append(f"scenes/index.json: site.{k} must be non-empty text")
        if not isinstance(site.get("intro"), list) or not site["intro"]:
            errors.append("scenes/index.json: site.intro must be a non-empty list of paragraphs")
        if "parody" not in str(site.get("footer", "")).lower():
            errors.append("scenes/index.json: site.footer must be the parody disclaimer")

    scenes = m.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes/index.json: 'scenes' must be a non-empty list")
        scenes = []
    for i, s in enumerate(scenes):
        w = f"scenes/index.json: scenes[{i}]"
        if not isinstance(s, dict) or not isinstance(s.get("id"), str):
            errors.append(f"{w}: must be an object with a string 'id'")
            continue
        sid = s["id"]
        if not ID_RE.match(sid):
            errors.append(f"{w}: id {sid!r} must match ^[a-z0-9][a-z0-9-]{{0,39}}$")
            continue
        if sid in ids:
            errors.append(f"{w}: duplicate id {sid!r}")
            continue
        ids.append(sid)
        if not os.path.isfile(os.path.join(scenes_dir, sid, "case.json")):
            errors.append(f"{w}: scenes/{sid}/case.json not found")
    find_todos(m, "scenes/index.json", errors)

    for name in sorted(os.listdir(scenes_dir)):
        if os.path.isdir(os.path.join(scenes_dir, name)) and name not in ids and not name.startswith("."):
            warnings.append(f"scenes/{name}/ is not listed in scenes/index.json (it will not be in the gallery)")
    return errors, warnings, ids


def _txt(v):
    return isinstance(v, str) and v.strip() != ""


def check_theory(repo, ids):
    """Check the manifest's grand theory and every scene's crossLinks targets."""
    errors, warnings = [], []
    claims = {}
    for sid in ids:
        try:
            with open(os.path.join(repo, "scenes", sid, "case.json"), encoding="utf-8") as f:
                claims[sid] = {c.get("id") for c in json.load(f).get("claims", []) if isinstance(c, dict)}
        except (OSError, json.JSONDecodeError, AttributeError):
            claims[sid] = set()

    for sid in ids:
        try:
            with open(os.path.join(repo, "scenes", sid, "case.json"), encoding="utf-8") as f:
                case = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for c in case.get("claims", []):
            for k, x in enumerate(c.get("crossLinks", []) if isinstance(c, dict) else []):
                if not isinstance(x, dict):
                    continue
                w = f"scenes/{sid} {c.get('id')}.crossLinks[{k}]"
                if x.get("scene") not in claims:
                    errors.append(f"{w}: scene {x.get('scene')!r} is not listed in the manifest")
                elif x.get("claim") not in claims[x["scene"]]:
                    errors.append(f"{w}: claim {x.get('claim')!r} not found in scenes/{x['scene']}")

    try:
        with open(os.path.join(repo, "scenes", "index.json"), encoding="utf-8") as f:
            t = json.load(f).get("theory")
    except (OSError, json.JSONDecodeError, AttributeError):
        return errors, warnings
    if t is None:
        if len(ids) >= 2:
            errors.append(f"theory: missing; {len(ids)} scenes are listed, so run the three-layer "
                          "grand-theory refinement (references/grand-theory.md)")
        return errors, warnings
    if not isinstance(t, dict):
        return errors + ["theory: must be an object"], warnings

    for k in ("title", "thesis"):
        if not _txt(t.get(k)):
            errors.append(f"theory.{k}: must be non-empty text")

    covered = t.get("scenes")
    if not isinstance(covered, list) or set(covered) != set(ids) or len(covered) != len(set(covered)):
        missing = sorted(set(ids) - set(covered or []))
        extra = sorted(set(covered or []) - set(ids))
        errors.append(f"theory.scenes: must list exactly the manifest scenes (missing {missing}, unknown {extra}); "
                      "re-run all three refinement layers after adding a scene")

    def check_evidence(ev, w):
        cited = set()
        if not isinstance(ev, list) or not ev:
            errors.append(f"{w}.evidence: must be a non-empty list")
            return cited
        for k, e in enumerate(ev):
            if not isinstance(e, dict):
                errors.append(f"{w}.evidence[{k}]: must be an object")
            elif e.get("scene") not in claims:
                errors.append(f"{w}.evidence[{k}]: scene {e.get('scene')!r} is not listed in the manifest")
            elif e.get("claim") not in claims[e["scene"]]:
                errors.append(f"{w}.evidence[{k}]: claim {e.get('claim')!r} not found in scenes/{e['scene']}")
            else:
                cited.add(e["scene"])
        return cited

    motifs = t.get("motifs")
    motif_ids = set()
    if not isinstance(motifs, list) or not 3 <= len(motifs) <= 6:
        errors.append("theory.motifs: must be a list of 3-6 motifs")
        motifs = motifs if isinstance(motifs, list) else []
    for i, m in enumerate(motifs):
        w = f"theory.motifs[{i}]"
        if not isinstance(m, dict):
            errors.append(f"{w}: must be an object")
            continue
        for k in ("id", "name", "text"):
            if not _txt(m.get(k)):
                errors.append(f"{w}.{k}: must be non-empty text")
        if m.get("id") in motif_ids:
            errors.append(f"{w}: duplicate id {m.get('id')!r}")
        motif_ids.add(m.get("id"))
        if len(check_evidence(m.get("evidence"), w)) < 2 and len(ids) >= 2:
            errors.append(f"{w}: a motif must be evidenced in at least 2 different scenes")

    chain = t.get("chain")
    if not isinstance(chain, list) or not 5 <= len(chain) <= 9:
        errors.append("theory.chain: must be a list of 5-9 steps")
        chain = chain if isinstance(chain, list) else []
    cited = set()
    for i, st in enumerate(chain):
        w = f"theory.chain[{i}]"
        if not isinstance(st, dict):
            errors.append(f"{w}: must be an object")
            continue
        if not _txt(st.get("text")):
            errors.append(f"{w}.text: must be non-empty text")
        cited |= check_evidence(st.get("evidence"), w)
        for mid in st.get("motifs", []) or []:
            if mid not in motif_ids:
                errors.append(f"{w}.motifs: unknown motif {mid!r}")
    uncited = sorted(set(ids) - cited)
    if chain and uncited:
        errors.append(f"theory.chain: never cites scene(s) {uncited}; the grand theory must use every case file")

    v = t.get("verdict")
    if not isinstance(v, list) or not 2 <= len(v) <= 6 or not all(_txt(x) for x in v):
        errors.append("theory.verdict: must be 2-6 non-empty lines")

    log = t.get("refinement")
    if (not isinstance(log, list) or [e.get("layer") if isinstance(e, dict) else None for e in log] != [1, 2, 3]):
        errors.append("theory.refinement: must log exactly layers 1, 2, 3 in order")
    else:
        for e in log:
            if not _txt(e.get("name")) or not _txt(e.get("summary")):
                errors.append(f"theory.refinement layer {e.get('layer')}: name and summary must be non-empty")

    crossed = sum(1 for sid in ids
                  if any(isinstance(c, dict) and c.get("crossLinks") for c in _load_claims(repo, sid)))
    if len(ids) >= 2 and crossed < len(ids):
        warnings.append(f"crossLinks: only {crossed} of {len(ids)} scenes link to another case file "
                        "(layer 2 should add 1-4 per scene)")
    return errors, warnings


def _load_claims(repo, sid):
    try:
        with open(os.path.join(repo, "scenes", sid, "case.json"), encoding="utf-8") as f:
            return json.load(f).get("claims", [])
    except (OSError, json.JSONDecodeError, AttributeError):
        return []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repository root (default .)")
    ap.add_argument("--no-shells", action="store_true", help="skip the scene.html / index.html checks")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    total_err = 0

    print("== scenes/index.json")
    errs, warns, ids = check_manifest(repo)
    crc.report(errs, warns, f"manifest: {len(ids)} scene(s)")
    total_err += len(errs)

    for sid in ids:
        case = os.path.join(repo, "scenes", sid, "case.json")
        if not os.path.isfile(case):
            continue
        print(f"== scenes/{sid}")
        errs, warns, summary = validate_case.validate(case)
        crc.report(errs, warns, summary)
        total_err += len(errs)

    print("== grand theory")
    errs, warns = check_theory(repo, ids)
    crc.report(errs, warns, f"theory across {len(ids)} scene(s)")
    total_err += len(errs)

    if not a.no_shells:
        for name, fn in (("scene.html", crc.check_scene), ("index.html", crc.check_gallery)):
            path = os.path.join(repo, name)
            print(f"== {name}")
            if not os.path.isfile(path):
                print(f"SKIP:  {name} not found (bootstrap the engine first); render checks skipped")
                continue
            errs, warns = fn(path)
            crc.report(errs, warns, name)
            total_err += len(errs)

    print(f"\n{'FAIL' if total_err else 'OK'}: {total_err} error(s) in total")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
