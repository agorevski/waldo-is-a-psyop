#!/usr/bin/env python3
"""Check the page shells against the waldo-psyop render contract.

Usage:
  check_render_contract.py [scene.html] [--css assets/css/styles.css]
  check_render_contract.py --gallery [index.html] [--css assets/css/styles.css]

Scene mode (default, scene.html): every static ID exactly once on the right
element (including census-instructions and scene-nav); hero-overlay has
preserveAspectRatio="none" and at most a placeholder viewBox (scene.js sets the
real one from case.json); hero-image has no hardcoded src, width, or height;
scene.html loads assets/js/scene.js and assets/css/styles.css; scene.js holds no
scene-specific strings; styles.css mentions every generated and state class.

Gallery mode (--gallery, index.html): the gallery IDs exist exactly once,
index.html loads assets/js/gallery.js and assets/css/styles.css, and gallery.js
reads scenes/index.json.

Both modes reject root-absolute URLs (the site is served from a subpath).
Exits 1 if any error is found.
"""
import argparse
import os
import re
import sys
from html.parser import HTMLParser

STATIC_IDS = {
    "site-banner": "div", "site-marquee": "div", "case-number": "span", "case-clock": "span",
    "hit-counter": "span", "last-updated": "span", "site-title": "h1", "site-subtitle": "p",
    "hero": "figure", "hero-image": "img", "hero-overlay": "svg", "hero-caption": "figcaption",
    "intro": "div", "board": "div", "claims": "div", "lineup": "div", "census-count": "span",
    "census-log": "ol", "updates": "ol", "receipts": "tbody", "guestbook": "div",
    "verdict-typewriter": "div", "paranoia-meter": "div", "paranoia-reset": "button",
    "request-investigation": "button", "cipher-toggle": "button", "cipher-text": "code",
    "site-footer": "footer", "spotlight": "dialog", "spotlight-view": "div",
    "spotlight-caption": "p", "spotlight-close": "button",
    "census-instructions": "p", "scene-nav": "nav", "theory-link": "p",
}
GALLERY_IDS = {
    "gallery-title": "h1", "gallery-subtitle": "p", "gallery-intro": "div",
    "gallery-cards": "ul", "gallery-disclaimer": "p",
    "grand-theory": "section", "theory-title": "h2", "theory-thesis": "div",
    "theory-chain": "ol", "theory-motifs": "div", "theory-verdict": "div",
}
GALLERY_CLASSES = ["case-card", "case-card-link", "case-card-thumb", "case-card-title",
                   "theory-step", "theory-text", "theory-evidence", "evidence-chip", "motif",
                   "motif-name", "motif-text", "theory-verdict-line"]
# Strings that would tie the shared engine to one scene.
ENGINE_FORBIDDEN = [r"waldo_beach", r"scenes/beach", r"data/case\.json", r"['\"]P\d{2}['\"]",
                    r"['\"]L\d['\"]", r"['\"]S\d{2}['\"]"]
INSIDE = {"hero-image": "hero", "hero-overlay": "hero", "hero-caption": "hero",
          "spotlight-view": "spotlight", "spotlight-caption": "spotlight",
          "spotlight-close": "spotlight"}
CLASSES = [
    "marquee-track", "digit", "pin", "pin-head", "pin-num", "hero-string", "string-label",
    "stripe-hit", "red-circle", "board-card", "pushpin", "board-thumb", "board-title",
    "board-string", "board-label", "claim", "claim-head", "claim-num", "claim-title",
    "rubber-stamp", "claim-body", "polaroid", "tape", "crop", "scrawl", "facts", "fact",
    "fact-text", "cross-chip", "see-btn", "leap", "sticky", "claim-update", "update-time", "claim-links",
    "link-chip", "suspect", "suspect-name", "suspect-has", "suspect-missing", "gb-entry",
    "gb-meta", "gb-name", "gb-date", "gb-text", "gb-reply", "update", "update-text",
    "update-link", "receipt", "r-item", "r-price", "r-note", "redact", "disclaimer",
    "is-active", "is-lit", "is-pulsing", "is-revealed", "is-seen", "is-counted",
    "is-flickering", "is-dragging",
]
VOID = {"img", "br", "hr", "meta", "link", "input", "source", "area", "base", "col", "embed",
        "param", "track", "wbr"}


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found, self.stack = {}, []

    def handle_starttag(self, tag, attrs):
        at = dict(attrs)
        if "id" in at:
            ancestors = [i for _, i in self.stack if i]
            self.found.setdefault(at["id"], []).append((tag, at, ancestors))
        if tag not in VOID:
            self.stack.append((tag, at.get("id")))

    def handle_startendtag(self, tag, attrs):
        at = dict(attrs)
        if "id" in at:
            self.found.setdefault(at["id"], []).append((tag, at, [i for _, i in self.stack if i]))

    def handle_endtag(self, tag):
        for k in range(len(self.stack) - 1, -1, -1):
            if self.stack[k][0] == tag:
                del self.stack[k:]
                break


def parse(path):
    p = P()
    with open(path, encoding="utf-8") as f:
        text = f.read()
    p.feed(text)
    return p, text


def check_ids(p, ids, errors, inside=None):
    for i, tag in ids.items():
        hits = p.found.get(i, [])
        if len(hits) != 1:
            errors.append(f"#{i}: found {len(hits)} times, expected exactly once")
            continue
        t, _, anc = hits[0]
        if t != tag:
            errors.append(f"#{i}: is <{t}>, expected <{tag}>")
        if inside and i in inside and inside[i] not in anc:
            errors.append(f"#{i}: must be inside #{inside[i]}")


def check_urls(text, name, errors):
    for m in re.finditer(r"""\b(?:src|href)\s*=\s*["']\s*(/(?!/)[^"']*)""", text):
        errors.append(f"{name}: root-absolute URL {m.group(1)!r}; use a relative path (served from a subpath)")


def check_loads(text, name, needles, errors):
    for n in needles:
        if not re.search(r"""(?:src|href)\s*=\s*["'](?:\./)?""" + re.escape(n) + r"""["']""", text):
            errors.append(f"{name}: must load {n} (relative path)")


def check_css(css_path, classes, warnings, extra=("prefers-reduced-motion", "720px", ":focus")):
    if not os.path.isfile(css_path):
        warnings.append(f"{css_path} not found; skipped CSS checks")
        return
    with open(css_path, encoding="utf-8") as f:
        css = f.read()
    for c in classes:
        if not re.search(rf"\.{re.escape(c)}(?![\w-])", css):
            warnings.append(f"styles.css: no rule mentions .{c}")
    for needle in extra:
        if needle not in css:
            warnings.append(f"styles.css: no '{needle}' found")


def check_scene(html, css_path=None):
    """Return (errors, warnings) for scene.html."""
    errors, warnings = [], []
    root = os.path.dirname(os.path.abspath(html))
    css_path = css_path or os.path.join(root, "assets", "css", "styles.css")
    p, text = parse(html)
    check_ids(p, STATIC_IDS, errors, INSIDE)

    ov = p.found.get("hero-overlay", [])
    if len(ov) == 1:
        at = ov[0][1]
        vb = at.get("viewbox")
        if vb is not None and not re.fullmatch(r"\s*-?[\d.]+([\s,]+-?[\d.]+){3}\s*", vb):
            errors.append(f"#hero-overlay: viewBox {vb!r} is not four numbers (a placeholder is fine)")
        if at.get("preserveaspectratio") != "none":
            errors.append("#hero-overlay: preserveAspectRatio must be \"none\"")
    hi = p.found.get("hero-image", [])
    if len(hi) == 1:
        at = hi[0][1]
        if (at.get("src") or "").strip():
            errors.append(f"#hero-image: must not hardcode src (got {at.get('src')!r}); "
                          "scene.js sets it from case.json image.src")
        for k in ("width", "height"):
            if at.get(k):
                errors.append(f"#hero-image: must not hardcode {k}; scene.js sets it from case.json")
        if (at.get("alt") or "").strip():
            warnings.append("#hero-image: hardcoded alt; scene.js should set it from image.alt")

    check_urls(text, os.path.basename(html), errors)
    check_loads(text, os.path.basename(html), ["assets/js/scene.js", "assets/css/styles.css"], errors)

    js = os.path.join(root, "assets", "js", "scene.js")
    if os.path.isfile(js):
        with open(js, encoding="utf-8") as f:
            src = f.read()
        for pat in ENGINE_FORBIDDEN:
            m = re.search(pat, src)
            if m:
                errors.append(f"assets/js/scene.js: scene-specific string {m.group(0)!r}; the engine must "
                              "work for any case.json")
        if re.search(r"""fetch\(\s*["']/(?!/)""", src):
            errors.append("assets/js/scene.js: root-absolute fetch URL; use a relative path")
        if "wde-" not in src:
            warnings.append("assets/js/scene.js: no 'wde-' localStorage prefix found (expected wde-<id>-)")
        if re.search(r"\bbeach\b", src, re.I):
            warnings.append("assets/js/scene.js: mentions 'beach'; the engine should be scene-agnostic")
    else:
        errors.append("assets/js/scene.js not found")

    check_css(css_path, CLASSES, warnings)
    return errors, warnings


def check_gallery(html, css_path=None):
    """Return (errors, warnings) for the gallery index.html."""
    errors, warnings = [], []
    root = os.path.dirname(os.path.abspath(html))
    css_path = css_path or os.path.join(root, "assets", "css", "styles.css")
    p, text = parse(html)
    check_ids(p, GALLERY_IDS, errors)
    check_urls(text, os.path.basename(html), errors)
    check_loads(text, os.path.basename(html), ["assets/js/gallery.js", "assets/css/styles.css"], errors)
    if "800" not in text:
        warnings.append(f"{os.path.basename(html)}: no 'Best viewed at 800x600' badge found")
    js = os.path.join(root, "assets", "js", "gallery.js")
    if os.path.isfile(js):
        with open(js, encoding="utf-8") as f:
            src = f.read()
        if "scenes/index.json" not in src:
            errors.append("assets/js/gallery.js: must read scenes/index.json")
        if re.search(r"""fetch\(\s*["']/(?!/)""", src):
            errors.append("assets/js/gallery.js: root-absolute fetch URL; use a relative path")
        if "scene.html?id=" not in src:
            warnings.append("assets/js/gallery.js: no 'scene.html?id=' link found")
    else:
        errors.append("assets/js/gallery.js not found")
    check_css(css_path, GALLERY_CLASSES, warnings, extra=("prefers-reduced-motion",))
    return errors, warnings


def report(errors, warnings, label):
    for m in warnings:
        print(f"WARN:  {m}")
    for m in errors:
        print(f"ERROR: {m}")
    print(f"{label}: {len(errors)} error(s), {len(warnings)} warning(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", nargs="?", help="scene.html (default) or, with --gallery, index.html")
    ap.add_argument("--gallery", action="store_true", help="check the gallery page instead")
    ap.add_argument("--css", help="styles.css path (default: assets/css/styles.css next to the HTML)")
    a = ap.parse_args()
    html = a.html or ("index.html" if a.gallery else "scene.html")
    if not os.path.isfile(html):
        print(f"ERROR: {html} not found")
        return 1
    if a.gallery:
        errors, warnings = check_gallery(html, a.css)
        report(errors, warnings, f"{html} (gallery): {len(GALLERY_IDS)} ids checked")
    else:
        errors, warnings = check_scene(html, a.css)
        report(errors, warnings, f"{html}: {len(STATIC_IDS)} static ids checked")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
