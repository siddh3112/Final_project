// ════════════════════════════════════════════════════════════════
//  Opening cinematic — first hub visit (session), always skippable.
//  Glyph draws itself in gold, 3 lines type in, "Begin your Quest".
//  Presentation only: tracks "seen" via the server session (/seen),
//  never localStorage, never research data. Respects sound + motion
//  prefs (reduce_motion → single static intro card instead).
//  MUST load before hub-onboard.js (sets ATLAS_CINEMATIC_PENDING so
//  the How-to-Play tutorial defers until the cinematic closes).
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  var overlay = document.getElementById("hub-cinematic");
  if (!overlay) return;

  var P = window.AtlasPrefs;
  function reduce() { return P ? !!P.effective("reduce_motion") : false; }
  function soundOn() { return P ? P.soundOn() : true; }

  var lines = [];
  try { lines = JSON.parse(document.getElementById("cine-lines-data").textContent) || []; } catch (e) {}

  var linesEl = document.getElementById("cine-lines");
  var beginBtn = document.getElementById("cine-begin");
  var skipBtn = document.getElementById("cine-skip");
  var mapScreen = document.querySelector(".map-screen");

  var playing = false, closed = false, timers = [], audioCtx = null;

  function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
  function clearTimers() { timers.forEach(clearTimeout); timers = []; }

  // ── Soft synth swell: two slow sine pads fading in and out ──
  function swell() {
    if (!soundOn() || reduce()) return;
    try {
      var C = window.AudioContext || window.webkitAudioContext;
      if (!C) return;
      audioCtx = new C();
      var t = audioCtx.currentTime;
      [110, 164.81, 220].forEach(function (f, i) {
        var o = audioCtx.createOscillator(), g = audioCtx.createGain();
        o.type = "sine"; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.028 - i * 0.006, t + 2.5);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 9);
        o.connect(g); g.connect(audioCtx.destination);
        o.start(t + i * 0.4); o.stop(t + 9.5);
      });
    } catch (e) {}
  }
  function stopSwell() {
    if (!audioCtx) return;
    try { audioCtx.close(); } catch (e) {}
    audioCtx = null;
  }

  function addLine() {
    var p = document.createElement("p");
    p.className = "cine-line";
    linesEl.appendChild(p);
    return p;
  }

  function typeLine(el, str, cb) {
    var n = 0;
    (function tick() {
      n++;
      el.textContent = str.slice(0, n);
      if (n < str.length) timers.push(setTimeout(tick, 26));
      else if (cb) later(cb, 650);
    })();
  }

  function runLines(i) {
    if (closed) return;
    if (i >= lines.length) { beginBtn.hidden = false; beginBtn.classList.add("cine-in"); return; }
    var el = addLine();
    el.classList.add("cine-in");
    typeLine(el, lines[i], function () { runLines(i + 1); });
  }

  function show() {
    if (playing) return;
    playing = true; closed = false;
    window.ATLAS_CINEMATIC_PENDING = true;
    linesEl.innerHTML = "";
    beginBtn.hidden = true;
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    if (mapScreen) mapScreen.classList.add("cine-dim");

    if (reduce()) {
      // Static intro card: all text at once, Begin immediately. No audio/animation.
      overlay.classList.add("cine-open", "cine-static");
      lines.forEach(function (l) { addLine().textContent = l; });
      beginBtn.hidden = false;
      return;
    }

    requestAnimationFrame(function () { overlay.classList.add("cine-open"); });
    swell();
    later(function () { runLines(0); }, 2100); // after the glyph has mostly drawn
  }

  function close() {
    if (closed) return;
    closed = true;
    clearTimers();
    stopSwell();
    overlay.classList.add("cine-closing");
    if (mapScreen) mapScreen.classList.remove("cine-dim");
    document.body.style.overflow = "";
    setTimeout(function () {
      overlay.hidden = true;
      overlay.classList.remove("cine-open", "cine-static", "cine-closing");
      playing = false;
      window.ATLAS_CINEMATIC_PENDING = false;
      document.dispatchEvent(new Event("atlas:cinematic-done"));
    }, reduce() ? 30 : 650);
  }

  skipBtn.addEventListener("click", close);
  beginBtn.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && playing && !closed) close();
  });

  // Settings panel "Replay intro"
  window.AtlasCinematic = { play: show };

  // Auto-play on first visit this session. Set the pending flag SYNCHRONOUSLY
  // so hub-onboard.js (loaded after this file) defers its tutorial.
  if (overlay.getAttribute("data-seen") !== "1") {
    window.ATLAS_CINEMATIC_PENDING = true;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", show);
    } else {
      show();
    }
  }
})();
