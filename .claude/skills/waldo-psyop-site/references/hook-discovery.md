# Hook Discovery: Finding and Verifying Hooks in Any Scene

A **hook** is something literally visible in the scene image, with a source-pixel region, that the author can build a claim on. Every fact, lineup suspect, and census stripe in `case.json` must come from a verified hook. This procedure works for any *Where's Waldo?* scene. [examples/beach-hooks.md](examples/beach-hooks.md) shows the result for the beach scene.

Run all commands from the repo root. Survey and zoom output goes to `.waldo-work/<id>/`, which is scratch space: never commit it.

## 1. Know the canvas

`new_scene.py` prints the image size and writes it to `image.width` and `image.height`. All regions are integer `{x, y, w, h}` in those source pixels, with the origin at the top-left. The hero overlay's `viewBox` is `0 0 {width} {height}`, so these numbers are used as-is everywhere.

## 2. Survey pass (find candidates)

```sh
python3 .claude/skills/waldo-psyop-site/scripts/survey.py scenes/<id>            # 300 px tiles at 3x, 60 px overlap
python3 .claude/skills/waldo-psyop-site/scripts/survey.py scenes/<id> --tile 200 --scale 4   # denser scenes
```

1. View `overview.png` first (grid every 100 px). Note the scene's layout: where the text is, where the crowds are, and any large objects.
2. View **every** tile, in order. Tiles overlap, so an object cut by one tile's edge appears whole in its neighbour. Rulers on all four sides and the faint magenta grid are labelled in SOURCE pixels: read a candidate's left, top, right, and bottom edges directly off the rulers.
3. Write each candidate down with a rough region and a one-line description. Be greedy here; you cut later.

### What to look for (strongest first)

| Kind | Examples | Why it's useful |
|---|---|---|
| **Printed text** | postcards, signs, banners, labels, checklists, posters, shop names, numbers, flags with letters | Unambiguous and quotable. Text is the best "official document" evidence. Quote it exactly, including punctuation and line breaks. |
| **Official-looking marks** | stamps, postmarks, seals, badges, tickets, maps, portraits, statues | Feeds "Waldo is *issued*". |
| **Waldo look-alikes** | full matches (red-and-white bobble hat, round glasses, red-and-white striped shirt, blue trousers) and partial matches (any 1–3 pieces) | Feeds "there are many of him" and the lineup. Note which pieces each one has and lacks. |
| **Red-and-white stripes on things** | towels, awnings, umbrellas, tents, booths, flags, poles, clothes | The stripe census (10–20 hotspots) and "the pattern is everywhere". |
| **Uniforms and matching groups** | crews, guards, bands, teams, staff, anyone dressed identically | Feeds "it's a uniform, handed out". |
| **Duplicates and doubles** | the same outfit twice, twins, reflections, posters of a figure who is also in the crowd | "Which one?" |
| **Exits and vehicles** | boats, hovercraft, balloons, trains, ladders, doors, tunnels | "How they get him out". |
| **Covered or hidden areas** | something lying over the scene, a crowd blocking a view, a closed door, a tent | "The one place you can't look". |
| **Absences** | something the text promises that is nowhere in the picture | Strong closers, but only after you have searched every tile. |
| **Scene gags** | anything visibly odd, reversed, upside down, or out of place | Tempting leaps, as long as the fact stays literal. |

## 3. Zoom pass (confirm and measure)

```sh
python3 .claude/skills/waldo-psyop-site/scripts/zoom.py scenes/<id> X Y W H                 # 8x, 20 px context
python3 .claude/skills/waldo-psyop-site/scripts/zoom.py scenes/<id> X Y W H --scale 4 --pad 40   # big objects
```

- Confirm every candidate at **4–10× zoom** (8× for objects under about 60 px, 4× for objects over about 150 px). View the PNG every time.
- The cyan outline is the region exactly as `case.json` will store it. Adjust x, y, w, h until it hugs the object with a 2–5 px margin, then zoom again. Read the new numbers off the rulers; don't guess.
- A claim or suspect region frames the whole object. A fact region frames only the detail the fact describes (for example, just the question mark at the end of a postmark), so the spotlight lands on it. Keep every region at least about 20 × 20 px so the spotlight stays readable.
- Quote text only after reading it at zoom. If a letter is illegible, the text is not a fact.

## 4. Name things correctly

Write down what each object **is**, not what the author wants it to be: "hovercraft" (roof propellers, inflated skirt), not "ferry"; "puppet booth" (puppets in the window), not "red hut". The facts stay correct and the *leap* does the misreading. If you can't tell what something is at 10×, describe only its appearance ("a tall red-and-white striped booth") or drop it. Describe people only by what they visibly wear or do. Never identify anyone as a real person.

## 5. Record the hook table and the Dropped list

Write `scenes/<id>/hooks.md`:

```markdown
# Hooks: <id> (<width> × <height> px)

| Hook | Region (x, y, w, h) | What is actually visible |
|---|---|---|
| ... | ... | ... |

**Lineup suspects:** <hook names, each with ✔ has / ✘ missing pieces>
**Census stripes:** <10–20 regions with labels>
**Dropped as unverifiable or misleading:** <item (reason)>; <item (reason)>; ...
```

**Dropped-list discipline (binding):** anything you couldn't confirm, anything ambiguous, and every tempting misreading goes on the Dropped list with its reason. Dropped items never become facts. The author may mention a dropped item only as something he *couldn't* find (the beach example: an underlined "KNIGHT IN ARMOR" on the postcard, and no knight anywhere on the beach). Re-check the Dropped list before writing every claim.

## 6. Minimum counts

| Need | Count | Notes |
|---|---|---|
| Claims | 10–12 | Exactly 2 facts each. Facts may share hooks, but each claim needs its own primary region. |
| Distinct hooks | about 14 or more | Fewer usually means claims repeat themselves. |
| Lineup suspects | about 5 (3–6) | Look-alikes with different missing pieces. Optional `lineupReference`: the clearest complete Waldo image (a stamp, poster, or portrait) as the comparison card. |
| Census stripes | 10–20 | Red-and-white striped objects and clothes, spread across the scene. |

If you come up short, survey again with `--tile 200 --scale 4`. Never pad with unverified details. Ten strong claims beat twelve weak ones.

## 7. If the scene has no printed text

The "issued" beat must come from something else that is visibly official or mass-produced: identical uniforms, numbered shirts, flags, badges, signposts with symbols, a portrait or statue, identical objects in a row. The opening claim then uses the clearest Waldo look-alike, or the most striking uniform group, instead of a document. Do not invent text, and do not borrow a document from another scene: a fact must be visible in *this* image. If there is no complete Waldo image, omit `lineupReference` and compare suspects against the pieces they share.

## 8. From hooks to a claim chain

The site is one chain of reasoning, not a pile of trivia. Sort your hooks into the thesis's three beats, then order the claims as an escalation arc.

**The thesis beats** ("Waldo doesn't exist; he's a uniform handed out in pieces"):

1. **Issued**: evidence that "Waldo" is official, printed, or distributed (text, stamps, signs, uniforms).
2. **Plural, in pieces**: more than one of him, and nobody has the whole outfit (look-alikes, the lineup, stripes everywhere).
3. **Managed**: someone runs it, searches for him, or controls the exits (uniformed groups, vehicles, puppets, organisers, hidden areas, absences).

**The arc:**

- **Opening claim (P01, paranoia 1–2):** the most checkable, most striking hook, usually printed text or the clearest Waldo image. The reader confirms it in 5 seconds and the leap is gentle.
- **Middle claims (P02 to about P09, paranoia rising):** each one cites an earlier claim, in the leap, the update, the note, or a `links[]` string ("SAME POSTCARD", "THE CHECKLIST SKIPPED IT"). Move from beat 1 to beat 2 to beat 3. Put the lineup claim (often with a composite asset of every suspect) in the middle.
- **Closing claims (the last one or two, paranoia 4–5):** loop back to the opener, often through an absence or something hidden, and set up the pattern the verdict will name. At least one links back to P01 or another early claim.
- `links[]` form a connected graph: every claim links to at least one other, and no claim is an island.
- The other sections reuse the same hooks: lineup from look-alikes, census from stripes, receipts and updates and guestbook entries each tied to a claim, the cipher pointing at the most "hidden" claim, and verdict lines restating the thesis with this scene's specific evidence.

**Leap test:** for each claim, a normal reader should be able to say what the author is thinking in one sentence, even while disagreeing. If they can't, the leap is too far: split it or cut it.

**Earlier case files:** each new scene is a new case file by the same author. He may cite an earlier case file in passing, once or twice (in the intro, an update, or a webmaster reply), for example "Same question mark as the beach postmark." Every claim must stand alone: no fact, region, or asset may come from another image, and no claim may require the reader to have seen another scene. Structured connections between scenes (motifs, the grand chain, `crossLinks`) are not built here; they come later, in the three-layer refinement in [grand-theory.md](grand-theory.md).

### Worked example: the beach arc

From the hooks in [examples/beach-hooks.md](examples/beach-hooks.md):

| # | Claim | Beat | Builds on |
|---|---|---|---|
| P01 | He mailed us a picture of himself (signature + face stamp) | Issued | opener |
| P02 | The post office is asking the question (postmark ends in "?") | Issued | P01, same postcard |
| P03 | Addressed to nobody, delivered anyway (address has no street) | Issued | P02 |
| P04 | People are standing under the postcard (legs below its edge) | Managed | P03, hidden area |
| P05 | He gave us a checklist (stripe list + the real striped huts) | Plural | P04, same card |
| P06 | There are two of him (two hat-and-shirt look-alikes) | Plural | P01 face vs. crowd |
| P07 | The lineup: every one is missing a piece (composite of suspects vs. stamp) | Plural | P06, P01 |
| P08 | Someone is pulling the strings (striped puppet booth, left off the checklist) | Managed | P05, P06 |
| P09 | That is not a ferry (hovercraft: the only exit that needs no dock) | Managed | P08 |
| P10 | The men in blue are looking for someone (uniformed crew) | Managed | P09, P06 |
| P11 | The knight he underlined (underlined text vs. empty sand castles) | Closer: absence | P01, P04 |
| P12 | The signal tower (human pyramid with a view of the exit) | Closer: managed | P09 |

The verdict then names the pattern: a stamp, a postmark, and a uniform, whole on the postcard and handed out in pieces on the beach.
