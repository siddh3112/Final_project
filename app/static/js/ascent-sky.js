// ════════════════════════════════════════════════════════════════
//  Final Ascent — night-sky backdrop for the post-test question screen.
//  Low-CPU parallax starfield (gold + white), slow drift, an occasional
//  gold shooting star. Presentation only — no scoring/flow/logging.
//  Respects prefers-reduced-motion (static sky, no drift/shooting stars).
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var canvas = document.getElementById("ascent-sky");
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");

  var P = window.AtlasPrefs;
  var REDUCE = !!((P && P.effective && P.effective("reduce_motion")) ||
    (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches));

  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var W = 0, H = 0, layers = [], shooting = null, nextShoot = 0, running = true, last = 0;

  function build() {
    layers = [];
    // [count, drift px/frame, max radius, colour]
    [[70, 0.02, 0.5, "#ece8ff"], [42, 0.05, 0.9, "#f0c96b"], [26, 0.09, 1.3, "#ffffff"]]
      .forEach(function (d) {
        var stars = [];
        for (var i = 0; i < d[0]; i++) {
          stars.push({ x: Math.random() * W, y: Math.random() * H * 0.86, r: Math.random() * d[2] + 0.3, ph: Math.random() * 6.28 });
        }
        layers.push({ stars: stars, speed: d[1], color: d[3] });
      });
    nextShoot = performance.now() + 8000 + Math.random() * 14000;
  }

  function size() {
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    build();
  }

  function draw(now) {
    ctx.clearRect(0, 0, W, H);
    for (var l = 0; l < layers.length; l++) {
      var L = layers[l];
      ctx.fillStyle = L.color;
      for (var i = 0; i < L.stars.length; i++) {
        var s = L.stars[i];
        if (!REDUCE) { s.x -= L.speed; if (s.x < -2) { s.x = W + 2; s.y = Math.random() * H * 0.86; } }
        var tw = REDUCE ? 0.8 : (0.5 + 0.5 * Math.sin(now / 900 * (0.5 + l * 0.3) + s.ph));
        ctx.globalAlpha = 0.32 + 0.5 * tw;
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.2832); ctx.fill();
      }
    }
    ctx.globalAlpha = 1;

    if (!REDUCE) {
      if (!shooting && now > nextShoot) shooting = { x: W * (0.15 + Math.random() * 0.5), y: H * 0.08 + Math.random() * H * 0.22, t0: now };
      if (shooting) {
        var p = (now - shooting.t0) / 900;
        if (p >= 1) { shooting = null; nextShoot = now + 16000 + Math.random() * 12000; }
        else {
          var hx = shooting.x + p * 260, hy = shooting.y + p * 150;
          var g = ctx.createLinearGradient(hx, hy, hx - 92, hy - 53);
          g.addColorStop(0, "rgba(240,201,107," + (0.9 * (1 - p)) + ")");
          g.addColorStop(1, "rgba(240,201,107,0)");
          ctx.strokeStyle = g; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(hx - 92, hy - 53); ctx.stroke();
        }
      }
    }
  }

  function frame(now) {
    if (!running) return;
    requestAnimationFrame(frame);
    if (now - last < 33) return;   // ~30fps cap
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
