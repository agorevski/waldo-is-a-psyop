# Waldo is a PsyOp

> *"Stop looking for him. He's not on the beach. He's a stamp, a postmark, and a uniform, and somebody is counting on you to keep looking."*
> — Night 31, 8:30 AM

For thirty-one nights, one amateur theorist stared at a single *Where's Waldo?* beach scene and concluded that the man in the stripes was never a man at all. Then he opened the rest of the folder. Seven case files later (a beach, a sealed scroll, a department store, a dragon in a crowd, a packing list, and the same Trojan war twice), he has a **grand theory**: Waldo is a product, issued by THE DEPARTMENT, and the mailing list is you.

This repository is the case files: a static website with no build step that presents the evidence as the investigator found it. Every "clue" is a deliberately absurd reading of something actually visible in the scene images under `scenes/<id>/`. The investigator is wrong. The pictures are right. Go check.

## What you'll find

- **Seven case files** in a gallery, tied together by **The Grand Theory**: motifs and an eight-step chain where every link is a chip that jumps to the proof it cites.
- **Ten to twelve proofs per case file**, pinned to a corkboard and connected with red string. Each has two facts you can verify in five seconds and one leap you're not supposed to make.
- **SEE FOR YOURSELF** buttons that zoom the real scene to the exact spot under discussion.
- **The Lineup:** the people in red-and-white stripes, each missing exactly the piece that would make them Waldo.
- **Stripe Census:** click every striped thing in the scene. The count is saved in your browser, so you can prove you counted.
- **Redacted documents** that reveal the jokes when clicked.
- **A guestbook** where readers push back and the investigator replies, increasingly unwell.
- **A paranoia meter** that rises as you look at more evidence. Reset it if you're getting too calm.

## Run it locally

The live site is at <https://agorevski.github.io/waldo-is-a-psyop/>. Locally, the pages load `scenes/index.json` and each scene's `case.json` over HTTP, so serve the folder rather than opening the files directly. From the repository root:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000> for the gallery of case files, or go straight to <http://localhost:8000/scene.html?id=beach>. Do not trust the stamp.

## File layout

- `index.html`: the gallery. One case-file card per scene listed in `scenes/index.json`.
- `scene.html`: the shared scene page. It renders `scenes/<id>/case.json` for `scene.html?id=<id>` (no `id` means the first scene).
- `assets/css/styles.css`: the early-2000s homepage and corkboard look for both pages, responsive rules, and reduced-motion handling.
- `assets/js/scene.js`: renders all copy and interactive pieces of a scene from its `case.json`. It knows nothing about any particular scene.
- `assets/js/gallery.js`: renders the gallery from `scenes/index.json` and each scene's `case.json`.
- `scenes/index.json`: the list of scenes (in gallery order) plus the gallery's title, intro, and footer.
- `scenes/<id>/case.json`: every line of in-character copy for one scene, the claims, the regions they point at, and the footer disclaimer. Paths inside it are relative to the scene folder.
- `scenes/<id>/scene.jpg`: the scene image (the beach is 1500 × 937 px).
- `scenes/<id>/evidence/`: cropped evidence images, one per proof and suspect.
- `.claude/skills/waldo-psyop-site/`: the build brief packaged as a Claude skill (`SKILL.md`, contracts in `references/`, and validation, crop, and render-contract scripts in `scripts/`). To use it in other projects, copy the folder to `~/.claude/skills/`.
- `PROMPT.md`: the brief the site was built from, including the rule that every claim must stay anchored to something visible.

All URLs are relative, so the site works both at the root of a local server and under the `/waldo-is-a-psyop/` subpath on GitHub Pages. There is no build step.

## Add a new scene

One beach was never going to be enough. To open a new case file, follow the Claude skill in `.claude/skills/waldo-psyop-site/`: give it a scene image and an id (lowercase letters, digits, and hyphens, such as `ski-slope`). It writes `scenes/<id>/`, adds the id to `scenes/index.json`, and validates the result. The gallery and `scene.html?id=<id>` pick it up automatically.

Once there are two or more scenes, the skill runs a three-layer refinement to tie every case file into one **grand theory**:

1. **Evidence inventory:** verified things that recur across scenes.
2. **Synthesis:** motifs, a thesis, and an escalating chain.
3. **Skeptic review:** a fresh reviewer tries to break it.

The theory lives in `scenes/index.json` and appears on the gallery. Cross-scene links appear on each proof. CI refuses to deploy a theory that doesn't cover every scene.

## Want to add a clue?

Every claim must follow the plausibility ladder in `PROMPT.md`: two facts you can check, each tied to a region of the image, plus one leap that uses only things actually in the picture. If you can't point at it, it isn't evidence. It's a feeling, and the investigator already has enough of those.

## Disclaimer

This is a parody. Waldo is a fictional character created by Martin Handford. No actual investigation occurred, no postal service was involved, and no hovercraft was harmed. No real person in the picture is identified or targeted. The investigator's conclusions are fiction; the beach is real, so please go look at it.
