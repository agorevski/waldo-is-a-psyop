# PROMPT: "Waldo Doesn't Exist" — A Conspiracy Website, Authored by the Theorist

## Mission

Build a static website that looks like it was made, by hand and at 3 a.m., by an obsessive conspiracy theorist who has stared at one *Where's Waldo?* beach scene (`waldo_beach.jpg`) for 31 nights and concluded that **Waldo doesn't exist**: he is a uniform, a stamp, and a postmark, handed out in pieces to people on the beach.

**Two audiences, one page:**
- **The author** (in character, everywhere except the footer) is sincere, sleep-deprived, and certain. He never hedges, never winks, never explains the joke.
- **The reader** is a normal person. They should be able to confirm every factual statement in seconds, nod along, and then catch themselves thinking "…huh." The humour comes from the gap between true observations and the wrong conclusion.

This is parody. The footer disclaimer is the only place the site breaks character.

## The Plausibility Ladder (core rule)

Every claim is built the same way:

1. **Fact 1**: something literally visible, with a source-pixel region. Checkable in about 5 seconds.
2. **Fact 2**: a second visible thing, also with a region, that sits next to Fact 1.
3. **The leap**: one wrong-but-tempting conclusion that uses only words, colours, positions, or objects that are actually in the image.

Rules:
- Facts must be true. If a detail can't be confirmed at zoom, it can't be a fact. The author may mention it only as something he *couldn't* find.
- Each leap is **one step** from the facts, not a random non-sequitur. Test: a normal reader can say what the author is thinking, even while disagreeing.
- Claims escalate and **cite earlier claims**. The site is one chain of reasoning, not a pile of trivia.
- Fewer, stronger claims beat many weak ones (target 10–12).
- Every fact has a **SEE FOR YOURSELF** button that spotlights its region on the real image.

## Persona and Voice

- First person, present tense, addressing the reader directly ("Look at the booth. Just look at it.").
- ALL-CAPS bursts for emphasis, but not whole paragraphs.
- Timestamped self-interruptions: `UPDATE 4:12 AM: …`.
- Crossed-out self-corrections (`~~I'm not crazy.~~`), highlighter marks (`==…==`), and redactions (`[[REDACTED|reveal]]`).
- Rhetorical questions, "I'm just asking questions," "think about it," and "convenient."
- He is obsessive, not cruel. The humour targets his reasoning, never mental illness as such and never the reader. Do not use clinical or diagnostic language.
- Never names or targets a real person. Figures are described only by what they visibly wear or do.
- In-character text must not hedge ("this is just a joke", "not an observation"). Hedging lives only in the footer.

## Source Material: verified hooks

Image: `waldo_beach.jpg`, exactly **1500 × 937 px**. All regions are `{x, y, w, h}` in these pixels. Each item below was confirmed at 4–10× zoom.

| Hook | Region (x, y, w, h) | What is actually visible |
|---|---|---|
| Postcard | 50, 50, 352, 240 | Postcard lying over the top-left corner of the beach |
| Signature | 75, 235, 60, 35 | Signed "Waldo" |
| Stamp | 316, 42, 74, 86 | Face, red-and-white bobble hat, round glasses |
| Postmark | 250, 55, 72, 75 | "WHERE'S" / "ON THE BEACH" / "WALDO?" (it ends in a question mark) |
| Address | 250, 155, 145, 60 | "TO: WALDO-FOLLOWERS HERE, THERE, EVERYWHERE" (no street or town) |
| Stripe list | 70, 120, 170, 60 | "STRIPES ON TOWELS, CLOTHES, UMBRELLAS, AND BEACH HUTS" |
| Knight line | 70, 195, 150, 30 | "KNIGHT IN ARMOR" is underlined |
| Under the card | 100, 262, 300, 48 | Legs and shorts poke out below the postcard's bottom edge; upper bodies hidden |
| Suspect A | 905, 298, 48, 74 | Striped bobble hat, striped shirt, blue trousers; face half-blocked by another head |
| Suspect B | 1022, 632, 40, 60 | Second figure in striped bobble hat and striped shirt |
| Striped swimsuit | 612, 780, 58, 80 | Red-and-white striped one-piece, no hat |
| Striped trousers | 850, 705, 50, 85 | Red-and-white striped trousers, yellow top, no hat |
| Striped shorts | 1105, 480, 45, 45 | Red-and-white striped shorts, seen from behind |
| Puppet booth | 1030, 282, 52, 76 | Red-and-white striped Punch-and-Judy booth with puppets in its window |
| Hovercraft | 1335, 90, 165, 150 | Roof-mounted propellers, inflated skirt, half on sand. It is NOT a ferry |
| Uniformed crew | 1345, 215, 155, 85 | Men in matching blue uniforms and caps on the sand; one has both hands on his head |
| Sand castles | 1420, 835, 70, 50 | Plain sand castles, empty. **No knight is visible anywhere** |
| Human pyramid | 990, 100, 100, 115 | Swimmers stacked in the surf |

Dropped as unverifiable or misleading: any visible knight; "ferry" (it's a hovercraft); "red hut" (it's a puppet booth); the red bucket-shaped mound near (1450, 485) (ambiguous).

## Build Plan (orchestrator + parallel builders)

| Role | Owns | Notes |
|---|---|---|
| **Orchestrator** (writes and verifies) | `data/case.json`, `assets/**` | Writes ALL copy in one voice. Generates and visually verifies every crop. Finalised before builders start. |
| Builder B | `index.html`, `styles.css`, `README.md` | Page shell and all styling for the render contract. Writes no narrative copy. |
| Builder C | `script.js` | Renders everything from `data/case.json` using the render contract. Writes no narrative copy. |

B and C run in parallel against the contracts below. If a builder needs a string that isn't in `case.json`, it must use a neutral UI label (e.g. "Close"), never new in-character copy.

## Data Contract: `data/case.json`

```jsonc
{
  "image": { "src": "assets/waldo_beach.jpg", "width": 1500, "height": 937 },
  "site": {
    "title": "...", "subtitle": "...", "caseNumber": "...",
    "banner": "...",            // mirror-site warning bar
    "marquee": "...",           // scrolling ticker
    "heroCaption": "...",
    "intro": ["paragraph", "..."],   // inline markup allowed
    "hitCounterBase": 1956,
    "lastUpdated": "..."
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
    "asset": "assets/evidence/x.png", "alt": "...",
    "caption": "...",            // handwritten polaroid caption
    "paranoia": 1,               // 1–5
    "links": [{ "to": "P02", "label": "SAME POSTCARD" }]
  }],
  "lineup": [{ "id": "L1", "name": "...", "region": {...}, "asset": "...", "alt": "...",
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

Inline markup (escape HTML first, then convert):
- `==text==` becomes `<mark>text</mark>` (yellow highlighter)
- `~~text~~` becomes `<s>text</s>` (crossed out)
- `[[shown|reveal]]` becomes `<button class="redact" data-reveal="reveal" aria-label="Redacted. Activate to reveal.">shown</button>`. Clicking it toggles `.is-revealed` and swaps in the reveal text. Revealed state persists in `localStorage`.

Validation: every region is integer and in bounds; every claim has exactly 2 facts; every `links[].to`, `claim` and `cipher.claim` exists; every asset file exists.

## Render Contract (`index.html` + `styles.css` ↔ `script.js`)

### Static IDs in `index.html` (each exactly once)

| ID | Element | Filled by script with |
|---|---|---|
| `site-banner` | `div` | `site.banner` |
| `site-marquee` | `div` | `site.marquee` inside `<span class="marquee-track">` (CSS animates it) |
| `case-number` | `span` | `site.caseNumber` |
| `case-clock` | `span` | Live "Hours awake: N.NN" (start time persisted) |
| `hit-counter` | `span` | Zero-padded digits, each `<span class="digit">` (`hitCounterBase` + local visits) |
| `last-updated` | `span` | `site.lastUpdated` |
| `site-title` | `h1` | `site.title` |
| `site-subtitle` | `p` | `site.subtitle` |
| `hero` | `figure` (position: relative) | Contains `hero-image`, `hero-overlay`, `hero-caption` |
| `hero-image` | `img` src `assets/waldo_beach.jpg` | — |
| `hero-overlay` | `svg` with `viewBox="0 0 1500 937"` `preserveAspectRatio="none"`, absolutely covering the image | Pins, link strings, census hotspots, red circle (all in source-pixel units; no resize math needed) |
| `hero-caption` | `figcaption` | `site.heroCaption` |
| `intro` | `div` | `site.intro` paragraphs |
| `board` | `div` (position: relative) | Corkboard of claim cards + `svg#board-strings` |
| `claims` | `div` | One `article.claim` per claim |
| `lineup` | `div` | One `.suspect` per lineup entry + the stamp for comparison |
| `census-count` | `span` | Number |
| `census-log` | `ol` | Newest first, max 8 |
| `updates` | `ol` | `li.update` |
| `receipts` | `tbody` | `tr.receipt` |
| `guestbook` | `div` | `.gb-entry` |
| `verdict-typewriter` | `div` | `verdict.lines` typed out |
| `paranoia-meter` | `div` | Sets CSS var `--level` (0–100) and `aria-valuenow` |
| `paranoia-reset` | `button` | — |
| `request-investigation` | `button` | — |
| `cipher-toggle` | `button` | — |
| `cipher-text` | `code` | Cipher or plain text |
| `site-footer` | `footer` | `footer` text in `<p class="disclaimer">` (the HTML may also hardcode it) |
| `spotlight` | `dialog` | "See for yourself" viewer |
| `spotlight-view` | `div` inside dialog | Full image as background, zoomed to region |
| `spotlight-caption` | `p` inside dialog | Fact text |
| `spotlight-close` | `button` inside dialog | — |

### Markup script generates (CSS must style these classes)

```html
<!-- hero overlay (SVG) -->
<g class="pin" data-claim="P01" tabindex="0" role="button" aria-label="Proof #1: title">
  <circle class="pin-head" cx cy r="9"/><text class="pin-num">1</text></g>
<path class="hero-string" data-from="P01" data-to="P02"/>  <text class="string-label">SAME POSTCARD</text>
<rect class="stripe-hit" data-stripe="S01" x y width height tabindex="0" role="button"/>
<ellipse class="red-circle"/>

<!-- board -->
<div class="board-card" data-claim="P01" tabindex="0" style="left:..;top:..;--tilt:-3deg">
  <span class="pushpin"></span><img class="board-thumb"><span class="board-title">PROOF #1</span></div>
<svg id="board-strings"><path class="board-string" data-from data-to/><text class="board-label"/></svg>

<!-- claim -->
<article class="claim" id="claim-P01" data-claim="P01" data-paranoia="2">
  <header class="claim-head"><span class="claim-num">PROOF #1</span><h3 class="claim-title">…</h3>
    <span class="rubber-stamp">CLASSIFIED</span></header>
  <div class="claim-body">
    <figure class="polaroid"><span class="tape"></span><img class="crop" loading="lazy"><figcaption class="scrawl">…</figcaption></figure>
    <ol class="facts"><li class="fact"><span class="fact-text">…</span>
      <button class="see-btn" data-claim="P01" data-fact="0">SEE FOR YOURSELF</button></li></ol>
    <p class="leap">…</p>
    <aside class="sticky">…</aside>
  </div>
  <p class="claim-update"><span class="update-time">UPDATE 4:12 AM:</span> …</p>
  <ul class="claim-links"><li><a class="link-chip" href="#claim-P02">→ PROOF #2: SAME POSTCARD</a></li></ul>
</article>

<!-- lineup -->
<div class="suspect" data-region="x,y,w,h"><img class="crop"><h4 class="suspect-name">…</h4>
  <ul class="suspect-has"><li>✔ …</li></ul><ul class="suspect-missing"><li>✘ …</li></ul>
  <button class="see-btn">SEE FOR YOURSELF</button></div>

<!-- guestbook / updates / receipts -->
<div class="gb-entry"><p class="gb-meta"><span class="gb-name"/> <span class="gb-date"/></p>
  <p class="gb-text"/><p class="gb-reply"><b>WEBMASTER:</b> …</p></div>
<li class="update"><span class="update-time"/> <span class="update-text"/> <a class="update-link"/></li>
<tr class="receipt"><td class="r-item"/><td class="r-price"/><td class="r-note"/><td><a class="link-chip"/></td></tr>
```

State classes: `.is-active`, `.is-lit`, `.is-pulsing`, `.is-revealed`, `.is-seen`, `.is-counted`, `body.is-flickering`, `body.is-dragging`.

## Site Sections (top to bottom)

1. **Chrome**: `site-banner` (black/yellow hazard bar), `site-marquee`, a header strip with `case-number`, `case-clock`, `hit-counter` ("You are visitor #"), `last-updated`.
2. **Hero**: `site-title`, `site-subtitle`, then `hero` with pins and **labelled red strings drawn across the beach between linked claims**. A red marker circle drifts over the crowd and never settles.
3. **Intro letter** ("READ THIS FIRST"): `intro`.
4. **The Board**: corkboard of claim cards with labelled strings between linked cards. Cards are draggable on desktop (positions persist). Below 720 px it becomes a stacked list with link chips and no SVG strings.
5. **The Proofs**: `claims`, one per claim, in order.
6. **The Lineup**: `lineup`, suspects beside the stamp with ✔ has / ✘ missing.
7. **Stripe Census**: instructions plus `census-count` and `census-log`. Hotspots live on the hero image.
8. **Investigation Log**: `updates`.
9. **Receipts**: table with `receipts`.
10. **Guestbook**: `guestbook` (normal readers push back; the webmaster replies in character).
11. **The Verdict**: `verdict-typewriter`, `paranoia-meter`, `paranoia-reset`, `request-investigation`.
12. **Footer**: `site-footer` disclaimer, `cipher-toggle` and `cipher-text`.

## Design: "personal homepage meets 3 a.m. corkboard"

It must look homemade, not designed.
- **Early-2000s personal site:** Times New Roman body on cream "paper", **Comic Neue** or **Caveat** for scrawl, **Special Elite** for typewriter and case text, and one heavy condensed face (e.g. **Anton**) for the title. Blue underlined links, visited links purple. A hazard-tape banner, a scrolling marquee (CSS), and a hit counter in odometer digits. Horizontal rules made of a repeated `★ ★ ★` or a red-and-white stripe gradient. Slightly uneven column widths. A "Best viewed at 800×600" badge.
- **Corkboard:** cork texture from CSS gradients, polaroids with tape, sticky notes (yellow, rotated), rubber stamps (red, rotated, semi-transparent, `mix-blend-mode: multiply`), and red marker circles and underlines.
- **Highlighter:** `mark` is a yellow highlighter swipe (gradient with ragged edges).
- **Palette:** sand yellow `#f5d84a`, sea blue `#2a7fbf`, stripe red `#d6202a`, white, cork brown, ink `#1b1b1b`. Body text WCAG AA on its background.
- **Responsive:** 360 px to 1440 px. No horizontal scroll at 360 px.
- **Accessibility:** alt text on every image; every interactive element keyboard reachable with visible focus; `Esc` closes the spotlight; respect `prefers-reduced-motion` (no marquee scroll, no flicker, no typewriter, no drifting circle; text appears instantly).

## Interaction Details

- **SEE FOR YOURSELF** opens `spotlight`. `spotlight-view` shows the real image zoomed so the region fills about 60% of the view, with a red marker ring around the region and the rest dimmed. Each use raises the paranoia meter and marks the claim `.is-seen` (persisted).
- **Hero pins**: clicking one scrolls to its claim and pulses its strings. Hovering a pin, card, or string highlights the linked pair everywhere (hero strings, board strings, board cards).
- **Stripe Census**: clicking a hotspot on the hero image marks it `.is-counted` (persisted), increments the count, and logs a random `censusComments` line. Re-clicking a counted stripe still increments the count but logs "Already counted. Counting it again." The count persists.
- **Paranoia meter**: `--level` = percentage of distinct facts seen (persisted). Reset clears seen, census, redactions, and card positions.
- **Verdict**: when it scrolls into view, light hero and board strings one by one (`.is-lit`), then type out `verdict.lines`.
- **Request Further Investigation**: flickers the body and scrolls to the top.
- **Cipher**: `cipher-toggle` swaps between `cipher.cipher` and `cipher.plain` (which links to the claim).
- **Keyboard**: `Esc` closes the dialog; arrow keys move focus between board cards; `Enter` or `Space` activate pins and hotspots.
- No console errors. No external JS libraries.

## Definition of Done

- `python3 -m http.server` from the repo root serves the site. It loads with no console errors or 404s at 360 px and 1440 px.
- Every fact's SEE FOR YOURSELF spotlight shows the thing the fact describes (orchestrator checks visually).
- Every crop matches its region. Every link, claim reference, and asset resolves.
- Census, paranoia, redactions, and board positions persist across reloads; reset clears them.
- The author voice is consistent; in-character copy never hedges; the footer disclaimer is present.
- No real people are named or targeted; every fact is visible in the image.

## Tone Calibration

- "Who puts their OWN face on a stamp? Nobody. Stamps are ==ISSUED==."
- "So you found Waldo. Congratulations. ==Which one?=="
- "The one striped thing on the beach he 'forgot' to list is the one with a hand up inside a little person, making it move."
- "UPDATE 4:31 AM: I tried to lift the postcard. It's a picture. You can't lift it. CONVENIENT."
