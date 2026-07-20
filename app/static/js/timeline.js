// ════════════════════════════════════════════════════════════════
//  The Chronicle — a horizontal TIMELINE the explorer travels along.
//  Six era-beats, left→right chronological. Click the lit era to study
//  it; pass its quick-check and the node lights, the rail draws forward,
//  and the next era unlocks. Light all six to unlock the Trial.
//
//  Mirrors the Library/Observatory loop (explore → learn → quick-check →
//  unlock) and their per-user restore. Presentation/progress only — the
//  quick-checks are ungraded and unlogged; only the Trial is graded.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var root = document.getElementById("chronicle");
  if (!root) return;
  var location = root.dataset.location || "chronicle";

  // ── Prefs ──
  var P = window.AtlasPrefs;
  var REDUCE = !!(P && P.effective && P.effective("reduce_motion"));
  var muted = !!(P && P.soundOn && !P.soundOn());

  function json(id) { try { return JSON.parse(document.getElementById(id).textContent) || []; } catch (e) { return []; } }
  var BEATS = json("timeline-beats");
  var HOOKS = json("timeline-hooks");
  var TOTAL = BEATS.length;

  var nodes = Array.prototype.slice.call(document.querySelectorAll(".tl-node"));
  var railFill = document.getElementById("tl-rail-fill");
  var traveller = document.getElementById("tl-traveller");
  var countEl = document.getElementById("tl-count");
  var progFill = document.getElementById("tl-progress-fill");
  var hintEl = document.getElementById("tl-hint");

  var panel = document.getElementById("tl-panel");
  var panelTitle = document.getElementById("tl-panel-title");
  var eraEl = document.getElementById("tl-era");
  var textEl = document.getElementById("tl-text");
  var readSlot = document.getElementById("tl-read-slot");
  var pageRead = document.getElementById("tl-page-read");
  var pageCheck = document.getElementById("tl-page-check");
  var toCheckBtn = document.getElementById("tl-to-check");
  var checkQ = document.getElementById("tl-check-q");
  var checkOpts = document.getElementById("tl-check-opts");
  var checkFb = document.getElementById("tl-check-fb");
  var backBtn = document.getElementById("tl-back-read");
  var stamp = document.getElementById("tl-stamp");
  var closeBtn = document.getElementById("tl-panel-close");

  var trialGate = document.getElementById("tl-trial-gate");
  var trialReady = document.getElementById("tl-trial-ready");

  var lit = 0;              // eras completed (checks passed) — drives everything
  var activeIndex = -1;     // era whose panel is open
  var checkPassed = false;  // has THIS open era's quick-check been passed
  var hooksShown = {};      // guess-first hook shown once per era

  // ── A tiny confirmation chime (respects the local mute + sound pref) ──
  function chime() {
    if (muted) return;
    try {
      var C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      var a = new C();
      [523.25, 783.99].forEach(function (f, i) {
        var o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        var t = a.currentTime + i * 0.09;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.12, t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.5);
        o.connect(g); g.connect(a.destination); o.start(t); o.stop(t + 0.55);
      });
      setTimeout(function () { try { a.close(); } catch (e) {} }, 1100);
    } catch (e) {}
  }

  // ── Ambient soundscape (aged clockwork hall) — matches the AI Lab / Observatory
  //    pattern: a persistent context whose master gain reflects the global sound
  //    pref, a soft low drone, and a faint clock tick. Started on the first user
  //    gesture (browsers block autoplay). Silent while muted. ──
  var _actx = null, _master = null, _amStarted = false, _tickTimer = null;
  function _ac() {
    try {
      if (!_actx) {
        var C = window.AudioContext || window.webkitAudioContext; if (!C) return null;
        _actx = new C();
        _master = _actx.createGain(); _master.gain.value = muted ? 0 : 1; _master.connect(_actx.destination);
      }
      if (_actx.state === "suspended") _actx.resume();
      return _actx;
    } catch (e) { return null; }
  }
  function startAmbient() {
    var a = _ac(); if (!a || _amStarted) return; _amStarted = true;
    try {
      // Warm, very low "aged hall" drone (two detuned sines), quiet background.
      [55, 82.4].forEach(function (f, i) {
        var o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        g.gain.value = i === 0 ? 0.03 : 0.02;
        o.connect(g); g.connect(_master); o.start();
      });
      scheduleTick(a);   // faint clock tick motif
    } catch (e) {}
  }
  // A soft filtered click every ~2s — subtle, not foreground. Keeps its timer
  // running even when muted (it simply produces no sound), so it resumes cleanly.
  function scheduleTick(a) {
    _tickTimer = setTimeout(function () { scheduleTick(a); }, 2000);
    if (muted) return;
    try {
      var o = a.createOscillator(), g = a.createGain(), lp = a.createBiquadFilter();
      lp.type = "lowpass"; lp.frequency.value = 2000;
      o.type = "square"; o.frequency.value = 1500;
      var t = a.currentTime;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.02, t + 0.004);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
      o.connect(lp); lp.connect(g); g.connect(_master); o.start(t); o.stop(t + 0.06);
    } catch (e) {}
  }
  // First user gesture kicks the ambient (autoplay-safe).
  var _kicked = false;
  function _kick() { if (_kicked) return; _kicked = true; _ac(); if (!muted) startAmbient(); }
  ["pointerdown", "keydown"].forEach(function (ev) { document.addEventListener(ev, _kick, { once: true }); });

  // ── Rail fill + traveller reflect the number of lit eras ──
  function pctFor(i) { return TOTAL > 1 ? (i / (TOTAL - 1)) * 100 : 0; }
  function paint() {
    if (countEl) countEl.textContent = lit;
    if (progFill) progFill.style.width = (TOTAL ? (lit / TOTAL) * 100 : 0) + "%";
    // Backdrop shifts warm→cooler as the traveller moves forward in time.
    root.style.setProperty("--era-progress", TOTAL ? (lit / TOTAL).toFixed(3) : 0);
    // rail fills up to the last lit node (or the ready node's position)
    var reach = lit >= TOTAL ? 100 : pctFor(lit);
    if (railFill) railFill.style.width = reach + "%";
    if (traveller) traveller.style.left = (lit >= TOTAL ? 100 : pctFor(lit)) + "%";
    nodes.forEach(function (n, i) {
      n.classList.remove("lit", "ready", "locked");
      // A completed era stays clickable for read-only review (see the node click
      // handler + showPanel's i < lit "recorded" state); the title makes that
      // re-read affordance discoverable.
      if (i < lit) { n.classList.add("lit"); n.title = "Re-read this era"; }
      else if (i === lit) { n.classList.add("ready"); n.title = "Study this era"; }
      else { n.classList.add("locked"); n.title = "Locked, complete the earlier eras first"; }
    });
    if (hintEl) hintEl.style.opacity = lit > 0 ? "0" : "";   // only shown before the first era
  }

  // ── Persist a lit era (per user) so the timeline survives navigation ──
  function persist(i) {
    try {
      fetch("/location/" + encodeURIComponent(location) + "/progress", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item: "beat-" + i }), keepalive: true,
      });
    } catch (e) {}
  }

  function unlockTrial() {
    if (trialGate) trialGate.hidden = true;
    if (trialReady) trialReady.hidden = false;
  }

  // ── Read-aloud button for the open era (taught text only) ──
  var readBtn = null;
  if (window.AtlasVoice && window.AtlasVoice.supported && readSlot) {
    readBtn = window.AtlasVoice.button(root.style.getPropertyValue("--accent") || "#c1824a");
    readSlot.appendChild(readBtn);
  }

  function openPanel(i) {
    var beat = BEATS[i];
    if (!beat) return;
    activeIndex = i;
    checkPassed = i < lit;   // already-lit eras open in a "recorded" review state

    // Guess-first hook before a fresh era (never logged/graded), shown once.
    var hook = HOOKS[i];
    if (hook && !hooksShown[i] && i === lit && window.AtlasHook) {
      hooksShown[i] = true;
      var host = document.createElement("div");
      host.className = "lh-hook-host tl-hook-host";
      root.appendChild(host);
      window.AtlasHook.mount(host, hook, {
        accent: root.style.getPropertyValue("--accent") || "#c1824a",
        onContinue: function () { if (host.parentNode) host.parentNode.removeChild(host); showPanel(i); },
      });
      return;
    }
    showPanel(i);
  }

  var hideTimer = null;

  function showPanel(i) {
    var beat = BEATS[i];
    if (window.AtlasVoice) window.AtlasVoice.stop();   // never carry a previous page's read-aloud in
    if (eraEl) eraEl.textContent = beat.era || "";
    if (panelTitle) panelTitle.textContent = beat.title || "";
    if (textEl) textEl.textContent = beat.text || "";
    if (stamp) stamp.hidden = !(i < lit);
    // reset to the reading page
    if (pageRead) pageRead.hidden = false;
    if (pageCheck) pageCheck.hidden = true;
    if (checkFb) { checkFb.hidden = true; checkFb.textContent = ""; }
    if (closeBtn) closeBtn.hidden = !(i < lit);   // review eras can close immediately
    if (toCheckBtn) toCheckBtn.style.display = (i < lit) ? "none" : "";
    if (readBtn) {
      readBtn.onclick = function () {
        if (muted && window.AtlasVoice) { window.AtlasVoice.stop(); return; }
        window.AtlasVoice.toggle(beat.text || "", root.style.getPropertyValue("--accent") || "#c1824a", readBtn);
      };
    }
    clearTimeout(hideTimer);   // cancel a pending close so reopening always sticks
    panel.hidden = false;
    requestAnimationFrame(function () { panel.classList.add("show"); });
  }

  function toCheck() {
    var beat = BEATS[activeIndex]; if (!beat || !beat.check) return;
    if (window.AtlasVoice) window.AtlasVoice.stop();   // leaving the passage — stop read-aloud
    if (pageRead) pageRead.hidden = true;
    if (pageCheck) pageCheck.hidden = false;
    if (backBtn) backBtn.hidden = false;
    if (checkPassed) return;   // returning to an already-passed check — keep its recorded state
    if (checkQ) checkQ.textContent = beat.check.q || "";
    if (checkFb) { checkFb.hidden = true; checkFb.textContent = ""; }
    if (checkOpts) {
      checkOpts.innerHTML = "";
      shuffled((beat.check.options || []).map(function (opt, k) { return { opt: opt, k: k }; }))
        .forEach(function (o, d) {
          var b = document.createElement("button");
          b.type = "button"; b.className = "tl-check-opt";
          b.innerHTML = '<span class="tl-check-letter">' + String.fromCharCode(65 + d) + "</span><span>" + o.opt + "</span>";
          b.addEventListener("click", function () { answer(o.k, b); });
          checkOpts.appendChild(b);
        });
    }
  }

  // Fisher-Yates: a fresh, unseeded, uncached random order on every call, so the
  // correct option's on-screen position is never predictable across renders. The
  // ORIGINAL index is passed to answer(), so grading is unaffected.
  function shuffled(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  // Back from the quick-check to the passage — read-only page flip, no reset.
  function backToRead() {
    if (pageCheck) pageCheck.hidden = true;
    if (pageRead) pageRead.hidden = false;
  }

  function answer(k, btn) {
    var beat = BEATS[activeIndex]; if (!beat || !beat.check) return;
    if (checkPassed) return;
    if (k === beat.check.correct) {
      checkPassed = true;
      btn.classList.add("correct");
      var lt = btn.querySelector(".tl-check-letter"); if (lt) lt.textContent = "✓";
      checkOpts.querySelectorAll(".tl-check-opt").forEach(function (o) { o.disabled = true; });
      if (checkFb) { checkFb.hidden = false; checkFb.className = "tl-check-fb ok"; checkFb.textContent = "✓ Recorded. This era is now part of your Chronicle."; }
      lightEra(activeIndex);
      if (closeBtn) closeBtn.hidden = false;
    } else {
      btn.classList.add("wrong");
      if (checkFb) { checkFb.hidden = false; checkFb.className = "tl-check-fb bad"; checkFb.textContent = "Not quite. Revisit the passage above and try again."; }
      setTimeout(function () { btn.classList.remove("wrong"); }, 600);
    }
  }

  function lightEra(i) {
    if (i !== lit) return;   // eras light strictly in order
    lit = i + 1;
    persist(i);
    chime();
    if (stamp) stamp.hidden = false;
    paint();
    if (lit >= TOTAL) setTimeout(unlockTrial, 400);
  }

  function closePanel() {
    if (!checkPassed) return;   // must pass this era's check before leaving
    if (window.AtlasVoice) window.AtlasVoice.stop();
    panel.classList.remove("show");
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function () { panel.hidden = true; }, 260);
    activeIndex = -1;
  }

  // ── Wiring ──
  nodes.forEach(function (n) {
    n.addEventListener("click", function () {
      var i = parseInt(n.dataset.index, 10);
      if (i > lit) return;         // locked — future eras aren't clickable yet
      openPanel(i);
    });
  });
  if (toCheckBtn) toCheckBtn.addEventListener("click", toCheck);
  if (backBtn) backBtn.addEventListener("click", backToRead);
  panel.querySelectorAll("[data-panel-close]").forEach(function (el) { el.addEventListener("click", closePanel); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden && checkPassed) closePanel(); });

  // ── Local mute toggle (gates the timeline's chime; read-aloud follows the
  //    global voice pref independently) ──
  var muteBtn = document.getElementById("tl-mute");
  function syncMute() { if (muteBtn) { muteBtn.textContent = muted ? "🔇" : "🔊"; muteBtn.classList.toggle("muted", muted); } }
  if (muteBtn) { syncMute(); muteBtn.addEventListener("click", function () {
    _kick();
    muted = !muted;
    try { if (_master) _master.gain.value = muted ? 0 : 1; } catch (e) {}
    if (!muted) startAmbient();   // (idempotent) ensure the ambient is running
    if (muted && window.AtlasVoice) window.AtlasVoice.stop();
    syncMute();
  }); }

  // ── Silent restore: re-light already-completed eras (per user), draw the
  //    rail forward and set ERA x/N — no replay, exactly like the Library. ──
  (function restore() {
    var ids = json("timeline-explored");
    var n = 0;
    for (var i = 0; i < TOTAL; i++) { if (ids.indexOf("beat-" + i) !== -1) n++; }
    lit = Math.min(n, TOTAL);
    for (var h = 0; h < lit; h++) hooksShown[h] = true;   // don't replay a done era's hook
    paint();
    if (lit >= TOTAL) unlockTrial();
  })();
})();
