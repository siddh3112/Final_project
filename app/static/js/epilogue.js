// ════════════════════════════════════════════════════════════════
//  Closing cinematic (epilogue) — mirrors the opening, resolves it.
//  Restored realms + Atlas glyph drawing in gold + resolving lines +
//  a triumphant swell, ending on "Claim your Certificate" / "Return to
//  Map". Plays ONCE per session after the results reveal (tracked via
//  the server "seen" flag), replayable on demand. Presentation only —
//  never touches scoring or progress. Respects sound + motion prefs.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  var overlay = document.getElementById("epilogue");
  if (!overlay) return;

  var P = window.AtlasPrefs;
  function reduce() { return P ? !!P.effective("reduce_motion") : false; }
  function soundOn() { return P ? P.soundOn() : true; }

  var lines = [];
  try { lines = JSON.parse(document.getElementById("epi-lines-data").textContent) || []; } catch (e) {}

  var linesEl = document.getElementById("epi-lines");
  var cta = document.getElementById("epi-cta");
  var skipBtn = document.getElementById("epi-skip");
  var standalone = overlay.getAttribute("data-standalone") === "1";

  var playing = false, ended = false, timers = [], audioCtx = null;
  function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
  function clearTimers() { timers.forEach(clearTimeout); timers = []; }

  // ── Triumphant swell: a rising major chord (gold, resolving) ──
  function swell() {
    if (!soundOn() || reduce()) return;
    try {
      var C = window.AudioContext || window.webkitAudioContext;
      if (!C) return;
      audioCtx = new C();
      var t = audioCtx.currentTime;
      [146.83, 220, 293.66, 440].forEach(function (f, i) {   // D major, ascending
        var o = audioCtx.createOscillator(), g = audioCtx.createGain();
        o.type = "sine"; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.03 - i * 0.004, t + 2.2);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 8);
        o.connect(g); g.connect(audioCtx.destination);
        o.start(t + i * 0.35); o.stop(t + 8.5);
      });
    } catch (e) {}
  }
  function stopSwell() { if (!audioCtx) return; try { audioCtx.close(); } catch (e) {} audioCtx = null; }

  function addLine() { var p = document.createElement("p"); p.className = "epi-line"; linesEl.appendChild(p); return p; }
  function typeLine(el, str, cb) {
    var n = 0;
    (function tick() {
      n++;
      el.textContent = str.slice(0, n);
      if (n < str.length) timers.push(setTimeout(tick, 26));
      else if (cb) later(cb, 700);
    })();
  }
  function showCTA() { cta.hidden = false; cta.classList.add("epi-in"); }

  function runLines(i) {
    if (ended) return;
    if (i >= lines.length) { showCTA(); return; }
    var el = addLine(); el.classList.add("epi-in");
    typeLine(el, lines[i], function () { runLines(i + 1); });
  }

  function markSeen() {
    try {
      fetch("/seen", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ flags: ["epilogue"] }), keepalive: true,
      });
    } catch (e) {}
  }

  function play() {
    if (playing) return;
    playing = true; ended = false;
    linesEl.innerHTML = ""; cta.hidden = true; cta.classList.remove("epi-in");
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    markSeen();

    if (reduce()) {
      // Static card: restored map + all lines + CTA, no draw/type/audio.
      overlay.classList.add("epi-open", "epi-static");
      lines.forEach(function (l) { addLine().textContent = l; });
      showCTA();
      return;
    }
    overlay.classList.remove("epi-static");
    requestAnimationFrame(function () { overlay.classList.add("epi-open"); });
    swell();
    later(function () { runLines(0); }, 2400); // after the glyph + map have drawn
  }

  // Skip → jump straight to the end (all lines + CTA), keep the overlay so the
  // learner can claim their certificate immediately.
  function skipToEnd() {
    if (ended) return;
    ended = true; clearTimers(); stopSwell();
    linesEl.innerHTML = "";
    lines.forEach(function (l) { addLine().textContent = l; });
    overlay.classList.add("epi-open");
    showCTA();
  }

  skipBtn.addEventListener("click", skipToEnd);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && playing && !ended) skipToEnd();
  });

  // Replay control on the results page
  var replayBtn = document.getElementById("rv-replay-ending");
  if (replayBtn) replayBtn.addEventListener("click", function () {
    ended = false; playing = false;
    overlay.classList.remove("epi-open", "epi-static", "epi-closing");
    play();
  });

  window.AtlasEpilogue = { play: play };

  // ── Auto-play ──
  if (overlay.getAttribute("data-auto") === "1") {
    if (standalone) {
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", play);
      else play();
    } else {
      // Results page: play after the score/Sage/seal/review reveal finishes.
      document.addEventListener("ascent:reveal-done", function () { later(play, 2600); }, { once: true });
      // Fallback in case the reveal event never fires.
      later(function () { if (!playing) play(); }, 13000);
    }
  }
})();
