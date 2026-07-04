// ════════════════════════════════════════════════════════════════
//  The living map — state-reactive presentation layer for the hub.
//  * one-time reveals when newly earned: golden path draw on pass,
//    Final Ascent pin ignition — each tracked via server-session
//    "seen" flags (POST /seen), never localStorage.
//  * sparse accent particles over COMPLETED zones.
//  All state comes from #hub-state — no writes to progress or research
//  data, no effect on unlocking or scoring.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  var stage = document.querySelector(".map-stage");
  if (!stage) return;

  var state = {};
  try { state = JSON.parse(document.getElementById("hub-state").textContent) || {}; } catch (e) {}
  var seen = state.seen || {};

  var P = window.AtlasPrefs;
  function reduce() { return P ? !!P.effective("reduce_motion") : false; }
  function soundOn() { return P ? P.soundOn() : true; }

  // ── position glow layers (kept out of inline styles, like the pins) ──
  stage.querySelectorAll(".zone-glow[data-x]").forEach(function (el) {
    el.style.left = el.dataset.x + "%";
    el.style.top = el.dataset.y + "%";
    if (el.dataset.accent) el.style.setProperty("--zone-accent", el.dataset.accent);
  });

  // ── soft reveal chime (visual events only; respects the sound pref) ──
  function chime(freqs) {
    if (!soundOn() || reduce()) return;
    try {
      var C = window.AudioContext || window.webkitAudioContext;
      if (!C) return;
      var a = new C();
      (freqs || [523.25, 783.99]).forEach(function (f, i) {
        var o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        var t = a.currentTime + i * 0.09;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.09, t + 0.03);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.55);
        o.connect(g); g.connect(a.destination);
        o.start(t); o.stop(t + 0.6);
      });
      setTimeout(function () { try { a.close(); } catch (e) {} }, 1200);
    } catch (e) {}
  }

  // ── build the one-time reveal queue (newly earned, not yet seen) ──
  var reveals = [];
  var newlySeen = [];

  // Golden path draws — passed segments not yet seen animate in; seen ones are static
  stage.querySelectorAll(".path-gold").forEach(function (line) {
    var flag = "path_" + line.dataset.path;
    if (seen[flag]) { line.classList.add("drawn-static"); return; }
    reveals.push({ flag: flag, ms: 1400, run: function () {
      line.classList.add("drawn");
      chime([659.25, 987.77]);
    }});
  });

  // Final Ascent pin ignition — once, when it first appears unlocked
  var portal = stage.querySelector(".map-pin.portal");
  if (portal && state.final && state.final.unlocked && !seen.ignite_final) {
    reveals.push({ flag: "ignite_final", ms: 2300, run: function () {
      portal.classList.add("ignite");
      chime([523.25, 783.99, 1046.5]);
      setTimeout(function () { portal.classList.remove("ignite"); }, 2400);
    }});
  }

  function saveSeen() {
    if (!newlySeen.length) return;
    try {
      fetch("/seen", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ flags: newlySeen }),
        keepalive: true,
      });
    } catch (e) {}
  }

  function playReveals() {
    if (!reveals.length) return;
    if (reduce()) {
      reveals.forEach(function (r) { r.run(); newlySeen.push(r.flag); });
      saveSeen();
      return;
    }
    var i = 0;
    (function next() {
      if (i >= reveals.length) { saveSeen(); return; }
      var r = reveals[i++];
      r.run();
      newlySeen.push(r.flag);
      setTimeout(next, r.ms);
    })();
  }

  // Wait for the opening cinematic (if it's about to play) before revealing.
  if (window.ATLAS_CINEMATIC_PENDING) {
    document.addEventListener("atlas:cinematic-done", function () {
      setTimeout(playReveals, 450);
    }, { once: true });
  } else {
    setTimeout(playReveals, 600);
  }

  // ══════════ Sparse accent particles over completed zones ══════════
  var glows = Array.prototype.slice.call(stage.querySelectorAll(".zone-glow"));
  var canvas = document.getElementById("map-live");
  if (!canvas || !glows.length || reduce()) return;

  var ctx = canvas.getContext("2d");
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var W = 0, H = 0, parts = [];
  var PER_ZONE = 6; // deliberately sparse — performance first

  function size() {
    W = stage.clientWidth; H = stage.clientHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function spawn(zone) {
    return {
      cx: zone.x, cy: zone.y, color: zone.color,
      ox: (Math.random() - 0.5) * 0.18,      // offset as fraction of stage width
      oy: (Math.random() - 0.5) * 0.24,      // fraction of stage height
      r: 0.8 + Math.random() * 1.3,
      vy: 0.05 + Math.random() * 0.08,       // slow upward drift (px/frame @30fps)
      a: 0, fade: 0.004 + Math.random() * 0.006,
      life: 0, max: 240 + Math.random() * 240,
    };
  }

  var zones = glows.map(function (g) {
    return { x: parseFloat(g.dataset.x) / 100, y: parseFloat(g.dataset.y) / 100, color: g.dataset.accent || "#e8c97a" };
  });
  zones.forEach(function (z) { for (var i = 0; i < PER_ZONE; i++) parts.push(spawn(z)); });

  var last = 0, running = true;
  function frame(ts) {
    if (!running) return;
    requestAnimationFrame(frame);
    if (ts - last < 33) return; // ~30fps cap
    last = ts;
    ctx.clearRect(0, 0, W, H);
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      p.life++;
      p.oy -= p.vy / H;
      p.a = Math.min(0.55, p.a + p.fade) * (1 - p.life / p.max);
      if (p.life >= p.max) { parts[i] = spawn({ x: p.cx, y: p.cy, color: p.color }); continue; }
      var x = (p.cx + p.ox) * W, y = (p.cy + p.oy) * H;
      ctx.globalAlpha = Math.max(0, p.a);
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(x, y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) { running = false; }
    else if (!running) { running = true; requestAnimationFrame(frame); }
  });
  window.addEventListener("resize", size);

  size();
  requestAnimationFrame(frame);
})();
