(function () {
  'use strict';

  var ID_RE = /^[a-z0-9][a-z0-9-]{0,39}$/;
  var STATE_KEYS = ['seen', 'census', 'redactions', 'board', 'clock'];
  var SCENE_ID = '';
  var BASE = '';
  var MANIFEST_IDS = [];
  var PREFIX = 'wde-';
  var SVG_NS = 'http://www.w3.org/2000/svg';
  var HOVER_SEL = '.pin, .board-card, .hero-string, .board-string';
  var ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

  var DATA = null;
  var claims = [];
  var claimById = new Map();
  var stripes = [];
  var pairs = [];
  var pairIndex = new Map();
  var neighbors = new Map();
  var memo = new Map();

  var activeSpec = null;
  var hoverEl = null;
  var litIndex = 0;
  var verdictStarted = false;
  var redEl = null;
  var driftTimer = null;
  var pulseTimers = new Map();
  var spotRegion = null;
  var spotOpener = null;
  var cipherPlain = false;

  function $(id) { return document.getElementById(id); }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function svgEl(tag, attrs) {
    var n = document.createElementNS(SVG_NS, tag);
    Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    return n;
  }

  function reducedMotion() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function narrow() {
    return !!(window.matchMedia && window.matchMedia('(max-width: 719px)').matches);
  }

  function pick(list) {
    return list[Math.floor(Math.random() * list.length)];
  }

  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

  function mulberry32(seed) {
    return function () {
      seed = (seed + 0x6d2b79f5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* ---------- persistence (localStorage with in-memory fallback) ---------- */

  function load(key, fallback) {
    try {
      var raw = localStorage.getItem(PREFIX + key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch (e) {
      return memo.has(key) ? memo.get(key) : fallback;
    }
  }

  function save(key, value) {
    memo.set(key, value);
    try { localStorage.setItem(PREFIX + key, JSON.stringify(value)); } catch (e) { /* storage unavailable */ }
  }

  function clearState() {
    STATE_KEYS.forEach(function (k) {
      memo.delete(k);
      try { localStorage.removeItem(PREFIX + k); } catch (e) { /* storage unavailable */ }
    });
  }

  function asset(path) { return BASE + path; }

  function seenSet() { return new Set(load('seen', [])); }
  function redactionSet() { return new Set(load('redactions', [])); }

  /* ---------- text & inline markup (escape first, then convert) ---------- */

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return ESC[c]; });
  }

  function ctxFor(scope) { return { scope: scope, n: 0 }; }

  function markup(text, ctx) {
    var revealed = redactionSet();
    var s = esc(text == null ? '' : text);
    s = s.replace(/\[\[([\s\S]+?)\|([\s\S]+?)\]\]/g, function (_, shown, reveal) {
      var key = ctx.scope + ':' + ctx.n++;
      var on = revealed.has(key);
      return '<button type="button" class="redact' + (on ? ' is-revealed' : '') +
        '" data-key="' + key + '" data-shown="' + shown + '" data-reveal="' + reveal +
        '" aria-label="Redacted. Activate to reveal.">' + (on ? reveal : shown) + '</button>';
    });
    return s.replace(/==([\s\S]+?)==/g, '<mark>$1</mark>').replace(/~~([\s\S]+?)~~/g, '<s>$1</s>');
  }

  function fill(node, text, ctx) {
    if (node) node.innerHTML = markup(text, ctx || ctxFor('misc'));
  }

  function stripMarkup(t) {
    return t.replace(/\[\[([^|\]]+)\|[^\]]*\]\]/g, '$1').replace(/==|~~/g, '');
  }

  function chip(id) {
    var c = claimById.get(id);
    var a = el('a', 'link-chip', c ? '→ PROOF #' + c.num : '→ PROOF');
    a.href = '#claim-' + id;
    return a;
  }

  function shorten(t, n) {
    if (t.length <= n) return t;
    var cut = t.slice(0, n);
    var sp = cut.lastIndexOf(' ');
    return (sp > 12 ? cut.slice(0, sp) : cut).replace(/[ ,.:;]+$/, '') + '…';
  }

  /* ---------- geometry ---------- */

  function pairKeyOf(a, b) { return a < b ? a + '|' + b : b + '|' + a; }

  function center(r) { return { x: r.x + r.w / 2, y: r.y + r.h / 2 }; }

  function curve(a, b) {
    var d = Math.hypot(b.x - a.x, b.y - a.y);
    var cx = (a.x + b.x) / 2;
    var cy = (a.y + b.y) / 2 + 0.12 * d;
    return {
      d: 'M' + a.x.toFixed(1) + ' ' + a.y.toFixed(1) + ' Q' + cx.toFixed(1) + ' ' + cy.toFixed(1) +
        ' ' + b.x.toFixed(1) + ' ' + b.y.toFixed(1),
      mid: { x: 0.25 * a.x + 0.5 * cx + 0.25 * b.x, y: 0.25 * a.y + 0.5 * cy + 0.25 * b.y }
    };
  }

  function prepare(data) {
    DATA = data;
    claims = data.claims || [];
    claims.forEach(function (c) { claimById.set(c.id, c); });
    stripes = data.stripes || [];
    claims.forEach(function (c) {
      (c.links || []).forEach(function (l) {
        if (!claimById.has(l.to)) return;
        var key = pairKeyOf(c.id, l.to);
        if (!pairIndex.has(key)) {
          pairIndex.set(key, pairs.length);
          pairs.push({ a: c.id, b: l.to, label: l.label, key: key });
        }
        if (!neighbors.has(c.id)) neighbors.set(c.id, new Set());
        if (!neighbors.has(l.to)) neighbors.set(l.to, new Set());
        neighbors.get(c.id).add(l.to);
        neighbors.get(l.to).add(c.id);
      });
    });
  }

  /* ---------- chrome ---------- */

  function renderChrome() {
    var s = DATA.site;
    var set = function (id, text) { var n = $(id); if (n) n.textContent = text; };
    set('site-banner', s.banner);
    set('case-number', s.caseNumber);
    set('last-updated', s.lastUpdated);
    set('site-title', s.title);
    set('site-subtitle', s.subtitle);
    set('census-instructions', s.censusInstructions);
    if (s.title) document.title = s.title;
    fill($('hero-caption'), s.heroCaption, ctxFor('hero'));

    var hero = $('hero-image');
    if (hero) {
      hero.width = DATA.image.width;
      hero.height = DATA.image.height;
      hero.alt = DATA.image.alt || '';
      hero.src = asset(DATA.image.src);
    }

    var marquee = $('site-marquee');
    if (marquee) {
      var track = el('span', 'marquee-track');
      for (var i = 0; i < 2; i++) track.append(el('span', null, s.marquee + '\u2003\u2605\u2003'));
      marquee.replaceChildren(track);
    }

    save('visits', load('visits', 0) + 1);
    renderHits();
  }

  function renderHits() {
    var node = $('hit-counter');
    if (!node || !DATA) return;
    var total = String(DATA.site.hitCounterBase + load('visits', 0)).padStart(7, '0');
    node.replaceChildren();
    for (var i = 0; i < total.length; i++) node.append(el('span', 'digit', total[i]));
  }

  function startClock() {
    var node = $('case-clock');
    function startTime() {
      var t = load('clock', null);
      if (typeof t !== 'number') { t = Date.now(); save('clock', t); }
      return t;
    }
    function tick() {
      if (node) node.textContent = 'Hours awake: ' + ((Date.now() - startTime()) / 3600000).toFixed(2);
    }
    tick();
    setInterval(tick, 1000);
  }

  function renderFooter() {
    var footer = $('site-footer');
    if (!footer || !DATA.footer) return;
    var p = footer.querySelector('.disclaimer');
    if (!p) { p = el('p', 'disclaimer'); footer.prepend(p); }
    p.textContent = DATA.footer;
  }

  /* ---------- static-ish sections ---------- */

  function renderIntro() {
    var root = $('intro');
    if (!root) return;
    root.replaceChildren();
    DATA.site.intro.forEach(function (t, i) {
      var p = el('p');
      fill(p, t, ctxFor('intro:' + i));
      root.append(p);
    });
  }

  function renderUpdates() {
    var root = $('updates');
    if (!root) return;
    root.replaceChildren();
    (DATA.updates || []).forEach(function (u, i) {
      var li = el('li', 'update');
      li.append(el('span', 'update-time', u.time), ' ');
      var text = el('span', 'update-text');
      fill(text, u.text, ctxFor('update:' + i));
      li.append(text, ' ');
      var c = claimById.get(u.claim);
      var link = el('a', 'update-link', c ? '→ PROOF #' + c.num : '');
      if (c) link.href = '#claim-' + u.claim;
      li.append(link);
      root.append(li);
    });
  }

  function renderReceipts() {
    var root = $('receipts');
    if (!root) return;
    root.replaceChildren();
    (DATA.receipts || []).forEach(function (r, i) {
      var tr = el('tr', 'receipt');
      tr.append(el('td', 'r-item', r.item), el('td', 'r-price', r.price));
      var note = el('td', 'r-note');
      fill(note, r.note, ctxFor('receipt:' + i));
      var last = el('td');
      last.append(chip(r.claim));
      tr.append(note, last);
      root.append(tr);
    });
  }

  function renderGuestbook() {
    var root = $('guestbook');
    if (!root) return;
    root.replaceChildren();
    (DATA.guestbook || []).forEach(function (g, i) {
      var entry = el('div', 'gb-entry');
      var meta = el('p', 'gb-meta');
      meta.append(el('span', 'gb-name', g.name), ' ', el('span', 'gb-date', g.date));
      var text = el('p', 'gb-text');
      fill(text, g.text, ctxFor('gb:' + i));
      var reply = el('p', 'gb-reply');
      var replyText = el('span');
      fill(replyText, g.reply, ctxFor('gb:' + i + ':reply'));
      reply.append(el('b', null, 'WEBMASTER:'), ' ', replyText, ' ', chip(g.claim));
      entry.append(meta, text, reply);
      root.append(entry);
    });
  }

  function renderCipher() {
    var code = $('cipher-text');
    var btn = $('cipher-toggle');
    var cipher = DATA.cipher;
    if (!cipher) return;
    if (code) {
      code.replaceChildren();
      if (cipherPlain) {
        var span = el('span');
        fill(span, cipher.plain, ctxFor('cipher'));
        code.append(span, ' ', chip(cipher.claim));
      } else {
        code.textContent = cipher.cipher;
      }
    }
    if (btn) {
      btn.textContent = cipherPlain ? 'ENCODE' : 'DECODE';
      btn.setAttribute('aria-pressed', String(cipherPlain));
    }
  }

  function toggleCipher() {
    cipherPlain = !cipherPlain;
    renderCipher();
  }

  /* ---------- hero overlay ---------- */

  function pickDriftPoint(rx, ry) {
    var W = DATA.image.width, H = DATA.image.height;
    var boxes = claims.map(function (c) { return c.region; })
      .concat(stripes.map(function (s) { return s.region; }));
    for (var i = 0; i < 300; i++) {
      var x = rx + 8 + Math.random() * (W - 2 * rx - 16);
      var y = ry + 8 + Math.random() * (H - 2 * ry - 16);
      var hit = boxes.some(function (r) {
        return Math.abs(x - (r.x + r.w / 2)) < r.w / 2 + rx && Math.abs(y - (r.y + r.h / 2)) < r.h / 2 + ry;
      });
      if (!hit) return { x: x, y: y };
    }
    return null;
  }

  function buildHero() {
    var svg = $('hero-overlay');
    if (!svg || !DATA) return;
    svg.replaceChildren();
    svg.setAttribute('viewBox', '0 0 ' + DATA.image.width + ' ' + DATA.image.height);
    svg.setAttribute('preserveAspectRatio', 'none');
    var counted = load('census', { count: 0, ids: [] }).ids;

    stripes.forEach(function (s) {
      var r = s.region;
      var rect = svgEl('rect', {
        class: 'stripe-hit', 'data-stripe': s.id, x: r.x, y: r.y, width: r.w, height: r.h,
        tabindex: 0, role: 'button', 'aria-label': s.label
      });
      if (counted.indexOf(s.id) !== -1) rect.classList.add('is-counted');
      svg.appendChild(rect);
    });

    pairs.forEach(function (p) {
      var g = curve(center(claimById.get(p.a).region), center(claimById.get(p.b).region));
      svg.appendChild(svgEl('path', {
        class: 'hero-string', 'data-from': p.a, 'data-to': p.b, d: g.d, 'pointer-events': 'stroke'
      }));
    });

    pairs.forEach(function (p) {
      var g = curve(center(claimById.get(p.a).region), center(claimById.get(p.b).region));
      var t = svgEl('text', {
        class: 'string-label', 'data-from': p.a, 'data-to': p.b, x: g.mid.x.toFixed(1), y: g.mid.y.toFixed(1), 'text-anchor': 'middle'
      });
      t.textContent = p.label;
      svg.appendChild(t);
    });

    claims.forEach(function (c) {
      var ctr = center(c.region);
      var cx = ctr.x.toFixed(1), cy = ctr.y.toFixed(1);
      var g = svgEl('g', {
        class: 'pin', 'data-claim': c.id, tabindex: 0, role: 'button',
        'aria-label': 'Proof #' + c.num + ': ' + c.title
      });
      g.appendChild(svgEl('circle', { class: 'pin-head', cx: cx, cy: cy, r: 11 }));
      var num = svgEl('text', { class: 'pin-num', x: cx, y: cy, 'text-anchor': 'middle', dy: '0.35em' });
      num.textContent = String(c.num);
      g.appendChild(num);
      svg.appendChild(g);
    });

    if (!redEl) redEl = svgEl('ellipse', { class: 'red-circle', rx: 44, ry: 30 });
    redEl.style.pointerEvents = 'none';
    var start = pickDriftPoint(44, 30) || { x: DATA.image.width / 2, y: DATA.image.height / 2 };
    redEl.setAttribute('cx', start.x.toFixed(1));
    redEl.setAttribute('cy', start.y.toFixed(1));
    svg.appendChild(redEl);
  }

  function drift() {
    if (!redEl || reducedMotion()) return;
    var p = pickDriftPoint(44, 30);
    if (!p) return;
    redEl.style.transition = 'cx 2.2s ease-in-out, cy 2.2s ease-in-out';
    redEl.setAttribute('cx', p.x.toFixed(1));
    redEl.setAttribute('cy', p.y.toFixed(1));
  }

  function startDrift() {
    if (driftTimer) clearInterval(driftTimer);
    if (!redEl || reducedMotion()) return;
    driftTimer = setInterval(drift, 2500);
  }

  /* ---------- board ---------- */

  function validPos(p) {
    return p && typeof p.x === 'number' && typeof p.y === 'number' && isFinite(p.x) && isFinite(p.y) ? p : null;
  }

  function buildBoard() {
    var board = $('board');
    if (!board || !DATA) return;
    var svg = $('board-strings');
    if (!svg) {
      svg = svgEl('svg', { id: 'board-strings' });
      board.insertBefore(svg, board.firstChild);
    }
    svg.style.position = 'absolute';
    svg.style.left = '0';
    svg.style.top = '0';
    svg.style.overflow = 'visible';
    svg.style.pointerEvents = 'none';
    board.querySelectorAll('.board-card').forEach(function (n) { n.remove(); });

    var saved = load('board', {});
    var rand = mulberry32(1956);
    var rows = Math.max(1, Math.ceil(claims.length / 4));
    var rowStep = 93 / rows;
    board.style.setProperty('--rows', String(rows));
    claims.forEach(function (c, i) {
      var col = i % 4, row = Math.floor(i / 4);
      var dx = (rand() * 2 - 1) * 1.2;
      var dy = (rand() * 2 - 1) * 1.5;
      var tilt = rand() * 12 - 6;
      var def = { x: 2 + col * 24.5 + dx, y: 3 + row * rowStep + dy };
      var pos = validPos(saved[c.id]) || def;

      var card = el('div', 'board-card');
      card.dataset.claim = c.id;
      card.tabIndex = 0;
      card.setAttribute('aria-label', 'Proof ' + c.num + ': ' + c.title);
      card.style.left = pos.x.toFixed(2) + '%';
      card.style.top = pos.y.toFixed(2) + '%';
      card.style.setProperty('--tilt', tilt.toFixed(2) + 'deg');

      var img = el('img', 'board-thumb');
      img.src = asset(c.asset);
      img.alt = c.alt;
      img.loading = 'lazy';
      var title = el('span', 'board-title', 'PROOF #' + c.num + ' ' + shorten(c.title, 30));
      card.append(el('span', 'pushpin'), img, title);
      board.appendChild(card);
    });
    drawBoardStrings();
  }

  function drawBoardStrings() {
    var board = $('board');
    var svg = $('board-strings');
    if (!board || !svg) return;
    svg.replaceChildren();
    if (narrow()) return;

    var bw = board.clientWidth, bh = board.clientHeight;
    svg.setAttribute('width', bw);
    svg.setAttribute('height', bh);
    svg.setAttribute('viewBox', '0 0 ' + bw + ' ' + bh);
    var br = board.getBoundingClientRect();

    var anchor = function (id) {
      var pin = board.querySelector('.board-card[data-claim="' + id + '"] .pushpin');
      if (!pin) return null;
      var r = pin.getBoundingClientRect();
      return { x: r.left - br.left + r.width / 2, y: r.top - br.top + r.height / 2 };
    };

    pairs.forEach(function (p) {
      var a = anchor(p.a), b = anchor(p.b);
      if (!a || !b) return;
      svg.appendChild(svgEl('path', {
        class: 'board-string', 'data-from': p.a, 'data-to': p.b,
        d: curve(a, b).d, 'pointer-events': 'stroke'
      }));
    });

    pairs.forEach(function (p) {
      var a = anchor(p.a), b = anchor(p.b);
      if (!a || !b) return;
      var mid = curve(a, b).mid;
      var t = svgEl('text', {
        class: 'board-label', x: mid.x.toFixed(1), y: mid.y.toFixed(1), 'text-anchor': 'middle'
      });
      t.textContent = p.label;
      svg.appendChild(t);
    });

    applyLit();
    applyActive();
  }

  function setupDrag() {
    var board = $('board');
    if (!board) return;
    var drag = null;

    board.addEventListener('pointerdown', function (e) {
      if (e.button !== 0 || narrow()) return;
      var card = e.target.closest ? e.target.closest('.board-card') : null;
      if (!card) return;
      drag = {
        card: card, id: card.dataset.claim, x0: e.clientX, y0: e.clientY,
        left: parseFloat(card.style.left) || 0, top: parseFloat(card.style.top) || 0,
        x: null, y: null, moved: false
      };
    });

    window.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x0, dy = e.clientY - drag.y0;
      if (!drag.moved) {
        if (Math.hypot(dx, dy) < 4) return;
        drag.moved = true;
        document.body.classList.add('is-dragging');
      }
      var bw = board.clientWidth, bh = board.clientHeight;
      var maxX = Math.max(0, 100 - (drag.card.offsetWidth / bw) * 100);
      var maxY = Math.max(0, 100 - (drag.card.offsetHeight / bh) * 100);
      drag.x = clamp(drag.left + (dx / bw) * 100, 0, maxX);
      drag.y = clamp(drag.top + (dy / bh) * 100, 0, maxY);
      drag.card.style.left = drag.x.toFixed(2) + '%';
      drag.card.style.top = drag.y.toFixed(2) + '%';
      if (window.getSelection) window.getSelection().removeAllRanges();
      drawBoardStrings();
    });

    var end = function () {
      if (!drag) return;
      if (drag.moved) {
        var saved = load('board', {});
        saved[drag.id] = { x: drag.x, y: drag.y };
        save('board', saved);
      }
      document.body.classList.remove('is-dragging');
      drag = null;
    };
    window.addEventListener('pointerup', end);
    window.addEventListener('pointercancel', end);
  }

  /* ---------- claims ---------- */

  function buildClaims() {
    var root = $('claims');
    if (!root) return;
    root.replaceChildren();
    var seen = seenSet();

    claims.forEach(function (c, i) {
      var ctx = ctxFor(c.id);
      var art = el('article', 'claim');
      art.id = 'claim-' + c.id;
      art.dataset.claim = c.id;
      art.dataset.paranoia = String(c.paranoia);

      var head = el('header', 'claim-head');
      var h = el('h3', 'claim-title');
      fill(h, c.title, ctx);
      head.append(el('span', 'claim-num', 'PROOF #' + c.num), h, el('span', 'rubber-stamp', c.stamp));

      var polaroidCls = 'polaroid' + (i % 5 === 2 ? ' is-torn' : '') + (i % 7 === 3 ? ' is-upside-down' : '');
      var fig = el('figure', polaroidCls);
      var img = el('img', 'crop');
      img.loading = 'lazy';
      img.src = asset(c.asset);
      img.alt = c.alt;
      var cap = el('figcaption', 'scrawl');
      fill(cap, c.caption, ctx);
      fig.append(el('span', 'tape'), img, cap);

      var body = el('div', 'claim-body');
      var facts = el('ol', 'facts');
      c.facts.forEach(function (f, fi) {
        var li = el('li', 'fact');
        if (seen.has(c.id + ':' + fi)) li.classList.add('is-seen');
        var span = el('span', 'fact-text');
        fill(span, f.text, ctx);
        var btn = el('button', 'see-btn', 'SEE FOR YOURSELF');
        btn.type = 'button';
        btn.dataset.claim = c.id;
        btn.dataset.fact = String(fi);
        li.append(span, btn);
        facts.append(li);
      });

      var leap = el('p', 'leap');
      fill(leap, c.leap, ctx);
      var sticky = el('aside', 'sticky');
      fill(sticky, c.note, ctx);
      body.append(fig, facts, leap, sticky);

      var upd = el('p', 'claim-update');
      var updText = el('span');
      fill(updText, c.update.text, ctx);
      upd.append(el('span', 'update-time', 'UPDATE ' + c.update.time + ':'), ' ', updText);

      var links = el('ul', 'claim-links');
      (c.links || []).forEach(function (l) {
        var target = claimById.get(l.to);
        if (!target) return;
        var a = el('a', 'link-chip', '→ PROOF #' + target.num + ': ' + l.label);
        a.href = '#claim-' + l.to;
        var li = el('li');
        li.append(a);
        links.append(li);
      });
      (Array.isArray(c.crossLinks) ? c.crossLinks : []).forEach(function (x) {
        if (!x || typeof x.scene !== 'string' || typeof x.claim !== 'string') return;
        if (x.scene === SCENE_ID || MANIFEST_IDS.indexOf(x.scene) === -1) return;
        var a = el('a', 'link-chip cross-chip', '⇢ OTHER CASE FILE (' + x.scene + '): ' + (x.label || ''));
        a.href = 'scene.html?id=' + encodeURIComponent(x.scene) + '#claim-' + encodeURIComponent(x.claim);
        var li = el('li');
        li.append(a);
        links.append(li);
      });

      art.append(head, body, upd, links);
      if (c.facts.every(function (_, fi) { return seen.has(c.id + ':' + fi); })) art.classList.add('is-seen');
      root.append(art);
    });
  }

  /* ---------- lineup ---------- */

  function suspectCard(s) {
    var card = el('div', 'suspect');
    var r = s.region;
    card.dataset.region = [r.x, r.y, r.w, r.h].join(',');
    var img = el('img', 'crop');
    img.loading = 'lazy';
    img.src = asset(s.asset);
    img.alt = s.alt;
    card.append(img, el('h4', 'suspect-name', s.name));

    var has = el('ul', 'suspect-has');
    (s.has || []).forEach(function (t) { has.append(el('li', null, '✔ ' + t)); });
    var missing = el('ul', 'suspect-missing');
    (s.missing || []).forEach(function (t) { missing.append(el('li', null, '✘ ' + t)); });
    card.append(has, missing);

    if (s.id) {
      var btn = el('button', 'see-btn', 'SEE FOR YOURSELF');
      btn.type = 'button';
      btn.dataset.lineup = s.id;
      card.append(btn);
    }
    return card;
  }

  function buildLineup() {
    var root = $('lineup');
    if (!root || !DATA) return;
    root.replaceChildren();
    var ref = DATA.lineupReference;
    var refClaim = ref && claimById.get(ref.claim);
    if (refClaim) {
      root.append(suspectCard({
        name: ref.name, region: refClaim.region, asset: refClaim.asset, alt: refClaim.alt,
        has: ref.has || [], missing: ref.missing || []
      }));
    }
    (DATA.lineup || []).forEach(function (l) { root.append(suspectCard(l)); });
  }

  /* ---------- census ---------- */

  function renderCensus() {
    var st = load('census', { count: 0, ids: [] });
    var count = $('census-count');
    if (count) count.textContent = String(st.count);
    document.querySelectorAll('.stripe-hit').forEach(function (r) {
      r.classList.toggle('is-counted', st.ids.indexOf(r.dataset.stripe) !== -1);
    });
  }

  function countStripe(id) {
    var st = load('census', { count: 0, ids: [] });
    var already = st.ids.indexOf(id) !== -1;
    st.count += 1;
    if (!already) st.ids.push(id);
    save('census', st);

    var count = $('census-count');
    if (count) count.textContent = String(st.count);
    document.querySelectorAll('.stripe-hit[data-stripe="' + id + '"]').forEach(function (r) {
      r.classList.add('is-counted');
    });

    var log = $('census-log');
    if (log) {
      log.prepend(el('li', null, already ? 'Already counted. Counting it again.' : pick(DATA.censusComments)));
      while (log.children.length > 8) log.lastElementChild.remove();
    }
  }

  /* ---------- paranoia & seen ---------- */

  function updateClaimSeen(cid) {
    var c = claimById.get(cid);
    var set = seenSet();
    var art = $('claim-' + cid);
    if (!c || !art) return;
    art.classList.toggle('is-seen', c.facts.every(function (_, i) { return set.has(cid + ':' + i); }));
    art.querySelectorAll('.fact').forEach(function (li, i) {
      li.classList.toggle('is-seen', set.has(cid + ':' + i));
    });
  }

  function updateParanoia() {
    var meter = $('paranoia-meter');
    var valid = new Set();
    claims.forEach(function (c) { c.facts.forEach(function (_, i) { valid.add(c.id + ':' + i); }); });
    var total = valid.size;
    var seen = 0;
    seenSet().forEach(function (k) { if (valid.has(k)) seen++; });
    var level = total ? Math.round((100 * seen) / total) : 0;
    if (meter) {
      meter.style.setProperty('--level', String(level));
      meter.setAttribute('aria-valuenow', String(level));
    }
  }

  function markSeen(cid, fi) {
    var set = seenSet();
    set.add(cid + ':' + fi);
    save('seen', Array.from(set));
    updateClaimSeen(cid);
    updateParanoia();
  }

  /* ---------- spotlight ---------- */

  function layoutSpotlight() {
    var view = $('spotlight-view');
    if (!view || !spotRegion || !DATA) return;
    var r = spotRegion;
    var vw = view.clientWidth, vh = view.clientHeight;
    var s = Math.min((0.6 * vw) / r.w, (0.6 * vh) / r.h);
    var cx = r.x + r.w / 2, cy = r.y + r.h / 2;
    var px = vw / 2 - cx * s, py = vh / 2 - cy * s;
    view.style.backgroundSize = (DATA.image.width * s) + 'px ' + (DATA.image.height * s) + 'px';
    view.style.backgroundPosition = px + 'px ' + py + 'px';

    var ring = view.querySelector('.spotlight-ring');
    if (!ring) {
      ring = el('div', 'spotlight-ring');
      ring.style.cssText = 'position:absolute;border:4px solid #d6202a;border-radius:50%;' +
        'box-shadow:0 0 0 9999px rgba(0,0,0,.55);pointer-events:none;';
      view.appendChild(ring);
    }
    var pad = 14;
    ring.style.left = (px + r.x * s - pad) + 'px';
    ring.style.top = (py + r.y * s - pad) + 'px';
    ring.style.width = (r.w * s + 2 * pad) + 'px';
    ring.style.height = (r.h * s + 2 * pad) + 'px';
  }

  function openSpotlight(region, caption, opener) {
    var dlg = $('spotlight'), view = $('spotlight-view');
    if (!dlg || !view || !DATA || !region) return;
    spotRegion = region;
    spotOpener = opener || null;
    var cap = $('spotlight-caption');
    if (cap) fill(cap, caption, ctxFor('spotlight'));
    view.style.backgroundImage = 'url("' + asset(DATA.image.src) + '")';
    view.style.backgroundRepeat = 'no-repeat';
    view.style.position = 'relative';
    view.style.overflow = 'hidden';
    if (!dlg.open) {
      if (typeof dlg.showModal === 'function') dlg.showModal();
      else dlg.setAttribute('open', '');
    }
    layoutSpotlight();
  }

  function closeSpotlight() {
    var dlg = $('spotlight');
    if (dlg && dlg.open) {
      if (typeof dlg.close === 'function') dlg.close();
      else dlg.removeAttribute('open');
    }
    finishSpotlight();
  }

  function finishSpotlight() {
    var view = $('spotlight-view');
    if (view) view.querySelectorAll('.spotlight-ring').forEach(function (n) { n.remove(); });
    spotRegion = null;
    var opener = spotOpener;
    spotOpener = null;
    if (opener && opener.isConnected) opener.focus();
  }

  /* ---------- interaction: redactions, pins, stripes, see buttons ---------- */

  function toggleRedact(btn) {
    var set = redactionSet();
    var key = btn.dataset.key;
    var on = !set.has(key);
    if (on) set.add(key); else set.delete(key);
    save('redactions', Array.from(set));
    btn.classList.toggle('is-revealed', on);
    btn.textContent = on ? btn.dataset.reveal : btn.dataset.shown;
  }

  function onSee(btn) {
    if (btn.dataset.lineup) {
      var suspect = (DATA.lineup || []).filter(function (l) { return l.id === btn.dataset.lineup; })[0];
      if (suspect) openSpotlight(suspect.region, suspect.alt, btn);
      return;
    }
    var c = claimById.get(btn.dataset.claim);
    var fi = parseInt(btn.dataset.fact, 10);
    var fact = c && c.facts[fi];
    if (!fact) return;
    markSeen(c.id, fi);
    openSpotlight(fact.region, fact.text, btn);
  }

  function pulse(id) {
    document.querySelectorAll('.hero-string').forEach(function (p) {
      if (p.dataset.from !== id && p.dataset.to !== id) return;
      var old = pulseTimers.get(p);
      if (old) clearTimeout(old);
      p.classList.add('is-pulsing');
      pulseTimers.set(p, setTimeout(function () {
        p.classList.remove('is-pulsing');
        pulseTimers.delete(p);
      }, 1600));
    });
  }

  function focusClaim(id) {
    var art = $('claim-' + id);
    if (art) art.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
    pulse(id);
  }

  function followHash() {
    var hash = window.location.hash;
    if (hash.indexOf('#claim-') !== 0) return;
    var id;
    try { id = decodeURIComponent(hash.slice(7)); } catch (e) { return; }
    var art = claimById.has(id) ? $('claim-' + id) : null;
    if (!art) return;
    art.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
    art.classList.add('is-pulsing');
    setTimeout(function () { art.classList.remove('is-pulsing'); }, 1600);
    holdScroll(art);
  }

  // Lazy crops above the target load during the scroll and push it down; re-align until they settle.
  function holdScroll(target) {
    if (typeof ResizeObserver !== 'function') return;
    var stopEvents = ['wheel', 'touchstart', 'keydown', 'pointerdown'];
    var height = document.body.offsetHeight;
    var ro = new ResizeObserver(function () {
      if (document.body.offsetHeight === height) return;
      height = document.body.offsetHeight;
      target.scrollIntoView({ behavior: 'instant', block: 'start' });
    });
    var stop = function () {
      ro.disconnect();
      stopEvents.forEach(function (t) { window.removeEventListener(t, stop, true); });
    };
    stopEvents.forEach(function (t) { window.addEventListener(t, stop, true); });
    ro.observe(document.body);
    setTimeout(stop, 3000);
  }

  function activate(el) {
    if (el.classList.contains('pin')) return focusClaim(el.dataset.claim);
    if (el.classList.contains('stripe-hit')) return countStripe(el.dataset.stripe);
  }

  /* ---------- highlighting & lighting ---------- */

  function applyActive() {
    var ids = new Set();
    var strOk = function () { return false; };
    if (activeSpec && activeSpec.claim) {
      var id = activeSpec.claim;
      ids.add(id);
      (neighbors.get(id) || new Set()).forEach(function (n) { ids.add(n); });
      strOk = function (a, b) { return a === id || b === id; };
    } else if (activeSpec && activeSpec.pair) {
      var pa = activeSpec.pair[0], pb = activeSpec.pair[1];
      ids.add(pa);
      ids.add(pb);
      var key = pairKeyOf(pa, pb);
      strOk = function (a, b) { return pairKeyOf(a, b) === key; };
    }
    document.querySelectorAll('.pin, .board-card').forEach(function (n) {
      n.classList.toggle('is-active', ids.has(n.dataset.claim));
    });
    document.querySelectorAll('.hero-string, .board-string, #hero-overlay .string-label').forEach(function (n) {
      n.classList.toggle('is-active', strOk(n.dataset.from, n.dataset.to));
    });
  }

  function applyLit() {
    document.querySelectorAll('.hero-string, .board-string').forEach(function (p) {
      var idx = pairIndex.get(pairKeyOf(p.dataset.from, p.dataset.to));
      p.classList.toggle('is-lit', idx !== undefined && idx < litIndex);
    });
  }

  function specFor(node) {
    if (node.classList.contains('pin') || node.classList.contains('board-card')) {
      return { claim: node.dataset.claim };
    }
    return { pair: [node.dataset.from, node.dataset.to] };
  }

  function setHover(node) {
    hoverEl = node || null;
    activeSpec = node ? specFor(node) : null;
    applyActive();
  }

  function closestHover(target) {
    return target && target.closest ? target.closest(HOVER_SEL) : null;
  }

  function wireHover() {
    document.addEventListener('pointerover', function (e) {
      var node = closestHover(e.target);
      if (node && node !== hoverEl) setHover(node);
    });
    document.addEventListener('pointerout', function (e) {
      var next = closestHover(e.relatedTarget) ||
        closestHover(document.activeElement);
      if (next !== hoverEl) setHover(next);
    });
    document.addEventListener('focusin', function (e) {
      var node = closestHover(e.target);
      if (node && node !== hoverEl) setHover(node);
    });
    document.addEventListener('focusout', function (e) {
      var next = closestHover(e.relatedTarget);
      if (next !== hoverEl) setHover(next);
    });
  }

  function startVerdict() {
    if (verdictStarted) return;
    verdictStarted = true;
    if (reducedMotion()) {
      litIndex = pairs.length;
      applyLit();
      showVerdictInstant();
      return;
    }
    var lightStep = function () {
      if (litIndex >= pairs.length) { typeVerdict(); return; }
      litIndex++;
      applyLit();
      setTimeout(lightStep, 120);
    };
    lightStep();
  }

  function showVerdictInstant() {
    var box = $('verdict-typewriter');
    if (!box || !DATA.verdict) return;
    box.replaceChildren();
    DATA.verdict.lines.forEach(function (line, i) {
      var p = el('p');
      fill(p, line, ctxFor('verdict:' + i));
      box.append(p);
    });
  }

  function typeVerdict() {
    var box = $('verdict-typewriter');
    if (!box || !DATA.verdict) return;
    var lines = DATA.verdict.lines;
    var li = 0, ci = 0, p = null, plain = '';
    box.replaceChildren();
    var step = function () {
      if (li >= lines.length) return;
      if (!p) {
        p = el('p');
        box.append(p);
        plain = stripMarkup(lines[li]);
        ci = 0;
      }
      if (ci < plain.length) {
        ci++;
        p.textContent = plain.slice(0, ci);
        setTimeout(step, 25);
        return;
      }
      fill(p, lines[li], ctxFor('verdict:' + li));
      li++;
      p = null;
      setTimeout(step, 250);
    };
    step();
  }

  /* ---------- full render (init + reset) ---------- */

  function renderAll() {
    renderIntro();
    renderUpdates();
    renderReceipts();
    renderGuestbook();
    buildHero();
    buildBoard();
    buildClaims();
    buildLineup();
    renderCensus();
    updateParanoia();
    applyLit();
    applyActive();
  }

  /* ---------- wiring (once) ---------- */

  function wireEvents() {
    document.addEventListener('click', function (e) {
      var t = e.target;
      if (!(t instanceof Element)) return;
      var redact = t.closest('.redact');
      if (redact) return toggleRedact(redact);
      var see = t.closest('.see-btn');
      if (see) return onSee(see);
      var node = t.closest('.pin, .stripe-hit');
      if (node) return activate(node);
    });

    document.addEventListener('keydown', function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      var card = t.closest('.board-card');
      if (card) {
        var step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
        if (!step) return;
        var cards = Array.prototype.slice.call(document.querySelectorAll('.board-card'));
        var target = cards[cards.indexOf(card) + step];
        if (target) { e.preventDefault(); target.focus(); }
        return;
      }
      if (e.key === 'Enter' || e.key === ' ') {
        var node = t.closest('.pin, .stripe-hit');
        if (node) { e.preventDefault(); activate(node); }
      }
    });

    wireHover();

    var resetBtn = $('paranoia-reset');
    if (resetBtn) resetBtn.addEventListener('click', function () {
      clearState();
      var log = $('census-log');
      if (log) log.replaceChildren();
      renderAll();
    });

    var reqBtn = $('request-investigation');
    if (reqBtn) reqBtn.addEventListener('click', function () {
      var motion = !reducedMotion();
      if (motion) {
        document.body.classList.add('is-flickering');
        setTimeout(function () { document.body.classList.remove('is-flickering'); }, 900);
      }
      window.scrollTo({ top: 0, behavior: motion ? 'smooth' : 'auto' });
    });

    var cipherBtn = $('cipher-toggle');
    if (cipherBtn) cipherBtn.addEventListener('click', toggleCipher);

    var closeBtn = $('spotlight-close');
    if (closeBtn) closeBtn.addEventListener('click', closeSpotlight);

    var dlg = $('spotlight');
    if (dlg) dlg.addEventListener('close', finishSpotlight);

    setupDrag();
  }

  function start(data) {
    prepare(data);
    renderChrome();
    renderCipher();
    renderFooter();
    var verdictBtn = $('request-investigation');
    if (verdictBtn && data.verdict) verdictBtn.textContent = data.verdict.button;
    renderAll();
    startClock();
    startDrift();
    wireEvents();

    window.addEventListener('resize', function () {
      drawBoardStrings();
      layoutSpotlight();
    });

    var board = $('board');
    if (board && typeof ResizeObserver === 'function') {
      new ResizeObserver(function () { drawBoardStrings(); }).observe(board);
    }

    var box = $('verdict-typewriter');
    if (!box || reducedMotion() || typeof IntersectionObserver !== 'function') {
      startVerdict();
    } else {
      var io = new IntersectionObserver(function (entries) {
        if (entries.some(function (en) { return en.isIntersecting; })) {
          io.disconnect();
          startVerdict();
        }
      }, { threshold: 0.2 });
      io.observe(box);
    }

    followHash();
  }

  /* ---------- scene selection & navigation ---------- */

  function getJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' responded ' + r.status);
      return r.json();
    });
  }

  function sceneIds(manifest) {
    return ((manifest && manifest.scenes) || [])
      .map(function (s) { return s && s.id; })
      .filter(function (id) { return typeof id === 'string' && ID_RE.test(id); });
  }

  function renderNav(ids) {
    var nav = $('scene-nav');
    if (!nav) return;
    var i = ids.indexOf(SCENE_ID);
    if (i === -1 || ids.length < 2) return;
    var add = function (id, label, rel) {
      var a = el('a', 'scene-nav-' + rel, label);
      a.href = 'scene.html?id=' + encodeURIComponent(id);
      a.rel = rel;
      nav.append(' ', a);
    };
    if (i > 0) add(ids[i - 1], '← Previous case file', 'prev');
    if (i < ids.length - 1) add(ids[i + 1], 'Next case file →', 'next');
  }

  function renderTheoryLink(manifest) {
    var p = $('theory-link');
    var theory = manifest && manifest.theory;
    if (!p || !theory || typeof theory !== 'object' || !Array.isArray(theory.scenes)) return;
    if (theory.scenes.indexOf(SCENE_ID) === -1 || !theory.title) return;
    var a = el('a', null, stripMarkup(String(theory.title)));
    a.href = 'index.html#grand-theory';
    p.replaceChildren('★ ', a, ' ★');
    p.hidden = false;
  }

  function showMissing(manifest) {
    document.body.classList.add('is-missing');
    var box = $('case-missing');
    if (box) box.hidden = false;
    document.title = 'Case file not found.';
    var footer = manifest && manifest.site && manifest.site.footer;
    var p = document.querySelector('#site-footer .disclaimer');
    if (p && footer) p.textContent = footer;
  }

  function init() {
    var requested = null;
    try { requested = new URLSearchParams(window.location.search).get('id'); } catch (e) { /* no query */ }

    getJSON('scenes/index.json')
      .catch(function () { return null; })
      .then(function (manifest) {
        var ids = sceneIds(manifest);
        var id = requested === null || requested === '' ? ids[0] : requested;
        var known = manifest ? ids.indexOf(id) !== -1 : true;
        if (!id || !ID_RE.test(id) || !known) { showMissing(manifest); return; }
        SCENE_ID = id;
        MANIFEST_IDS = ids;
        BASE = 'scenes/' + id + '/';
        PREFIX = 'wde-' + id + '-';
        return getJSON(BASE + 'case.json').then(function (data) {
          if (!data || !data.image || !data.site) { showMissing(manifest); return; }
          renderNav(ids);
          renderTheoryLink(manifest);
          start(data);
        }, function () { showMissing(manifest); });
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
