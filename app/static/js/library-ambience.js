// ════════════════════════════════════════════════════════════════
//  Library Ambience — atmospheric audio + visual FX for the Library.
//  Web Audio API only (no files). Exposes window.LibFX so bookshelf.js
//  can trigger sounds/effects at the right moments. Everything is
//  wrapped in try-catch so a missing API never breaks the page.
// ════════════════════════════════════════════════════════════════

// Keep the Library a single static (non-scrolling) scene: scale the
// shelf scene down to fit whatever vertical space is left under the hero.
(function () {
  if (!document.body.classList.contains("theme-archive")) return;
  function fit() {
    var stage = document.querySelector(".shelf-stage");
    if (!stage) return;
    stage.style.zoom = "1";
    var top = stage.getBoundingClientRect().top;
    var natural = stage.offsetHeight;
    var avail = window.innerHeight - top - 14;
    if (natural > 0 && avail > 0) {
      var z = Math.min(1, avail / natural);
      stage.style.zoom = z > 0.45 ? String(z) : "0.45";
    }
  }
  window.addEventListener("load", fit);
  window.addEventListener("resize", fit);
  setTimeout(fit, 60); setTimeout(fit, 400);
})();

(function () {
  // Library page only.
  if (!document.body.classList.contains("theme-archive")) return;

  var AC = window.AudioContext || window.webkitAudioContext;
  var ctx = null, master = null;
  // Inherit the GLOBAL "Master sound" preference (settings toggle) — the same
  // mechanism the AI Lab / Observatory use. Start muted if sound is off.
  var muted = !!(window.ATLAS_PREFS && window.ATLAS_PREFS.sound === false), started = false;
  var fireNode = null;

  function ensureCtx() {
    if (ctx || !AC) return ctx;
    try {
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = muted ? 0 : 1;
      master.connect(ctx.destination);
    } catch (e) { ctx = null; }
    return ctx;
  }
  function t0() { return ctx ? ctx.currentTime : 0; }
  function audible() { return ctx && !muted; }

  // Short generated impulse response → light room reverb.
  function impulse(seconds, decay) {
    var rate = ctx.sampleRate, len = Math.max(1, Math.floor(rate * seconds));
    var buf = ctx.createBuffer(2, len, rate);
    for (var c = 0; c < 2; c++) {
      var d = buf.getChannelData(c);
      for (var i = 0; i < len; i++) {
        d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay);
      }
    }
    return buf;
  }

  // ── Ambient crackling fire: brown noise → low-pass → very low gain ──
  function startFire() {
    if (!ctx || fireNode) return;
    try {
      var size = 4096;
      var node = ctx.createScriptProcessor(size, 1, 1);
      var last = 0;
      node.onaudioprocess = function (e) {
        var out = e.outputBuffer.getChannelData(0);
        for (var i = 0; i < size; i++) {
          var white = Math.random() * 2 - 1;
          last = (last + 0.02 * white) / 1.02;
          // occasional crackle pops
          var pop = Math.random() < 0.0008 ? (Math.random() * 2 - 1) * 0.5 : 0;
          out[i] = last * 3.2 + pop;
        }
      };
      var lp = ctx.createBiquadFilter();
      lp.type = "lowpass"; lp.frequency.value = 400;
      var g = ctx.createGain(); g.gain.value = 0.04;
      node.connect(lp); lp.connect(g); g.connect(master);
      fireNode = node;
    } catch (e) {}
  }

  // Paper noise: random amplitude "grains" give noise a crinkly, paper-like
  // texture instead of flat hiss. `crinkle` = how often grains re-trigger.
  function paperBuffer(dur, crinkle) {
    var len = Math.floor(ctx.sampleRate * dur);
    var buf = ctx.createBuffer(1, len, ctx.sampleRate);
    var d = buf.getChannelData(0);
    var amp = 0;
    for (var i = 0; i < len; i++) {
      if (Math.random() < crinkle) amp = 0.4 + Math.random() * 0.6;
      amp *= 0.9;                       // each grain decays quickly
      d[i] = (Math.random() * 2 - 1) * amp;
    }
    return buf;
  }

  // A swept band-pass "page swish": the rustle moving through the air.
  function paperSwish(dur, peak, f1, f2, f3, delay) {
    var now = t0() + (delay || 0);
    var src = ctx.createBufferSource();
    src.buffer = paperBuffer(dur, 0.06);
    var bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.Q.value = 0.6;
    bp.frequency.setValueAtTime(f1, now);
    bp.frequency.linearRampToValueAtTime(f2, now + dur * 0.4);
    bp.frequency.linearRampToValueAtTime(f3, now + dur);
    var hp = ctx.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 700;
    var g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, now);
    g.gain.linearRampToValueAtTime(peak, now + 0.05);
    g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    src.connect(bp); bp.connect(hp); hp.connect(g); g.connect(master);
    src.start(now); src.stop(now + dur + 0.02);
  }

  // ── Real book-open sound file: immediate playback on click. Falls back
  //    to the synth version below if the file can't load/play. Mute-aware. ──
  var bookOpenEl = null;
  try {
    bookOpenEl = new Audio("/static/sounds/book-open.mp3");
    bookOpenEl.preload = "auto";
    bookOpenEl.volume = 0.9;
  } catch (e) { bookOpenEl = null; }

  function bookPull() {
    if (muted) return;
    if (bookOpenEl) {
      try {
        bookOpenEl.currentTime = 0;
        var pr = bookOpenEl.play();
        if (pr && pr.catch) pr.catch(function () { bookPullSynth(); });
        return;
      } catch (e) {}
    }
    bookPullSynth();
  }

  // ── Synth book opening (fallback): cover "fwump" + pages spreading ──
  function bookPullSynth() {
    if (!audible()) return;
    try {
      var now = t0();
      // low cover thud (the binding opening)
      var tlen = Math.floor(ctx.sampleRate * 0.2);
      var tbuf = ctx.createBuffer(1, tlen, ctx.sampleRate);
      var td = tbuf.getChannelData(0);
      for (var i = 0; i < tlen; i++) td[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / tlen, 3);
      var tsrc = ctx.createBufferSource(); tsrc.buffer = tbuf;
      var lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 160;
      var tg = ctx.createGain(); tg.gain.value = 0.45;
      tsrc.connect(lp); lp.connect(tg); tg.connect(master);
      tsrc.start(now);
      // pages spreading open (fuller, longer rustle) + a little room reverb
      var conv = ctx.createConvolver(); conv.buffer = impulse(0.4, 2.8);
      var wet = ctx.createGain(); wet.gain.value = 0.18;
      conv.connect(wet); wet.connect(master);
      var swSrc = ctx.createBufferSource(); swSrc.buffer = paperBuffer(0.5, 0.05);
      var swBp = ctx.createBiquadFilter(); swBp.type = "bandpass"; swBp.Q.value = 0.5;
      swBp.frequency.setValueAtTime(1400, now + 0.04);
      swBp.frequency.linearRampToValueAtTime(2800, now + 0.25);
      swBp.frequency.linearRampToValueAtTime(1600, now + 0.5);
      var swG = ctx.createGain();
      swG.gain.setValueAtTime(0.0001, now + 0.04);
      swG.gain.linearRampToValueAtTime(0.4, now + 0.12);
      swG.gain.exponentialRampToValueAtTime(0.0001, now + 0.52);
      swSrc.connect(swBp); swBp.connect(swG); swG.connect(master); swG.connect(conv);
      swSrc.start(now + 0.04); swSrc.stop(now + 0.56);
    } catch (e) {}
  }

  // ── Page turn (Next/Previous): play the same sound as opening a book ──
  function pageTurn() {
    bookPull();
  }

  function tone(freq, start, dur, type, vol) {
    var o = ctx.createOscillator(); o.type = type || "sine";
    var g = ctx.createGain();
    var s = t0() + start;
    o.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, s);
    g.gain.exponentialRampToValueAtTime(vol || 0.2, s + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, s + dur);
    o.connect(g); g.connect(master);
    o.start(s); o.stop(s + dur + 0.03);
  }

  // ── Quiz correct: gentle two-tone chime ──
  function correct() {
    if (!audible()) return;
    try { tone(523.25, 0, 0.1, "sine", 0.2); tone(659.25, 0.1, 0.18, "sine", 0.2); } catch (e) {}
  }
  // ── Quiz wrong: low square buzz ──
  function wrong() {
    if (!audible()) return;
    try { tone(140, 0, 0.2, "square", 0.12); } catch (e) {}
  }
  // ── Professor Atlas summon: gentle rising three-note chime ──
  function atlasChime() {
    if (!audible()) return;
    try {
      tone(587.33, 0, 0.18, "sine", 0.16);
      tone(784.0, 0.1, 0.2, "sine", 0.15);
      tone(987.77, 0.22, 0.3, "sine", 0.14);
    } catch (e) {}
  }
  // ── Knowledge Core charge: rising sine sweep ──
  function coreCharge() {
    if (!audible()) return;
    try {
      var o = ctx.createOscillator(); o.type = "sine";
      var g = ctx.createGain(); var now = t0();
      o.frequency.setValueAtTime(300, now);
      o.frequency.exponentialRampToValueAtTime(800, now + 0.6);
      g.gain.setValueAtTime(0.0001, now);
      g.gain.exponentialRampToValueAtTime(0.22, now + 0.05);
      g.gain.exponentialRampToValueAtTime(0.0001, now + 0.62);
      o.connect(g); g.connect(master);
      o.start(now); o.stop(now + 0.64);
    } catch (e) {}
  }
  // ── Concept Card acquired: bright ascending three-note sparkle ──
  function reward() {
    if (!audible()) return;
    try {
      tone(659.25, 0, 0.12, "sine", 0.18);
      tone(880.0, 0.09, 0.14, "sine", 0.17);
      tone(1174.66, 0.2, 0.3, "sine", 0.15);
    } catch (e) {}
  }

  // ── First user gesture: browsers block audio until then ──
  function kick() {
    if (started) return;
    started = true;
    ensureCtx();
    try { if (ctx && ctx.state === "suspended") ctx.resume(); } catch (e) {}
    if (!muted) startFire();   // begin the ambient crackling fire on first gesture
  }
  ["pointerdown", "keydown"].forEach(function (ev) {
    document.addEventListener(ev, kick, { once: true });
  });

  // ── Mute toggle (top-right) — reflects the inherited global sound pref ──
  var btn = document.getElementById("lib-mute");
  function syncMuteBtn() {
    if (!btn) return;
    btn.textContent = muted ? "🔇" : "🔊";
    btn.classList.toggle("muted", muted);
    btn.setAttribute("aria-label", muted ? "Sound off" : "Sound on");
  }
  if (btn) {
    syncMuteBtn();   // show 🔇 at load if the user has sound off globally
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      kick();
      muted = !muted;
      try {
        if (ctx) {
          if (!muted && ctx.state === "suspended") ctx.resume();
          if (master) master.gain.value = muted ? 0 : 1;
          if (!muted) startFire();   // (idempotent) ensure the ambient is running
        }
      } catch (err) {}
      syncMuteBtn();
    });
  }

  // ── Drifting dust motes (30) ──
  var dust = document.getElementById("lib-dust");
  if (dust) {
    for (var i = 0; i < 30; i++) {
      var m = document.createElement("span");
      m.className = "dust-mote";
      m.style.left = (Math.random() * 100).toFixed(2) + "%";
      m.style.top = (60 + Math.random() * 40).toFixed(2) + "%";
      m.style.animationDuration = (8 + Math.random() * 12).toFixed(1) + "s";
      m.style.animationDelay = (-Math.random() * 20).toFixed(1) + "s";
      m.style.opacity = (0.2 + Math.random() * 0.5).toFixed(2);
      var sz = (1.5 + Math.random() * 1.5).toFixed(1);
      m.style.width = sz + "px"; m.style.height = sz + "px";
      dust.appendChild(m);
    }
  }

  // ── Knowledge Core energy burst (8 sparks fly outward) ──
  function coreBurst(el) {
    if (!el) return;
    try {
      for (var i = 0; i < 8; i++) {
        var s = document.createElement("span");
        s.className = "core-spark";
        var ang = (Math.PI * 2 / 8) * i;
        var dist = 46 + Math.random() * 22;
        s.style.setProperty("--dx", (Math.cos(ang) * dist).toFixed(1) + "px");
        s.style.setProperty("--dy", (Math.sin(ang) * dist).toFixed(1) + "px");
        el.appendChild(s);
        (function (node) { setTimeout(function () { if (node.parentNode) node.parentNode.removeChild(node); }, 950); })(s);
      }
      el.classList.add("bursting");
      setTimeout(function () { el.classList.remove("bursting"); }, 700);
    } catch (e) {}
  }

  // ── Completion celebration: candle frenzy + golden shockwave ──
  function celebrate() {
    try {
      document.body.classList.add("lib-celebrate");
      var wave = document.createElement("div");
      wave.className = "lib-shockwave";
      document.body.appendChild(wave);
      setTimeout(function () { if (wave.parentNode) wave.parentNode.removeChild(wave); }, 1000);
      setTimeout(function () { document.body.classList.remove("lib-celebrate"); }, 1200);
    } catch (e) {}
  }

  window.LibFX = {
    bookPull: bookPull,
    pageTurn: pageTurn,
    correct: correct,
    wrong: wrong,
    atlasChime: atlasChime,
    coreCharge: coreCharge,
    reward: reward,
    coreBurst: coreBurst,
    celebrate: celebrate,
  };
})();
