# Render Contract (shells + styles ↔ scripts)

Builder B (HTML/CSS) and Builder C (JS) build against this contract in parallel. Neither builder writes narrative copy. If a builder needs a string that isn't in `case.json` or `scenes/index.json`, it uses a neutral UI label (for example "Close" or "All case files").

## Files and URLs

```
index.html              # Builder B: gallery shell
scene.html              # Builder B: scene shell, renders scenes/<id>/case.json for ?id=<id>
assets/css/styles.css   # Builder B: all styling (scene page + gallery)
assets/js/scene.js      # Builder C: scene renderer (scene-agnostic)
assets/js/gallery.js    # Builder C: gallery renderer
.nojekyll               # Builder B: GitHub Pages serves files as-is
```

- The site is served from a subpath (`https://<owner>.github.io/<repo>/`). Every URL in HTML, CSS, JS, and JSON is **relative**: no leading `/`. There is no build step; the repo root is the site root.
- Both shells load fonts with a stylesheet `<link>`, `assets/css/styles.css`, their script with `defer`, and `<link rel="icon" href="data:,">` (no `/favicon.ico` 404).
- No external JS libraries.

## Scene page (`scene.html` + `assets/js/scene.js`)

- Reads `id` from the query string (`scene.html?id=beach`). If `id` is missing, use the first scene in `scenes/index.json`. If the id is unknown or invalid (`^[a-z0-9][a-z0-9-]{0,39}$`), or its `case.json` fails to load, show a neutral "Case file not found." message with a link back to `index.html`. No console errors.
- Fetches `scenes/<id>/case.json` and resolves every path in it as `scenes/<id>/<path>`.
- Sets `document.title` to `site.title`.
- Sets `hero-image` `src`, `alt`, `width`, and `height` from `image.*`, and the `hero-overlay` `viewBox` to `0 0 {image.width} {image.height}`. Nothing about the image is hardcoded; the HTML may ship a placeholder `viewBox`, and the script always overwrites it.
- Namespaces every `localStorage` key with `wde-<id>-`, so census, paranoia, seen facts, redactions, board positions, the case clock, and visits are separate for each scene. Reset clears only the current scene's keys.
- Must not reference any claim id, hook, scene id, or scene-specific wording. It must work for any valid `case.json`.

## Static IDs in `scene.html` (each exactly once)

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
| `hero-image` | `img` with NO hardcoded `src`, `width`, `height`, or `alt` | `src` = `scenes/<id>/` + `image.src`; `alt` = `image.alt`; `width`/`height` = `image.width`/`image.height` |
| `hero-overlay` | `svg` with `preserveAspectRatio="none"` (and at most a placeholder `viewBox`), absolutely covering the image | `viewBox="0 0 {image.width} {image.height}"`, then pins, link strings, census hotspots, red circle (all in source-pixel units; no resize math needed) |
| `hero-caption` | `figcaption` | `site.heroCaption` |
| `intro` | `div` | `site.intro` paragraphs |
| `board` | `div` (position: relative) | Corkboard of claim cards + `svg#board-strings` |
| `claims` | `div` | One `article.claim` per claim |
| `lineup` | `div` | The `lineupReference` card first (if present), then one `.suspect` per lineup entry |
| `census-instructions` | `p` | `site.censusInstructions` |
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
| `scene-nav` | `nav` | Holds a link to `index.html` ("All case files", a neutral UI label). The script may add previous/next scene links from the manifest. |
| `theory-link` | `p` (`hidden` by default) | Shown only when the manifest `theory.scenes` includes this scene: a link to `index.html#grand-theory` labelled with `theory.title` |

Because the `viewBox` always equals the image's own pixel size, every overlay coordinate is a raw source-pixel region from `case.json`, whatever the scene's dimensions.

## Markup the script generates (CSS must style these classes)

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
  <ul class="claim-links"><li><a class="link-chip" href="#claim-P02">→ PROOF #2: SAME POSTCARD</a></li>
    <!-- one per crossLinks entry; skipped if the target scene is not in the manifest -->
    <li><a class="link-chip cross-chip" href="scene.html?id=ski#claim-P04">⇢ OTHER CASE FILE (ski): SAME FACE, DIFFERENT HAT</a></li></ul>
</article>

<!-- lineup (the lineupReference card, if any, uses the same markup and comes first) -->
<div class="suspect" data-region="x,y,w,h"><img class="crop"><h4 class="suspect-name">…</h4>
  <ul class="suspect-has"><li>✔ …</li></ul><ul class="suspect-missing"><li>✘ …</li></ul>
  <button class="see-btn">SEE FOR YOURSELF</button></div>

<!-- guestbook / updates / receipts -->
<div class="gb-entry"><p class="gb-meta"><span class="gb-name"/> <span class="gb-date"/></p>
  <p class="gb-text"/><p class="gb-reply"><b>WEBMASTER:</b> …</p></div>
<li class="update"><span class="update-time"/> <span class="update-text"/> <a class="update-link"/></li>
<tr class="receipt"><td class="r-item"/><td class="r-price"/><td class="r-note"/><td><a class="link-chip"/></td></tr>
```

Deep links: after rendering, if `location.hash` is `#claim-<id>` and that claim exists, scroll it into view and pulse it (`.is-pulsing`), because the claims don't exist yet when the browser first processes the hash. The gallery does the same for `#grand-theory` and `#motif-<id>`.

## State classes

`.is-active`, `.is-lit`, `.is-pulsing`, `.is-revealed`, `.is-seen`, `.is-counted`, `body.is-flickering`, `body.is-dragging`.

## Gallery (`index.html` + `assets/js/gallery.js`)

- Same homemade early-2000s look as the scene page: hazard banner, cream paper, Anton / Special Elite / Caveat, star rules, a "Best viewed at 800×600" badge.
- Fetches `scenes/index.json`, then every scene's `case.json` in parallel. If one scene fails to load, skip it and keep rendering the rest.
- Renders the manifest's `site.title`, `site.subtitle`, `site.intro` (same inline markup: escape HTML, then `==mark==`, `~~s~~`, `[[shown|reveal]]`), and `site.footer`.
- One "case file" card per scene, in manifest order: the scene image as a thumbnail (`object-fit: cover`, `loading="lazy"`, `alt` = `image.alt`), plus that scene's `site.title`, `site.subtitle`, `site.caseNumber`, `site.lastUpdated`, and "N proofs" (the claim count). Each card links to `scene.html?id=<id>`.
- Responsive from 360 to 1440 px with no horizontal scroll, keyboard accessible, respects `prefers-reduced-motion`.

### Static IDs in `index.html` (each exactly once)

| ID | Element | Filled by script with |
|---|---|---|
| `gallery-title` | `h1` | manifest `site.title` |
| `gallery-subtitle` | `p` | manifest `site.subtitle` |
| `gallery-intro` | `div` | manifest `site.intro` paragraphs |
| `gallery-cards` | `ul` | One `li.case-card` per scene |
| `gallery-disclaimer` | `p` | manifest `site.footer` |

Optional: `gallery-count` (`span`, number of scenes), `gallery-status` (`p`, neutral loading or error status), `gallery-marquee` (`div`).

### Grand theory section (gallery)

Static IDs in `index.html` (each exactly once). The section ships `hidden` and is shown only when the manifest has a valid `theory`:

| ID | Element | Filled by script with |
|---|---|---|
| `grand-theory` | `section` (`hidden` by default) | Container; place it after the case cards and before the footer |
| `theory-title` | `h2` | `theory.title` |
| `theory-thesis` | `div` | `theory.thesis` (inline markup) |
| `theory-chain` | `ol` | One `li.theory-step` per `theory.chain` step, in order |
| `theory-motifs` | `div` | One `.motif` per `theory.motifs` entry |
| `theory-verdict` | `div` | `theory.verdict` lines, each a `p.theory-verdict-line` |

Generated markup (an evidence chip resolves its claim's `num` and the scene's `site.title` from the `case.json` files the gallery already fetched; if it can't resolve a reference, it skips that chip and never throws):

```html
<li class="theory-step" data-motifs="M1 M2"><p class="theory-text">…</p>
  <ul class="theory-evidence"><li><a class="link-chip evidence-chip" href="scene.html?id=beach#claim-P01">→ BEACH TITLE · PROOF #1</a></li></ul></li>
<div class="motif" id="motif-M1"><h3 class="motif-name">…</h3><p class="motif-text">…</p>
  <ul class="theory-evidence">…evidence chips…</ul></div>
```

Style it as the corkboard's big brother: chain steps as numbered index cards joined by a red string or rule, motifs as tilted sticky notes. Hovering or focusing a motif highlights (`.is-active`) the chain steps whose `data-motifs` include it.

Example card markup (the builder may add decoration; the check expects at least `case-card`, `case-card-link`, `case-card-thumb`, and `case-card-title` to be styled):

```html
<li class="case-card"><a class="case-card-link" href="scene.html?id=beach">
  <span class="case-card-thumb"><img src="scenes/beach/scene.jpg" alt="…" loading="lazy"></span>
  <h3 class="case-card-title">…</h3><p class="case-card-sub">…</p>
  <p class="case-card-meta">…caseNumber… · <span class="case-card-count">12 proofs</span> · <span class="case-card-updated">…</span></p>
</a></li>
```

## Checking the contract

`scripts/check_render_contract.py` (default `scene.html`) checks that:

- every static ID appears exactly once, on the right element (including `census-instructions` and `scene-nav`)
- `hero-overlay` has `preserveAspectRatio="none"` and at most a placeholder `viewBox`
- `hero-image` has no hardcoded `src`, `width`, or `height`
- the shell loads `assets/js/scene.js` and `assets/css/styles.css`, and no URL is root-absolute
- `assets/js/scene.js` contains no scene-specific strings (claim ids, scene paths) and uses the `wde-` prefix
- `styles.css` mentions each generated class and state class

`check_render_contract.py --gallery` checks `index.html`: the gallery IDs above (including the grand-theory IDs), relative URLs, that it loads `assets/js/gallery.js` and `assets/css/styles.css`, and that `gallery.js` reads `scenes/index.json`. `validate_site.py` runs both checks whenever the shells exist.
