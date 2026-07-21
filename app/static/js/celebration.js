// Location Complete celebration — gold particles + a short synthesized fanfare.
(function () {
  const cel = document.getElementById("celebration");
  if (!cel) return;

  // ── Gold particles ──
  const wrap = document.getElementById("celebration-particles");
  if (wrap) {
    for (let i = 0; i < 54; i++) {
      const p = document.createElement("span");
      p.className = "gold-particle";
      p.style.left = Math.random() * 100 + "%";
      p.style.animationDelay = Math.random() * 0.7 + "s";
      p.style.animationDuration = 1.6 + Math.random() * 1.7 + "s";
      const w = 6 + Math.random() * 9;
      p.style.width = w + "px";
      p.style.height = w * (0.5 + Math.random()) + "px";
      wrap.appendChild(p);
    }
  }

  // ── Short triumphant fanfare via Web Audio (best-effort; no asset).
  //    Respects the master sound preference (same guard as achievements.js). ──
  try {
    const soundOff = window.ATLAS_PREFS && window.ATLAS_PREFS.sound === false;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx && !soundOff) {
      const ac = new Ctx();
      const start = function () {
        const now = ac.currentTime;
        [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => {
          const o = ac.createOscillator();
          const g = ac.createGain();
          o.type = "triangle";
          o.frequency.value = f;
          o.connect(g);
          g.connect(ac.destination);
          const t = now + i * 0.13;
          g.gain.setValueAtTime(0, t);
          g.gain.linearRampToValueAtTime(0.25, t + 0.03);
          g.gain.exponentialRampToValueAtTime(0.001, t + 0.55);
          o.start(t);
          o.stop(t + 0.6);
        });
      };
      if (ac.state === "suspended") ac.resume().then(start).catch(start);
      else start();
    }
  } catch (e) {
    /* sound is best-effort */
  }

  // ── "Review my answers" ⇄ "Back to summary" toggle ──
  // Review is a TOGGLE, not a one-way dismiss: while a reflection is pending its
  // exits are hidden, so "Back to summary" must always be able to bring the
  // reflect card back (never a dead end, never a bypass to an ungated exit).
  let hideTimer = null;
  function showBreakdown() {
    cel.classList.add("dismissed");
    hideTimer = setTimeout(() => { cel.style.display = "none"; }, 400);
  }
  function showSummary() {
    if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    cel.style.display = "";
    cel.classList.remove("dismissed");
    try { window.scrollTo({ top: 0, behavior: "auto" }); } catch (e) { window.scrollTo(0, 0); }
  }

  const review = document.getElementById("celebration-review");
  if (review) review.addEventListener("click", showBreakdown);

  ["topbar-back-summary", "back-summary-btn"].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", showSummary);
  });
})();
