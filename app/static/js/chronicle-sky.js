// ════════════════════════════════════════════════════════════════
//  The Chronicle — aged-archive backdrop.
//  A warm, low-CPU field of drifting dust motes and slow "paper" flecks
//  over a sepia hall of records. Deliberately NOT a star sky (no twinkle,
//  no constellation) — warm tones, gentle upward/lateral drift, so the
//  scene reads as an old archive rather than the Observatory.
//  Respects prefers-reduced-motion (static) and pauses when hidden.
//  Presentation only — no scoring/flow/logging.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var canvas = document.getElementById("tl-sky");
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");

  var P = window.AtlasPrefs;
  var REDUCE = !!((P && P.effective && P.effective("reduce_motion")) ||
    (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches));

  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var W = 0, H = 0, motes = [], flecks = [], running = true, last = 0;

  // Warm archive palette (dust = pale gold; flecks = aged parchment)
  var DUST = ["rgba(224,196,140,", "rgba(200,168,120,", "rgba(240,214,164,"];
  var FLECK = ["rgba(196,160,104,", "rgba(168,132,80,", "rgba(214,186,140,"];

  function build() {
    motes = []; flecks = [];
    var dn = Math.round((W * H) / 26000);   // density scales with area
    dn = Math.max(24, Math.min(dn, 90));
    for (var i = 0; i < dn; i++) {
      motes.push({
        x: Math.random() * W, y: Math.random() * H,
        r: Math.random() * 1.6 + 0.4,
        vx: (Math.random() - 0.5) * 0.12,
        vy: -(Math.random() * 0.16 + 0.04),   // drift gently upward, like warm air
        ph: Math.random() * 6.28,
        c: DUST[(Math.random() * DUST.length) | 0],
      });
    }
    for (var j = 0; j < Math.max(5, (dn / 6) | 0); j++) {
      flecks.push({
        x: Math.random() * W, y: Math.random() * H,
        w: Math.random() * 4 + 2, h: Math.random() * 2 + 1,
        vx: (Math.random() - 0.5) * 0.22, vy: -(Math.random() * 0.1 + 0.03),
        rot: Math.random() * 6.28, vr: (Math.random() - 0.5) * 0.01,
        c: FLECK[(Math.random() * FLECK.length) | 0],
      });
    }
  }

  function size() {
    var host = canvas.parentElement || canvas;
    W = host.clientWidth || window.innerWidth;
    H = host.clientHeight || window.innerHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    build();
  }

  function wrap(p) {
    if (p.y < -6) { p.y = H + 6; p.x = Math.random() * W; }
    if (p.x < -6) p.x = W + 6; else if (p.x > W + 6) p.x = -6;
  }

  function draw(now) {
    ctx.clearRect(0, 0, W, H);
    // dust motes
    for (var i = 0; i < motes.length; i++) {
      var m = motes[i];
      if (!REDUCE) { m.x += m.vx; m.y += m.vy; wrap(m); }
      var tw = REDUCE ? 0.5 : (0.4 + 0.35 * Math.sin(now / 1400 + m.ph));
      ctx.fillStyle = m.c + (0.10 + 0.28 * tw) + ")";
      ctx.beginPath(); ctx.arc(m.x, m.y, m.r, 0, 6.2832); ctx.fill();
    }
    // paper flecks (small rotated rectangles)
    for (var k = 0; k < flecks.length; k++) {
      var f = flecks[k];
      if (!REDUCE) { f.x += f.vx; f.y += f.vy; f.rot += f.vr; wrap(f); }
      ctx.save();
      ctx.translate(f.x, f.y); ctx.rotate(f.rot);
      ctx.fillStyle = f.c + "0.18)";
      ctx.fillRect(-f.w / 2, -f.h / 2, f.w, f.h);
      ctx.restore();
    }
  }

  function frame(now) {
    if (!running) return;
    requestAnimationFrame(frame);
    if (now - last < 40) return;   // ~25fps cap (dust is slow; keep it cheap)
    last = now;
    draw(now);
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) running = false;
    else if (!running && !REDUCE) { running = true; requestAnimationFrame(frame); }
  });
  window.addEventListener("resize", function () { size(); if (REDUCE) draw(performance.now()); });

  size();
  if (REDUCE) draw(performance.now());
  else requestAnimationFrame(frame);
})();
