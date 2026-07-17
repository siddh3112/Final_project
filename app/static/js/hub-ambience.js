// ════════════════════════════════════════════════════════════════
//  Hub ambience — a soft welcoming pad for the world-map (main page).
//  Web Audio API only (no files). Matches the game's audio pattern: it
//  inherits the GLOBAL sound preference and starts on the first user
//  gesture (browsers block autoplay). Because the Settings panel lives on
//  the hub, it also responds LIVE when the user toggles "Master sound".
//  Presentation only — never touches scoring or research data.
// ════════════════════════════════════════════════════════════════
(function () {
  // World-map / hub only.
  if (!document.querySelector(".map-screen")) return;

  // Inherit the global "Master sound" preference (settings toggle) — the same
  // mechanism every location page uses. Start silent if sound is off.
  var muted = !!(window.ATLAS_PREFS && window.ATLAS_PREFS.sound === false);
  var AC = window.AudioContext || window.webkitAudioContext;
  var ctx = null, master = null, primed = false, padStarted = false;

  function ac() {
    try {
      if (!ctx && AC) {
        ctx = new AC();
        master = ctx.createGain();
        master.gain.value = muted ? 0 : 1;
        master.connect(ctx.destination);
      }
      if (ctx && ctx.state === "suspended") ctx.resume();
    } catch (e) { ctx = null; }
    return ctx;
  }

  // A soft, warm low chord that fades in gently and "breathes" — a quiet
  // welcome for the map, not a fanfare. No-op while muted.
  function startPad() {
    var a = ac();
    if (!a || padStarted || muted) return;
    padStarted = true;
    try {
      var now = a.currentTime;
      var pad = a.createGain();
      pad.gain.setValueAtTime(0.0001, now);
      pad.gain.exponentialRampToValueAtTime(0.05, now + 2.5); // slow, quiet fade-in
      pad.connect(master);
      // low root + fifth + octave (G2 / D3 / G3)
      [98.0, 146.83, 196.0].forEach(function (f) {
        var o = a.createOscillator();
        o.type = "sine";
        o.frequency.value = f;
        o.connect(pad);
        o.start();
      });
      // slow amplitude "breathing" on the pad only (never on master).
      var lfo = a.createOscillator(), lfoG = a.createGain();
      lfo.type = "sine";
      lfo.frequency.value = 0.08;
      lfoG.gain.value = 0.015;
      lfo.connect(lfoG); lfoG.connect(pad.gain);
      lfo.start();
    } catch (e) {}
  }

  // Browsers block audio until the first user gesture; prime + play then.
  function kick() {
    if (primed) return;
    primed = true;
    ac();
    startPad(); // no-ops if muted
  }
  ["pointerdown", "keydown"].forEach(function (ev) {
    document.addEventListener(ev, kick, { once: true });
  });

  // The Settings "Master sound" toggle is on this page — respond live.
  document.addEventListener("atlas:prefchange", function (e) {
    if (!e || !e.detail || e.detail.key !== "sound") return;
    muted = e.detail.value === false;
    try { if (master) master.gain.value = muted ? 0 : 1; } catch (err) {}
    if (!muted) { ac(); startPad(); } // start it now that sound is on
  });
})();
