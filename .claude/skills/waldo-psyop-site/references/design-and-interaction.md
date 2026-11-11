# Site Sections, Design, and Interaction

## Site sections (top to bottom)

1. **Chrome**: `site-banner` (black/yellow hazard bar), `site-marquee`, a header strip with `case-number`, `case-clock`, `hit-counter` ("You are visitor #"), `last-updated`, and `scene-nav` (a link back to the gallery, `index.html`, labelled "All case files"; optionally previous/next case files).
2. **Hero**: `site-title`, `site-subtitle`, then `hero` with pins and **labelled red strings drawn across the scene between linked claims**. A red marker circle drifts over the crowd and never settles.
3. **Intro letter** ("READ THIS FIRST"): `intro`.
4. **The Board**: corkboard of claim cards with labelled strings between linked cards. Cards are draggable on desktop (positions persist). Below 720 px it becomes a stacked list with link chips and no SVG strings.
5. **The Proofs**: `claims`, one per claim, in order.
6. **The Lineup**: `lineup`, the `lineupReference` card first (if present; on the beach it is the stamp), then suspects with ✔ has / ✘ missing.
7. **Stripe Census**: `census-instructions` (from `site.censusInstructions`) plus `census-count` and `census-log`. Hotspots live on the hero image.
8. **Investigation Log**: `updates`.
9. **Receipts**: table with `receipts`.
10. **Guestbook**: `guestbook` (normal readers push back; the webmaster replies in character).
11. **The Verdict**: `verdict-typewriter`, `paranoia-meter`, `paranoia-reset`, `request-investigation`.
12. **Footer**: `site-footer` disclaimer, `cipher-toggle` and `cipher-text`.

Section headings and neutral UI labels (for example "READ THIS FIRST", "Close", "You are visitor #", "All case files") may be hardcoded by Builder B. All narrative copy comes from `case.json` (scene page) or `scenes/index.json` (gallery).

The gallery (`index.html`) uses the same design: hazard banner, cream paper, the same fonts, star rules, and the "Best viewed at 800×600" badge, with one "case file" card per scene. See [render-contract.md](render-contract.md#gallery-indexhtml--assetsjsgalleryjs).

## Design: "personal homepage meets 3 a.m. corkboard"

It must look homemade, not designed.

- **Early-2000s personal site:** Times New Roman body on cream "paper", **Comic Neue** or **Caveat** for scrawl, **Special Elite** for typewriter and case text, and one heavy condensed face (e.g. **Anton**) for the title. Blue underlined links, visited links purple. A hazard-tape banner, a scrolling marquee (CSS), and a hit counter in odometer digits. Horizontal rules made of a repeated `★ ★ ★` or a red-and-white stripe gradient. Slightly uneven column widths. A "Best viewed at 800×600" badge.
- **Corkboard:** cork texture from CSS gradients, polaroids with tape, sticky notes (yellow, rotated), rubber stamps (red, rotated, semi-transparent, `mix-blend-mode: multiply`), and red marker circles and underlines.
- **Highlighter:** `mark` is a yellow highlighter swipe (gradient with ragged edges).
- **Palette:** sand yellow `#f5d84a`, sea blue `#2a7fbf`, stripe red `#d6202a`, white, cork brown, ink `#1b1b1b`. The palette is shared by every scene. Body text WCAG AA on its background.
- **Responsive:** 360 px to 1440 px. No horizontal scroll at 360 px.
- **Accessibility:** alt text on every image; every interactive element keyboard reachable with visible focus; `Esc` closes the spotlight; respect `prefers-reduced-motion` (no marquee scroll, no flicker, no typewriter, no drifting circle; text appears instantly).

## Interaction details

- **SEE FOR YOURSELF** opens `spotlight`. `spotlight-view` shows the real image zoomed so the region fills about 60% of the view, with a red marker ring around the region and the rest dimmed. Each use raises the paranoia meter and marks the claim `.is-seen` (persisted).
- **Hero pins**: clicking one scrolls to its claim and pulses its strings. Hovering a pin, card, or string highlights the linked pair everywhere (hero strings, board strings, board cards).
- **Stripe Census**: clicking a hotspot on the hero image marks it `.is-counted` (persisted), increments the count, and logs a random `censusComments` line. Re-clicking a counted stripe still increments the count but logs "Already counted. Counting it again." The count persists.
- **Paranoia meter**: `--level` = percentage of distinct facts seen (persisted). Reset clears seen, census, redactions, and card positions for the current scene only.
- **Verdict**: when it scrolls into view, light hero and board strings one by one (`.is-lit`), then type out `verdict.lines`.
- **Request Further Investigation**: flickers the body and scrolls to the top.
- **Cipher**: `cipher-toggle` swaps between `cipher.cipher` and `cipher.plain` (which links to the claim).
- **Keyboard**: `Esc` closes the dialog; arrow keys move focus between board cards; `Enter` or `Space` activate pins and hotspots.
- No console errors. No external JS libraries.

## Implementation notes for Builder C

These notes follow directly from the rules above:

- Wrap every `localStorage` access in `try/catch`, so that private mode does not cause console errors. Prefix every key with `wde-<id>-` so scenes never share state.
- Set the hero SVG `viewBox` to `0 0 {image.width} {image.height}` from `case.json` (never assume a size). Because it uses source-pixel units, pins, strings, and hotspots use raw region numbers. Use the region centre for pins and string endpoints.
- The spotlight background is the scene image (`scenes/<id>/` + `image.src`). To zoom it, set `background-size` and `background-position` so that `max(region.w/view.w, region.h/view.h)` ≈ 0.6. Draw the ring and the dimming with an overlay positioned on the region.
- To count "distinct facts seen", key each fact as `claimId:factIndex`. Lineup SEE buttons open the spotlight but are not claim facts.
- Board positions persist per card ID. Set `body.is-dragging` while a card is being dragged, and turn dragging off below 720 px (stacked-list layout).
