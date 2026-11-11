(function () {
  'use strict';

  var ID_RE = /^[a-z0-9][a-z0-9-]{0,39}$/;
  var MOTIF_RE = /^[A-Za-z0-9][A-Za-z0-9-]{0,39}$/;
  var ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

  function $(id) { return document.getElementById(id); }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function getJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' responded ' + r.status);
      return r.json();
    });
  }

  /* ---------- inline markup (escape first, then convert) ---------- */

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return ESC[c]; });
  }

  function markup(text) {
    var s = esc(text == null ? '' : text);
    s = s.replace(/\[\[([\s\S]+?)\|([\s\S]+?)\]\]/g, function (_, shown, reveal) {
      return '<button type="button" class="redact" data-shown="' + shown + '" data-reveal="' + reveal +
        '" aria-label="Redacted. Activate to reveal.">' + shown + '</button>';
    });
    return s.replace(/==([\s\S]+?)==/g, '<mark>$1</mark>').replace(/~~([\s\S]+?)~~/g, '<s>$1</s>');
  }

  function toggleRedact(btn) {
    var on = !btn.classList.contains('is-revealed');
    btn.classList.toggle('is-revealed', on);
    btn.textContent = on ? btn.dataset.reveal : btn.dataset.shown;
  }

  /* ---------- rendering ---------- */

  function renderSite(site) {
    if (!site) return;
    if (site.title) {
      document.title = site.title;
      $('gallery-title').textContent = site.title;
    }
    if (site.subtitle) $('gallery-subtitle').textContent = site.subtitle;
    var intro = $('gallery-intro');
    intro.replaceChildren();
    (site.intro || []).forEach(function (t) {
      var p = el('p');
      p.innerHTML = markup(t);
      intro.append(p);
    });
    if (site.footer) $('gallery-disclaimer').textContent = site.footer;
  }

  function card(id, data, i) {
    var s = data.site || {};
    var img = data.image || {};
    var count = (data.claims || []).length;

    var li = el('li', 'case-card');
    li.style.setProperty('--tilt', (i % 2 ? 0.8 : -0.9) * (1 + (i % 3) * 0.3) + 'deg');
    var a = el('a', 'case-card-link');
    a.href = 'scene.html?id=' + encodeURIComponent(id);

    var tab = el('span', 'case-card-tab', s.caseNumber || id);
    var thumb = el('span', 'case-card-thumb');
    var pic = el('img');
    pic.loading = 'lazy';
    pic.decoding = 'async';
    if (img.width && img.height) {
      pic.width = img.width;
      pic.height = img.height;
    }
    pic.alt = img.alt || '';
    pic.src = 'scenes/' + id + '/' + img.src;
    thumb.append(pic, el('span', 'case-card-clip'));

    var title = el('h3', 'case-card-title', s.title || id);
    var sub = el('p', 'case-card-sub', s.subtitle || '');
    var meta = el('p', 'case-card-meta');
    meta.append(el('span', 'case-card-count', count + (count === 1 ? ' proof' : ' proofs')));
    if (s.lastUpdated) meta.append(' · ', el('span', 'case-card-updated', 'Last updated: ' + s.lastUpdated));
    var seal = el('span', 'rubber-stamp case-card-stamp', count + (count === 1 ? ' PROOF' : ' PROOFS'));
    seal.setAttribute('aria-hidden', 'true');

    a.append(tab, thumb, title, sub, meta, seal);
    li.append(a);
    return li;
  }

  function renderMarquee(entries) {
    var box = $('gallery-marquee');
    if (!box) return;
    var text = entries.map(function (e) {
      var s = e.data.site || {};
      return [s.caseNumber, s.title].filter(Boolean).join(': ');
    }).join('\u2003\u2605\u2003');
    if (!text) { box.hidden = true; return; }
    var track = el('span', 'marquee-track');
    for (var i = 0; i < 2; i++) track.append(el('span', null, text + '\u2003\u2605\u2003'));
    box.replaceChildren(track);
  }

  function renderCards(ids) {
    var list = $('gallery-cards');
    var status = $('gallery-status');
    return Promise.all(ids.map(function (id) {
      return getJSON('scenes/' + id + '/case.json')
        .then(function (data) { return data && data.image && data.image.src ? { id: id, data: data } : null; })
        .catch(function () { return null; });
    })).then(function (results) {
      var ok = results.filter(Boolean);
      list.replaceChildren();
      ok.forEach(function (e, i) { list.append(card(e.id, e.data, i)); });
      $('gallery-count').textContent = String(ok.length);
      status.textContent = ok.length ? '' : 'No case files found.';
      status.hidden = !!ok.length;
      renderMarquee(ok);
      return ok;
    });
  }

  /* ---------- grand theory ---------- */

  function reducedMotion() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function fillMarkup(node, text) {
    node.innerHTML = markup(text);
    return node;
  }

  function evidenceList(evidence, byId) {
    var ul = el('ul', 'theory-evidence');
    (Array.isArray(evidence) ? evidence : []).forEach(function (ev) {
      if (!ev || typeof ev.scene !== 'string' || typeof ev.claim !== 'string') return;
      var data = byId[ev.scene];
      if (!data) return;
      var claim = (data.claims || []).filter(function (c) { return c && c.id === ev.claim; })[0];
      if (!claim) return;
      var title = (data.site && data.site.title) || ev.scene;
      var a = el('a', 'link-chip evidence-chip', '→ ' + title + ' · PROOF #' + claim.num);
      a.href = 'scene.html?id=' + encodeURIComponent(ev.scene) + '#claim-' + encodeURIComponent(ev.claim);
      var li = el('li');
      li.append(a);
      ul.append(li);
    });
    return ul;
  }

  function setMotifActive(motif, on) {
    var id = motif.dataset.motif;
    motif.classList.toggle('is-active', on);
    document.querySelectorAll('#theory-chain .theory-step').forEach(function (step) {
      var ids = (step.dataset.motifs || '').split(/\s+/);
      if (ids.indexOf(id) !== -1) step.classList.toggle('is-active', on);
    });
  }

  function wireMotif(motif) {
    motif.addEventListener('mouseenter', function () { setMotifActive(motif, true); });
    motif.addEventListener('mouseleave', function () {
      if (!motif.contains(document.activeElement)) setMotifActive(motif, false);
    });
    motif.addEventListener('focusin', function () { setMotifActive(motif, true); });
    motif.addEventListener('focusout', function (e) {
      if (!motif.contains(e.relatedTarget) && !motif.matches(':hover')) setMotifActive(motif, false);
    });
  }

  function renderTheory(theory, entries) {
    var section = $('grand-theory');
    if (!section || !theory || typeof theory !== 'object' || Array.isArray(theory)) return;
    var byId = {};
    entries.forEach(function (e) { byId[e.id] = e.data; });

    fillMarkup($('theory-title'), theory.title || '');

    var thesis = $('theory-thesis');
    thesis.replaceChildren();
    if (theory.thesis) thesis.append(fillMarkup(el('p'), theory.thesis));

    var motifIds = {};
    var motifs = $('theory-motifs');
    motifs.replaceChildren();
    (Array.isArray(theory.motifs) ? theory.motifs : []).forEach(function (m, i) {
      if (!m || typeof m !== 'object') return;
      var box = el('div', 'motif');
      if (typeof m.id === 'string' && MOTIF_RE.test(m.id)) {
        box.id = 'motif-' + m.id;
        box.dataset.motif = m.id;
        motifIds[m.id] = true;
      }
      box.tabIndex = 0;
      box.style.setProperty('--tilt', (i % 2 ? 1.6 : -1.9) * (1 + (i % 3) * 0.25) + 'deg');
      box.append(
        fillMarkup(el('h3', 'motif-name'), m.name || ''),
        fillMarkup(el('p', 'motif-text'), m.text || ''),
        evidenceList(m.evidence, byId)
      );
      if (box.dataset.motif) wireMotif(box);
      motifs.append(box);
    });

    var chain = $('theory-chain');
    chain.replaceChildren();
    (Array.isArray(theory.chain) ? theory.chain : []).forEach(function (step) {
      if (!step || typeof step !== 'object') return;
      var li = el('li', 'theory-step');
      var ids = (Array.isArray(step.motifs) ? step.motifs : []).filter(function (id) { return motifIds[id]; });
      li.dataset.motifs = ids.join(' ');
      li.append(fillMarkup(el('p', 'theory-text'), step.text || ''), evidenceList(step.evidence, byId));
      chain.append(li);
    });

    var verdict = $('theory-verdict');
    verdict.replaceChildren();
    (Array.isArray(theory.verdict) ? theory.verdict : []).forEach(function (line) {
      verdict.append(fillMarkup(el('p', 'theory-verdict-line'), line));
    });

    section.hidden = false;
  }

  function followHash() {
    var hash = window.location.hash;
    if (hash !== '#grand-theory' && !(hash.indexOf('#motif-') === 0 && MOTIF_RE.test(hash.slice(7)))) return;
    var target = $(hash.slice(1));
    var section = $('grand-theory');
    if (!target || !section || section.hidden) return;
    target.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
    target.classList.add('is-pulsing');
    setTimeout(function () { target.classList.remove('is-pulsing'); }, 1600);
  }

  function showEmpty() {
    var status = $('gallery-status');
    status.textContent = 'No case files found.';
    status.hidden = false;
    $('gallery-count').textContent = '0';
  }

  function init() {
    document.addEventListener('click', function (e) {
      var t = e.target;
      var btn = t instanceof Element ? t.closest('.redact') : null;
      if (btn) toggleRedact(btn);
    });

    getJSON('scenes/index.json')
      .then(function (manifest) {
        renderSite(manifest.site);
        var seen = {};
        var ids = (manifest.scenes || [])
          .map(function (s) { return s && s.id; })
          .filter(function (id) {
            if (typeof id !== 'string' || !ID_RE.test(id) || seen[id]) return false;
            seen[id] = true;
            return true;
          });
        if (!ids.length) return showEmpty();
        return renderCards(ids).then(function (ok) {
          if (manifest.theory) {
            renderTheory(manifest.theory, ok);
            followHash();
          }
        });
      })
      .catch(showEmpty);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
