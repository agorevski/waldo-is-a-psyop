# Data Contract: `scenes/<id>/case.json` and `scenes/index.json`

The orchestrator owns these files and writes all copy. The engine (`scene.html`, `assets/js/scene.js`) and the gallery (`index.html`, `assets/js/gallery.js`) only read them. `case.json` is the single source of truth for a scene.

## Layout

```
scenes/index.json            # manifest + gallery copy
scenes/<id>/case.json        # one scene's data (this contract)
scenes/<id>/scene.<ext>      # the scene image (.jpg, .png, or .webp)
scenes/<id>/evidence/*.png   # evidence crops
scenes/<id>/hooks.md         # the verified hook table and Dropped list (working notes)
```

The scene id is the folder name and matches `^[a-z0-9][a-z0-9-]{0,39}$`.

**Every path inside `case.json` is relative to the scene folder**: `image.src` is `"scene.jpg"`, and `claims[].asset` and `lineup[].asset` are `"evidence/x.png"`. The renderer resolves them as `scenes/<id>/<path>`. Never use a leading `/`, `..`, or a URL (the site is served from a GitHub Pages subpath).

## `case.json`

```jsonc
{
  "image": {
    "src": "scene.jpg", "width": 1500, "height": 937,   // real pixel size of src
    "alt": "..."                                          // REQUIRED: alt text for the hero image
  },
  "site": {
    "title": "...", "subtitle": "...", "caseNumber": "...",
    "banner": "...",            // mirror-site warning bar
    "marquee": "...",           // scrolling ticker
    "heroCaption": "...",
    "intro": ["paragraph", "..."],   // inline markup allowed
    "hitCounterBase": 1956,
    "lastUpdated": "...",
    "censusInstructions": "..."      // REQUIRED: e.g. "Click every striped thing on the beach above."
  },
  "claims": [{
    "id": "P01", "num": 1,
    "title": "...",
    "region": { "x":0,"y":0,"w":0,"h":0 },   // primary region: hero pin + board thumbnail
    "facts": [{ "text": "...", "region": { "x":0,"y":0,"w":0,"h":0 } }],   // exactly 2
    "leap": "...",               // inline markup allowed
    "update": { "time": "4:12 AM", "text": "..." },
    "note": "...",               // sticky-note scrawl
    "stamp": "CLASSIFIED",       // rubber-stamp overlay text
    "asset": "evidence/x.png", "alt": "...",
    "caption": "...",            // handwritten polaroid caption
    "paranoia": 1,               // 1–5
    "links": [{ "to": "P02", "label": "SAME POSTCARD" }],
    "crossLinks": [{ "scene": "ski", "claim": "P04", "label": "SAME FACE, DIFFERENT HAT" }]   // OPTIONAL; written by the grand-theory refinement
  }],
  "lineupReference": {           // OPTIONAL
    "claim": "P01", "name": "THE STAMP (reference)",
    "has": ["..."], "missing": []
  },
  "lineup": [{ "id": "L1", "name": "...", "region": {...}, "asset": "evidence/suspect-1.png", "alt": "...",
               "has": ["..."], "missing": ["..."] }],
  "stripes": [{ "id": "S01", "label": "...", "region": {...} }],
  "censusComments": ["..."],
  "guestbook": [{ "name": "...", "date": "...", "text": "...", "reply": "...", "claim": "P06" }],
  "updates": [{ "time": "...", "text": "...", "claim": "P01" }],
  "receipts": [{ "item": "...", "price": "...", "note": "...", "claim": "P02" }],
  "verdict": { "lines": ["..."], "button": "Request Further Investigation" },
  "cipher": { "cipher": "...", "plain": "...", "claim": "P04" },
  "footer": "This is a parody. Waldo is a fictional character created by Martin Handford. No actual investigation occurred."
}
```

- `image.width` and `image.height` must be the real pixel size of `image.src`. All regions are integer `{x, y, w, h}` in those source pixels.
- `lineupReference`: when present, the lineup starts with a reference card that uses that claim's `region`, `asset`, and `alt`, with this `name`, `has`, and `missing`. When absent, there is no reference card. Use the clearest complete Waldo image in the scene (a stamp, poster, or portrait).
- `cipher.cipher` is the ROT13 of `cipher.plain` (by convention; the engine just swaps the two strings).
- No string may contain `TODO`. `new_scene.py` writes a skeleton full of `TODO` placeholders, and `validate_case.py` rejects every one.

## `scenes/index.json` (manifest)

```json
{
  "site": {
    "title": "WALDO IS A PSYOP",
    "subtitle": "...",
    "intro": ["paragraph with inline markup"],
    "footer": "This is a parody. ..."
  },
  "scenes": [ { "id": "beach" }, { "id": "<next-id>" } ]
}
```

- `site.title`, `site.subtitle`, and `site.footer` are non-empty text; `site.intro` is a non-empty list of paragraphs (inline markup allowed); the footer is the parody disclaimer.
- `scenes` is a non-empty list of `{ "id": ... }` objects. Ids are valid and unique, and each has `scenes/<id>/case.json`. The order of the list is the gallery order. Append new scenes at the end.
- Everything else about a scene (title, subtitle, caseNumber, image, claim count, lastUpdated) is read from its `case.json`. Don't duplicate it in the manifest.
- The gallery copy is in character, like the scenes. Only the footer breaks character.

## `theory` (grand conspiracy, in `scenes/index.json`)

The theory is OPTIONAL with one scene. It is REQUIRED as soon as the manifest lists two or more scenes, and it must cover every listed scene. It is produced only by the three-layer refinement in [grand-theory.md](grand-theory.md) and lives in the manifest (so the gallery can render it without fetching anything extra):

```jsonc
"theory": {
  "title": "THE GRAND THEORY",            // in character
  "thesis": "...",                          // one paragraph, inline markup allowed
  "scenes": ["beach", "ski"],               // the scenes the theory was refined against; must equal the manifest ids (as a set)
  "motifs": [{                              // 3–6 motifs
    "id": "M1",
    "name": "THE ISSUED FACE",
    "text": "...",                          // in character, inline markup allowed
    "evidence": [ { "scene": "beach", "claim": "P01" }, { "scene": "ski", "claim": "P03" } ]   // at least 2 DIFFERENT scenes
  }],
  "chain": [{                               // 5–9 ordered steps: the grand escalation arc
    "text": "...",                          // in character, inline markup allowed
    "evidence": [ { "scene": "beach", "claim": "P01" } ],   // at least 1
    "motifs": ["M1"]                        // optional; must exist in motifs
  }],
  "verdict": ["...", "..."],                // grand verdict lines (2–6)
  "refinement": [                           // audit log; NOT rendered; exactly layers 1, 2, 3 in order
    { "layer": 1, "name": "Evidence inventory", "summary": "..." },
    { "layer": 2, "name": "Synthesis", "summary": "..." },
    { "layer": 3, "name": "Skeptic review", "summary": "..." }
  ]
}
```

- Every `evidence[]` entry points at an existing claim in an existing scene listed in the manifest. The facts behind that claim ARE the evidence: the theory never introduces a fact that is not already a verified fact in some `case.json`.
- Across all `chain` steps, every scene in `theory.scenes` is cited at least once. Every motif spans at least two scenes.
- `claims[].crossLinks` (in `case.json`) points from a claim to a claim in ANOTHER scene: `scene` is a listed scene id (not the claim's own scene), `claim` exists in that scene, and `label` is a short in-character string. Use 1–4 per scene, and only where a motif links the two claims.
- `refinement[].summary` is neutral working notes (what was inventoried, decided, cut, fixed). It is the only out-of-character text in the manifest besides `site.footer`, and it is never rendered.

## Inline markup

Escape HTML first, then convert:

- `==text==` becomes `<mark>text</mark>` (yellow highlighter)
- `~~text~~` becomes `<s>text</s>` (crossed out)
- `[[shown|reveal]]` becomes `<button class="redact" data-reveal="reveal" aria-label="Redacted. Activate to reveal.">shown</button>`. Clicking it toggles `.is-revealed` and swaps in the reveal text. Revealed state persists in `localStorage` (per scene).

The schema marks inline markup as allowed in `site.intro` (both files) and `claims[].leap`. A renderer may also apply it to other copy fields, but it must always escape first.

## Validation

- Every region is integer and in bounds.
- Every claim has exactly 2 facts.
- Every `links[].to`, `claim`, `cipher.claim`, and `lineupReference.claim` exists.
- Every asset file exists, and every path is relative to the scene folder.
- `image.alt` and `site.censusInstructions` are present and non-empty.
- No `TODO` placeholders remain.
- `crossLinks` (if any) have a valid `scene` id that is not the scene's own id, plus a `claim` and a `label`; `validate_site.py` checks that the target scene and claim exist.
- With two or more scenes, `scenes/index.json` has a `theory` that covers every listed scene and passes the rules above (`validate_site.py`).

`scripts/validate_case.py scenes/<id>` checks these rules and the required keys above. It also flags duplicate IDs, `paranoia` values outside 1–5, a declared image size that doesn't match the file, and crops whose aspect ratio does not match their region (a warning; expected for intentional composites). `scripts/validate_site.py` checks the manifest, runs `validate_case` on every listed scene, warns about scene folders that are not listed, and runs the render-contract checks when the shells exist.
