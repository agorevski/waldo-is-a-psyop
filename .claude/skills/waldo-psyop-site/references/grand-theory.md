# Grand-Theory Refinement (three layers)

Each scene is a self-contained case file. Once the manifest lists **two or more scenes**, the author also owes the reader a **grand conspiracy theory**: one cohesive story that ties every case file together. This file is the procedure for building it. It always runs as three layers in order, and it is the only way `theory` in `scenes/index.json` and `claims[].crossLinks` in each `case.json` may be written.

## When to run it

- After a new scene passes Step 5 (validate) and the manifest now lists two or more scenes.
- After any scene's claims, facts, or regions change, if a theory already exists.
- When the user asks to "refine", "connect", or "tie together" the case files.

Always re-run **all three layers** over **every listed scene**. Never patch the theory just for the newest scene. The previous `theory` (if any) is an *input* to Layer 1, not something to append to. `validate_site.py` fails when `theory.scenes` does not match the manifest, so a stale theory cannot ship.

## Ground rules (they apply to every layer)

1. **No new facts.** The theory may cite only facts that already exist, verified, in some scene's `case.json`. If the theory needs a fact that isn't there, go back to that scene's Step 2 (`zoom.py`), verify it, add it to that scene's `hooks.md`, and work it into a claim. The theory then cites that claim. A scene's Dropped list stays binding.
2. **The plausibility ladder scales up.** A scene claim is fact + fact → one leap. A **motif** is a verified fact in scene A + a verified fact in scene B → one cross-scene leap. A **chain step** is (the previous step + its cited claims) → one leap. Test: a normal reader can say what the author is thinking at every step, even while disagreeing.
3. **The thesis never changes; it widens.** "Waldo isn't a man; he's a uniform, handed out in pieces" stays the core. The grand theory explains *who hands it out, how, and why it keeps happening in every scene*, using only words, colours, positions, and objects that are actually in the images.
4. **Every scene still stands alone.** Scene copy may *mention* other case files, but a scene's own claims must make sense to a reader who never opens another scene.
5. **Fewer, stronger.** Each motif and chain step must earn its place. Cut weak links rather than padding.
6. **Voice and safety** are exactly as in [voice.md](voice.md): sincere, no hedging, no real people, no clinical or diagnostic language, obsessive not cruel. The refinement log is the only out-of-character text besides the footer, and it is never rendered.

Scratch work goes in `.waldo-work/theory/` (never commit it). The final output is the `theory` object in `scenes/index.json` (schema: [data-contract.md](data-contract.md)) plus `crossLinks` and light copy edits in the scenes.

---

## Layer 1: Evidence inventory (facts only, no leaps)

**Goal:** a complete, verified table of the things that recur across case files. Write no conspiracy copy in this layer.

**Inputs:** every listed scene's `case.json` and `hooks.md`, plus the previous `theory` if there is one.

**Procedure:**

1. For each scene, list every claim with its two facts, in neutral words (`beach P01: stamp with face, red-and-white bobble hat, round glasses`). If subagents are available, fan out **one subagent per scene** in parallel. Each one returns its scene's list plus candidate recurring items (Waldo look-alikes and partial outfits; red-and-white stripes on non-clothing objects; printed text, especially anything addressing or naming Waldo; uniforms and matching groups; counts; signage; stamps, postcards, documents; repeated positions or compositions).
2. Merge the lists into **recurrence groups**: the same *kind* of verifiable thing appearing in two or more scenes. Name each one for what is literally visible ("Waldo's full face appears only on printed matter"), not for the conclusion.
3. For every group member, record `scene`, `claim`, the fact index, and the fact text. Each member must point at an existing claim. If a strong recurring item exists in a scene but no claim covers it, mark it **NEEDS CLAIM**. Then either verify it and add it to that scene (back to Steps 2–5 for that scene) or drop it.
4. Re-open the evidence for every group member: `make_crops.py scenes/<id> --no-write --facts --only P03,P07 --sheet .waldo-work/theory/<id>-sheet.png`. View the sheet, and confirm each cited fact really shows what the group claims it shows. Remove any member that fails.
5. Keep groups that span **at least 2 scenes**. Rank them by how *checkable* and how *surprising* the recurrence is.

**Output:** `.waldo-work/theory/layer1-inventory.md`, a table of `group | scene | claim | fact | verified?` plus a short "rejected" list with the reasons.

**Gate (all must hold before Layer 2):**
- At least 3 recurrence groups, each spanning two or more scenes.
- Every listed scene appears in at least one group.
- Every member is an existing claim whose fact you re-viewed in this layer.

Write the `refinement[0]` summary (layer 1, "Evidence inventory"): the counts of groups and members, what was rejected and why, and any NEEDS CLAIM items resolved.

---

## Layer 2: Synthesis (the grand leap)

**Goal:** turn the inventory into one thesis, a set of motifs, and an escalating chain, then thread it back into the scenes.

**Procedure:**

1. **Motifs (3–6).** Promote the strongest recurrence groups to motifs. For each one, write `name` (a short, ALL-CAPS-friendly label in character, e.g. "THE ISSUED FACE"), `text` (2–4 sentences in character: state the two-scene facts, then the one-step leap), and `evidence` (two or more claims from at least two different scenes).
2. **Thesis (one paragraph).** It must explain every motif. Test: delete any one motif and the thesis should feel *less* supported, not irrelevant.
3. **Chain (5–9 steps).** Order the reasoning as an escalation arc:
   - Steps 1–2 are **the pattern**: the most checkable motif, stated with evidence from two or more scenes.
   - The middle steps are **the system**: each step uses the previous step plus new evidence to widen the claim (who issues the pieces, how they move between scenes, who keeps watch).
   - The last 1–2 steps are **the payoff**: the step that sets up the verdict. It should land on something visible, never on a new invention.
   Every step cites at least one claim. Across the chain, every scene is cited at least once. Tag each step's `motifs`.
4. **Verdict (2–6 lines).** The grand verdict, in the same typewriter cadence as the scene verdicts.
5. **Thread it into the scenes** (copy only; never change facts, regions, assets, or claim ids):
   - Add 1–4 `crossLinks` per scene, only between claims that share a motif. Labels are short and in character ("SAME FACE, DIFFERENT HAT").
   - Add one `updates` entry per scene that points at another case file. Optionally, change one guestbook reply or one verdict line to do the same. Keep each scene standalone.
   - Refresh `site.lastUpdated` in every scene you touched. If the gallery intro (`scenes/index.json` `site.intro`) no longer sets up the theory, update it.
6. **Consistency pass.** Check every scene for contradictions:
   - Case numbers are unique and increase in manifest order.
   - The "Night N" and hours-awake references agree.
   - Timestamps and dates don't collide.
   - Receipt prices and running jokes agree.
   - No scene verdict contradicts the thesis. If one does, edit the scene's copy, not the theory's evidence.

**Output:** the full `theory` object (without `refinement[2]` yet) written into `scenes/index.json`, plus the scene edits. Then run `validate_site.py`. Fix it until the only failures are the ones Layer 3 will address.

**Gate:**
- `validate_site.py` passes the theory and `crossLinks` checks.
- You can read the chain aloud from step 1 to the verdict without skipping a step.

Write the `refinement[1]` summary (layer 2, "Synthesis"): the chosen thesis in one neutral sentence, the motifs kept and merged, the scenes edited, and the number of `crossLinks` added.

---

## Layer 3: Skeptic review (adversarial tightening)

**Goal:** break the theory before a reader does. Then fix it, or cut what doesn't hold.

**Procedure:**

1. **Fresh eyes.** If subagents are available, run the review in a NEW subagent (a reviewer type if available, such as `rubber-duck`). Give it no authoring context, only:
   - the manifest `theory`
   - every scene's `case.json` and `hooks.md`
   - the Layer 1 inventory
   - [voice.md](voice.md) and this rubric
   Ask it for findings as `severity (BLOCKER/MAJOR/MINOR) | location | problem | suggested fix`. If no subagent is available, do the review yourself, *in order, item by item*, as a hostile but fair normal reader.
2. **Rubric.** Each item is a separate check:
   - **Truth:** every evidence reference resolves, and the cited claim's facts actually show what the motif or step says. Re-view the sheets for any doubtful item. Any untrue or Dropped-list fact is a BLOCKER.
   - **One step:** each motif leap and each chain step follows from its inputs in one step. A random non-sequitur is a MAJOR finding.
   - **Escalation:** the chain widens monotonically, there are no orphan steps, and every motif is used by at least one step.
   - **Coverage:** every scene contributes something essential. A scene cited only decoratively is a MAJOR finding.
   - **Consistency:** no contradictions across scenes or between a scene and the theory (case numbers, timeline, jokes, verdicts).
   - **Standalone:** each scene still reads correctly without the others.
   - **Voice and safety:** the voice is consistent, nothing hedges, there are no real people and no clinical or diagnostic language, and the humour targets the reasoning, never the reader.
   - **Economy:** anything that could be cut without weakening the thesis is a MINOR finding. Cut it.
3. **Fix.** Fix every BLOCKER and MAJOR finding. If one can't be fixed with existing verified facts, **cut** the motif, step, or `crossLink`; don't stretch it. Fix MINOR findings when cheap. Re-run the review once on the changed parts. At most two review rounds; whatever still fails after round two is cut.
4. **Re-validate and preview.**
   ```sh
   python3 $S/validate_site.py          # must exit 0
   python3 -m http.server 8000          # gallery: the theory section; scene pages: theory link + cross-chips
   ```
   In the browser, follow every evidence chip and every cross-chip. Each must land on the right claim with no console errors, at 360 px and 1440 px.

Write the `refinement[2]` summary (layer 3, "Skeptic review"): the findings by severity, what was fixed, what was cut, and the number of review rounds.

**Gate (the theory is done):**
- Zero open BLOCKER and MAJOR findings.
- `validate_site.py` exits 0.
- Every chip resolves in the browser.

---

## Worked shape (format illustration)

The beach scene's real claims are shown on the left. `<scene-2>` is a placeholder for whatever a second scene verifiably contains. Never copy this placeholder text as fact.

| Layer | Example output |
|---|---|
| 1 | Group "Waldo's full face appears only on printed matter": beach P01 fact 1 (the stamp face) + `<scene-2>` P0x fact y (a printed poster face, verified with `zoom.py`). |
| 2 | Motif `M1` "THE ISSUED FACE": "On the beach, his only clear face is on a STAMP. In `<scene-2>`, it's on a POSTER. Never a person. Always ==printed==." Chain step 1 cites both. |
| 3 | A reviewer flags that the `<scene-2>` poster face has no glasses at zoom (BLOCKER). Fix: cite the fact that is actually visible (the hat and stripes), or cut `<scene-2>` from M1 and find another member. |
