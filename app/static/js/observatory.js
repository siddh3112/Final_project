// ════════════════════════════════════════════════════════════════
//  The Observatory — a living constellation sky.
//  Parallax star field, nebulae, meteors, cursor stardust, mysterious
//  pulses, cinematic discovery sequences, sky-colour evolution, and a
//  layered Web-Audio soundscape. Canvas 2D + Web Audio only.
//  Data / quiz / DB / Atlas logic unchanged — presentation only.
// ════════════════════════════════════════════════════════════════
(function () {
  const root = document.getElementById("observatory");
  if (!root) return;
  const location = root.dataset.location || "observatory";
  const canvas = document.getElementById("sky-canvas");
  const ctx = canvas.getContext("2d");

  // Reduce-motion: canvas FX can't be calmed by CSS, so gate them here.
  // Constellation mechanics (stars, lines, clicks, checks) stay fully working.
  const REDUCE = !!((window.AtlasPrefs && window.AtlasPrefs.effective && window.AtlasPrefs.effective("reduce_motion")) ||
    (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches));

  // ONE constellation that builds star-by-star (in order). Ten concepts: the
  // five machine-learning stars, then a compact "Modern Language AI" arc.
  //
  // This array is the SINGLE SOURCE OF TRUTH for how many stars there are. Every
  // counter, progress readout, intro line, and the "all discovered" check derives
  // its total from CONSTELLATION_STARS.length rather than repeating the number.
  // Adding or removing a star here updates all of them, and the completion sound
  // still fires at the right moment; hardcoding a count anywhere would silently
  // desynchronise the finale from the actual set.
  const CONSTELLATION_STARS = [
    { x: 9,  y: 62 },   // 1 — how ML learns/answers
    { x: 19, y: 42 },   // 2 — supervised
    { x: 30, y: 58 },   // 3 — unsupervised
    { x: 25, y: 30 },   // 4 — reinforcement
    { x: 40, y: 40 },   // 5 — three levels
    { x: 52, y: 60 },   // 6 — overfitting & bias
    { x: 63, y: 36 },   // 7 — NLP
    { x: 73, y: 56 },   // 8 — LLMs (Atlas)
    { x: 84, y: 30 },   // 9 — hallucination
    { x: 92, y: 54 },   // 10 — few-shot prompting
  ];

  const CONCEPTS = [
    { heading: "How Machines Learn & Answer", era: "CONCEPT 1 · FOUNDATION",
      content: "Machine learning is how AI makes sense of the messy, unstructured majority of real-world data. Two ideas help: how a system learns, and how it answers. On answering, a deterministic system gives the same output for the same input every time (a calculator always returns 56 for 7 × 8; a car's emergency-braking logic behaves identically each time), which makes it predictable and easy to audit. A probabilistic system instead expresses confidence, like a medical AI saying '78% likelihood of a tumour' rather than a flat yes or no. That ability to weigh uncertainty is what lets machine learning handle ambiguity, predict outcomes, and improve on its own over time.",
      type: "normal" },
    { heading: "Supervised Learning", era: "CONCEPT 2 · LABELLED DATA",
      content: "Supervised learning trains on labelled data, examples where the correct answer is already known. Feed it 50,000 emails each tagged 'spam' or 'not spam' and it learns the input→label relationship, then predicts the label for new, unseen emails. It covers classification (sorting into categories, like spam / not-spam or a photo labelled 'dog') and regression (predicting a number). It's the engine behind spam filters, image recognition, and medical-diagnosis tools.",
      type: "breakthrough" },
    { heading: "Unsupervised Learning", era: "CONCEPT 3 · FINDING PATTERNS",
      content: "Unsupervised learning works on unlabelled data with no correct answers provided; it finds hidden structure on its own. A streaming service that wants to group viewers with similar tastes, without anyone defining the groups in advance, is a classic case: the model clusters similar people together (customer segmentation). The same idea powers exploratory analysis and anomaly detection.",
      type: "normal" },
    { heading: "Reinforcement Learning", era: "CONCEPT 4 · TRIAL AND ERROR",
      content: "Reinforcement learning has no answer key at all. An agent learns by trial and error, earning rewards for good actions and penalties for bad ones as it interacts with an environment. Amazon's warehouse robots learn to pick and move goods this way, and game-playing AIs (chess, Go) master their games through the same reward-and-consequence loop. Over time the agent's decisions improve automatically, without human intervention.",
      type: "breakthrough" },
    { heading: "The Three Levels of AI", era: "CONCEPT 5 · THE BIG PICTURE",
      content: "Now the three levels of AI make deeper sense. Narrow AI specialises in one task and can't transfer it elsewhere; almost every AI you meet is narrow. Broad AI, IBM's term for what's available today, integrates several narrow components into one business process: a self-driving car combines vision, route-planning and decision-making (often improved through reinforcement learning) into a single system. General AI, still only a research goal, would reason and learn across any domain like a human. It does not exist yet.",
      type: "present" },
    { heading: "When Learning Goes Wrong", era: "CONCEPT 6 · PITFALLS",
      content: "Learning from data can misfire in two ways. OVERFITTING is when a model memorises its training examples instead of the general pattern; it scores brilliantly on data it has seen but fails on anything new, like a student who memorised past papers word-for-word. BIAS is subtler: a model absorbs whatever bias sits in its training data. Train a hiring model on years of biased human decisions and it will faithfully repeat that bias. So varied, fair data matters as much as a clever algorithm.",
      type: "normal" },
    { heading: "Machines That Read & Write", era: "CONCEPT 7 · LANGUAGE AI",
      content: "Natural Language Processing (NLP) is how machines work with human language. That means understanding what we write or say, and generating language back. It powers translation, voice assistants, spam detection and chatbots. Turning messy, ambiguous human words into something a machine can reason about is one of AI's hardest and most useful tricks.",
      type: "breakthrough" },
    { heading: "Large Language Models", era: "CONCEPT 8 · LLMs",
      content: "A Large Language Model (LLM) is trained on enormous amounts of text and learns to predict language so well it can answer questions, summarise, and hold a conversation. Professor Atlas, the guide who has walked this whole journey with you, is itself an LLM. It has no true understanding; it predicts the most likely next words from patterns in the text it was trained on.",
      type: "present" },
    { heading: "When AI Makes Things Up", era: "CONCEPT 9 · HALLUCINATION",
      content: "Because an LLM predicts plausible-sounding text rather than checking facts, it can produce a HALLUCINATION, a confident, fluent answer that is simply false. It can invent a citation, a date, or a quote and state it with total certainty. That is why you should verify important answers from any AI, including Professor Atlas.",
      type: "normal" },
    { heading: "Steering an LLM", era: "CONCEPT 10 · PROMPTING",
      content: "You guide an LLM through its PROMPT, the instructions and context you give it. FEW-SHOT PROMPTING means adding a few worked examples of the input→output you want before your real question, so the model copies the pattern. Showing two or three examples of 'review → sentiment' steers it far better than asking cold. How you prompt is a genuine skill of modern AI literacy.",
      type: "breakthrough" },
  ];

  // Star colour follows its concept type (cyan palette).
  function colorFor(type) { return type === "breakthrough" ? "#5ad0f0" : type === "present" ? "#ffffff" : "#3ab8d8"; }

  // Inline check questions — learning gates, NOT the graded quiz (not logged).
  const CHECKS = [
    { q: "How is machine learning different from a traditional computer program?",
      options: ["It follows exact pre-written rules", "It gives probabilities and improves itself over time", "It can only work with numbers"], correct: 1 },
    { q: "What does supervised learning need to work?",
      options: ["Labelled examples with correct answers", "No data at all", "A human watching at all times"], correct: 0 },
    { q: "What does unsupervised learning do with unlabelled data?",
      options: ["Ignores it completely", "Finds hidden patterns and groupings by itself", "Waits for a human to label it"], correct: 1 },
    { q: "How does reinforcement learning improve?",
      options: ["Through rewards for correct and penalties for wrong predictions", "By copying answers from a database", "It never improves"], correct: 0 },
    { q: "Which level of AI is available and used by enterprises today?",
      options: ["General AI", "Broad AI", "None of them exist yet"], correct: 1 },
    { q: "What is overfitting?",
      options: ["A model that memorises training data and then fails on new, unseen data", "A model trained on too little data", "A model with no training data at all"], correct: 0 },
    { q: "What does Natural Language Processing let machines do?",
      options: ["Only work with numbers", "Understand and generate human language", "Run ordinary calculations faster"], correct: 1 },
    { q: "What is a Large Language Model, like Professor Atlas?",
      options: ["A database of every sentence ever written", "A model trained on huge amounts of text that predicts language", "A human answering in real time"], correct: 1 },
    { q: "What is an AI 'hallucination'?",
      options: ["A confident answer that is actually false", "A picture an AI draws", "A hardware failure"], correct: 0 },
    { q: "What is few-shot prompting?",
      options: ["Giving the model a few examples to steer its output", "Asking the same question many times", "Training a whole model from scratch"], correct: 0 },
  ];
  function escapeHtml(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // Guess-first hooks (chunk order), shown before each star's concept. Never logged.
  let OBS_HOOKS = [];
  try { OBS_HOOKS = JSON.parse(document.getElementById("obs-hooks").textContent) || []; } catch (e) { OBS_HOOKS = []; }
  const obsHooksShown = new Set();

  const INTRO_SLIDES = [
    "The Observatory holds a single hidden constellation, the architecture of machine learning, traced star by star. Each star is one concept that lets machines learn, predict, and improve without being reprogrammed.",
    "The constellation builds in order. Click the one glowing star to discover its concept; a line then reaches out to the next star, and so on, until all " + CONSTELLATION_STARS.length + " connect into one complete shape.",
    "Only one star is ever ready at a time. It pulses with a ring to show you where to click next. Discover all " + CONSTELLATION_STARS.length + " to complete the constellation and unlock the Final Assessment. Professor Atlas is here if you need guidance.",
  ];

  const PENTA = [261.63, 293.66, 329.63, 392.0, 440.0]; // hover notes

  // ───────────────────────── AUDIO ─────────────────────────
  // Start muted if the hub "Master sound" preference is off (the local mute
  // button below still overrides it on this page).
  let actx = null, master = null, muted = !!(window.ATLAS_PREFS && window.ATLAS_PREFS.sound === false), ambient = null;
  function ac() {
    try {
      if (!actx) {
        const C = window.AudioContext || window.webkitAudioContext; if (!C) return null;
        actx = new C(); master = actx.createGain(); master.gain.value = muted ? 0 : 1; master.connect(actx.destination);
      }
      if (actx.state === "suspended") actx.resume();
      return actx;
    } catch (e) { return null; }
  }
  function startAmbient() {
    const a = ac(); if (!a || ambient) return;
    try {
      const defs = [[40, 0.018], [82, 0.012], [164, 0.006]];
      ambient = defs.map(function (d) {
        const o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = d[0]; g.gain.value = d[1];
        o.connect(g); g.connect(master); o.start();
        return o;
      });
    } catch (e) {}
  }
  function noiseBurst(freq, dur, vol) {
    try {
      const a = ac(); if (!a || muted) return;
      const len = Math.floor(a.sampleRate * dur);
      const buf = a.createBuffer(1, len, a.sampleRate); const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
      const s = a.createBufferSource(); s.buffer = buf;
      const bp = a.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = freq; bp.Q.value = 0.8;
      const g = a.createGain(); g.gain.value = vol;
      s.connect(bp); bp.connect(g); g.connect(master); s.start();
    } catch (e) {}
  }
  function chord(freqs, vol, dur, delayT, fb) {
    try {
      const a = ac(); if (!a || muted) return;
      let out = master;
      if (delayT) {
        const dl = a.createDelay(); dl.delayTime.value = delayT;
        const fbg = a.createGain(); fbg.gain.value = fb || 0.3;
        dl.connect(fbg); fbg.connect(dl); dl.connect(master);
        out = a.createGain(); out.connect(master); out.connect(dl);
      }
      freqs.forEach(function (f) {
        const o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, a.currentTime);
        g.gain.exponentialRampToValueAtTime(vol, a.currentTime + 0.03);
        g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + dur);
        o.connect(g); g.connect(out); o.start(); o.stop(a.currentTime + dur + 0.05);
      });
    } catch (e) {}
  }
  function note(freq, dur, vol, offset, type, detune) {
    try {
      const a = ac(); if (!a || muted) return;
      const o = a.createOscillator(), g = a.createGain();
      o.type = type || "sine"; o.frequency.value = freq; if (detune) o.detune.value = detune;
      const t = a.currentTime + (offset || 0);
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.03);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g); g.connect(master); o.start(t); o.stop(t + dur + 0.05);
    } catch (e) {}
  }
  // discovery sounds by type
  function soundNormal() { chord([523.25, 659.25, 783.99], 0.08, 0.8, 0.08, 0.3); }
  function soundBreakthrough() { chord([523.25, 659.25, 783.99, 1046.5], 0.12, 0.9, 0.15, 0.4); noiseBurst(6000, 0.05, 0.14); }
  function soundWinter() { chord([440, 523.25, 622.25], 0.07, 1.2, 0.1, 0.3); note(438, 1.2, 0.05, 0, "sine"); }
  function soundFinal() {
    chord([523.25, 659.25, 783.99, 1046.5, 1318.5], 0.15, 1.4, 0.2, 0.5);
    [523.25, 659.25, 783.99, 1046.5].forEach(function (f, i) { note(f, 0.3, 0.12, 0.8 + i * 0.3, "sine"); });
  }
  function soundMeteor() { noiseBurst(6000, 0.03, 0.06); }
  // inline-check feedback
  function checkOk() { chord([659.25, 987.77], 0.08, 0.5, 0.06, 0.25); }
  function checkBad() { note(140, 0.22, 0.12, 0, "square"); }
  function soundUnlock() {
    const scale = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25];
    scale.forEach(function (f, i) { note(f, 0.25, 0.1, i * 0.16, "sine"); });
    setTimeout(function () { chord([261.63, 329.63, 392.0, 523.25], 0.1, 1.5, 0.2, 0.45); }, 1300);
  }
  // hover tone management
  let hoverOsc = null, hoverGain = null, hoverIdxAudio = -1;
  // Hover tone: a single note that rings out over ~2.5s when the cursor
  // enters a constellation. Does not restart while staying on the same one.
  function hoverTone(idx) {
    if (idx === hoverIdxAudio) return;
    hoverIdxAudio = idx;
    if (idx < 0) return; // leaving: let the current note finish ringing
    try {
      const a = ac(); if (!a || muted) return;
      const o = a.createOscillator(), g = a.createGain();
      o.type = "sine"; o.frequency.value = PENTA[idx % PENTA.length];
      const t = a.currentTime, dur = 2.5;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.07, t + 0.15);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g); g.connect(master);
      o.start(t); o.stop(t + dur + 0.05);
    } catch (e) {}
  }
  function stopHoverTone() {
    try {
      if (hoverOsc && hoverGain) {
        const a = actx; const o = hoverOsc, g = hoverGain;
        g.gain.cancelScheduledValues(a.currentTime);
        g.gain.setValueAtTime(g.gain.value, a.currentTime);
        g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + 0.3);
        o.stop(a.currentTime + 0.32);
      }
    } catch (e) {}
    hoverOsc = null; hoverGain = null; hoverIdxAudio = -1;
  }

  // first-gesture audio kick + mute
  let kicked = false;
  function kick() { if (kicked) return; kicked = true; ac(); if (!muted) startAmbient(); }
  ["pointerdown", "keydown"].forEach((ev) => document.addEventListener(ev, kick, { once: true }));
  const muteBtn = document.getElementById("obs-mute");
  if (muteBtn && muted) {  // reflect the inherited master-sound preference
    muteBtn.textContent = "🔇"; muteBtn.classList.add("muted");
    muteBtn.setAttribute("aria-label", "Sound off");
  }
  if (muteBtn) muteBtn.addEventListener("click", function (e) {
    e.stopPropagation(); kick(); muted = !muted;
    try { if (master) master.gain.value = muted ? 0 : 1; } catch (er) {}
    if (muted && window.AtlasVoice) window.AtlasVoice.stop(); // muting also silences read-aloud
    muteBtn.textContent = muted ? "🔇" : "🔊"; muteBtn.classList.toggle("muted", muted);
  });

  // ───────────────────────── CANVAS / LAYERS ─────────────────────────
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  let W = 0, H = 0;
  function resize() {
    const r = canvas.getBoundingClientRect();
    W = r.width; H = Math.max(r.height, 1);
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener("resize", resize);

  function mkStars(n) {
    const a = [];
    for (let i = 0; i < n; i++) a.push({ fx: Math.random(), fy: Math.random(), r: Math.random() * 1.3 + 0.3, ph: Math.random() * 6.28, sp: 0.6 + Math.random() * 1.4 });
    return a;
  }
  let LAYER_BG = mkStars(200);
  const LAYER_MID = mkStars(80);
  const LAYER_FG = mkStars(30);
  // Milky Way band (fixed, no parallax)
  const milky = [];
  for (let i = 0; i < 150; i++) {
    const t = Math.random(); const spread = (Math.random() - 0.5) * 0.16;
    milky.push({ t: t, spread: spread, r: 0.4 + Math.random() * 0.3 });
  }
  // nebulae
  const nebulae = [
    { fx: 0.24, fy: 0.28, rad: 400, col: [20, 100, 140], ph: 0 },
    { fx: 0.78, fy: 0.74, rad: 380, col: [40, 120, 200], ph: 2.2 },
  ];

  // mouse / parallax / cursor trail
  let mx = 0, my = 0, haveMouse = false;
  const trail = []; let TRAIL_MAX = 12; let lastTrail = 0;
  const TRAIL_COLORS = ["#3ab8d8", "#ffffff", "#5ad0f0"];
  window.addEventListener("mousemove", function (e) {
    const r = canvas.getBoundingClientRect();
    mx = e.clientX - r.left; my = e.clientY - r.top; haveMouse = true;
    if (REDUCE) return; // no cursor stardust under reduce-motion
    // cursor stardust (throttled)
    const now = performance.now();
    if (mx >= 0 && my >= 0 && mx <= W && my <= H && now - lastTrail > 28 && trail.length < TRAIL_MAX) {
      lastTrail = now;
      trail.push({ x: mx, y: my, r: 1.5 + Math.random() * 1.5, c: TRAIL_COLORS[Math.floor(Math.random() * 3)], t0: now });
    }
  });

  // sky warmth evolution
  let warm = 0, warmTarget = 0;
  function setWarmTarget() {
    const n = discoveredCount;
    warmTarget = n >= 5 ? 0.10 : n >= 3 ? 0.04 : n >= 1 ? 0.015 : 0;
  }

  // ───────────────────────── STATE ─────────────────────────
  let discoveredCount = 0;     // stars fully completed (check passed) — drives lines
  let ready = true;            // is the next star clickable / pulsing yet?
  let introActive = true;      // cinematic intro still playing
  let activeStar = null;       // star currently ignited with its panel/check open
  let hoverIdx = -1;           // star under the cursor, or -1
  let starAnim = null;         // { idx, t0 } white flash of the star being ignited
  const lineAnims = [];        // { a, b, t0, done } electric line draws
  const fx = [];               // transient effects: shock / parts / aurora
  let brightenBoost = 0;
  let pendingUnlock = false;
  const phase = CONSTELLATION_STARS.map(() => Math.random() * 6.28);

  // geometry helpers (single constellation: index into CONSTELLATION_STARS)
  function stx(i) { return (CONSTELLATION_STARS[i].x / 100) * W; }
  function sty(i) { return (CONSTELLATION_STARS[i].y / 100) * H; }
  function hexA(hex, a) {
    const h = hex.replace("#", ""); const n = h.length === 3 ? h.split("").map((x) => x + x).join("") : h;
    return "rgba(" + parseInt(n.slice(0, 2), 16) + "," + parseInt(n.slice(2, 4), 16) + "," + parseInt(n.slice(4, 6), 16) + "," + a + ")";
  }

  // ───────────────────────── DRAW ─────────────────────────
  function skyGradient() {
    const g = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.75);
    const w = warm + brightenBoost * 0.12;
    g.addColorStop(0, "rgba(" + Math.round(58 * w * 9) + "," + Math.round(184 * w * 9) + "," + Math.round(216 * w * 9) + "," + Math.min(0.18, w + brightenBoost * 0.2) + ")");
    g.addColorStop(0.5, "rgba(20,18,46," + (0.5 + brightenBoost * 0.2) + ")");
    g.addColorStop(1, "#06060f");
    return g;
  }

  function drawNebula(neb, now) {
    const breathe = 0.04 + 0.04 * (0.5 + 0.5 * Math.sin(now / 8000 + neb.ph));
    const dx = Math.sin(now / 6000 + neb.ph) * 30;
    const dy = Math.cos(now / 7000 + neb.ph) * 24;
    const cx = neb.fx * W + dx, cy = neb.fy * H + dy;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, neb.rad);
    g.addColorStop(0, "rgba(" + neb.col[0] + "," + neb.col[1] + "," + neb.col[2] + "," + breathe + ")");
    g.addColorStop(1, "rgba(" + neb.col[0] + "," + neb.col[1] + "," + neb.col[2] + ",0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }

  function drawLayer(stars, factor, now) {
    const ox = (haveMouse && !REDUCE) ? -(mx - W / 2) * factor : 0;  // no parallax under reduce-motion
    const oy = (haveMouse && !REDUCE) ? -(my - H / 2) * factor : 0;
    ctx.save(); ctx.translate(ox, oy);
    for (const s of stars) {
      const tw = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(now / 1000 * s.sp + s.ph));
      ctx.beginPath(); ctx.arc(s.fx * W, s.fy * H, s.r, 0, 6.2832);
      ctx.fillStyle = "rgba(200,210,255," + (tw * 0.7).toFixed(3) + ")"; ctx.fill();
    }
    ctx.restore();
  }

  function drawMilky() {
    ctx.save();
    ctx.translate(W / 2, H / 2); ctx.rotate(28 * Math.PI / 180); ctx.translate(-W / 2, -H / 2);
    for (const m of milky) {
      const x = m.t * W * 1.4 - W * 0.2;
      const y = H / 2 + m.spread * H;
      ctx.beginPath(); ctx.arc(x, y, m.r, 0, 6.2832);
      ctx.fillStyle = "rgba(220,225,255,0.25)"; ctx.fill();
    }
    ctx.restore();
  }

  // meteors
  let nextMeteor = performance.now() + 4000 + Math.random() * 6000;
  const meteors = [];
  function spawnMeteor(now) {
    const fromTop = Math.random() < 0.5;
    const sxp = fromTop ? Math.random() * W : -40;
    const syp = fromTop ? -40 : Math.random() * H * 0.5;
    const exp = sxp + (W * 0.5 + Math.random() * W * 0.4);
    const eyp = syp + (H * 0.5 + Math.random() * H * 0.4);
    meteors.push({ sx: sxp, sy: syp, ex: exp, ey: eyp, t0: now, parts: [] });
    soundMeteor();
  }
  function drawMeteors(now) {
    if (REDUCE) return; // no shooting stars under reduce-motion
    if (now > nextMeteor) { spawnMeteor(now); nextMeteor = now + 8000 + Math.random() * 14000; }
    for (let i = meteors.length - 1; i >= 0; i--) {
      const m = meteors[i]; const p = (now - m.t0) / 600;
      if (p >= 1.6) { meteors.splice(i, 1); continue; }
      if (p <= 1) {
        const hx = m.sx + (m.ex - m.sx) * p, hy = m.sy + (m.ey - m.sy) * p;
        const ang = Math.atan2(m.ey - m.sy, m.ex - m.sx);
        const tx = hx - Math.cos(ang) * 120, ty = hy - Math.sin(ang) * 120;
        const g = ctx.createLinearGradient(hx, hy, tx, ty);
        g.addColorStop(0, "rgba(255,255,255,0.9)"); g.addColorStop(1, "rgba(255,255,255,0)");
        ctx.strokeStyle = g; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(tx, ty); ctx.stroke();
        if (Math.random() < 0.7 && m.parts.length < 40) m.parts.push({ x: hx, y: hy, vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4, t0: now });
      }
      for (const pt of m.parts) {
        const pp = (now - pt.t0) / 400; if (pp >= 1) continue;
        ctx.beginPath(); ctx.arc(pt.x + pt.vx * (now - pt.t0), pt.y + pt.vy * (now - pt.t0), 1, 0, 6.2832);
        ctx.fillStyle = "rgba(255,255,255," + (0.7 * (1 - pp)).toFixed(3) + ")"; ctx.fill();
      }
    }
  }

  function jitterLine(ax, ay, bx, by, p, seed) {
    // electric arc: midpoint jitter, recalculated periodically
    ctx.beginPath(); ctx.moveTo(ax, ay);
    const ex = ax + (bx - ax) * p, ey = ay + (by - ay) * p;
    const segs = 4;
    for (let s = 1; s < segs; s++) {
      const t = s / segs;
      const jx = ax + (ex - ax) * t + (Math.sin(seed + s * 1.3) * 6) * (1 - Math.abs(0.5 - t) * 2);
      const jy = ay + (ey - ay) * t + (Math.cos(seed + s * 2.1) * 6) * (1 - Math.abs(0.5 - t) * 2);
      ctx.lineTo(jx, jy);
    }
    ctx.lineTo(ex, ey); ctx.stroke();
  }

  function drawConstellation(now) {
    const N = CONSTELLATION_STARS.length;
    const nextIdx = discoveredCount;                 // the star that's appearing next
    const nextVisible = activeStar === null && !introActive && nextIdx < N;

    ctx.lineCap = "round";
    // Solid segments: every completed star reaches forward to the next star.
    for (let j = 0; j + 1 < N && j < discoveredCount; j++) {
      if (lineAnims.some(function (la) { return la.a === j; })) continue; // animating
      const col = colorFor(CONCEPTS[j].type);
      ctx.lineWidth = 2.8; ctx.strokeStyle = hexA(col, 0.95); ctx.shadowBlur = 12; ctx.shadowColor = col;
      ctx.beginPath(); ctx.moveTo(stx(j), sty(j)); ctx.lineTo(stx(j + 1), sty(j + 1)); ctx.stroke();
    }
    ctx.shadowBlur = 0;

    // Animating electric segment (drawn the moment a star is completed).
    for (let n = lineAnims.length - 1; n >= 0; n--) {
      const la = lineAnims[n]; const el = now - la.t0;
      if (el < 0) continue;
      const p = Math.min(1, el / 280);
      const lc = colorFor(CONCEPTS[la.a].type);
      ctx.lineWidth = 2.8; ctx.strokeStyle = hexA(lc, 1); ctx.shadowBlur = 16; ctx.shadowColor = lc;
      jitterLine(stx(la.a), sty(la.a), stx(la.b), sty(la.b), p, Math.floor(now / 50));
      if (p >= 1 && !la.done) { la.done = true; spawnParts(stx(la.b), sty(la.b), 4, 25, 300, lc); noiseBurst(3000, 0.015, 0.05); }
      if (el > 600) lineAnims.splice(n, 1);
    }
    ctx.shadowBlur = 0;

    // Rotating ring marks the next star (where to click).
    if (nextVisible) {
      ctx.save(); ctx.setLineDash([4, 8]); ctx.lineDashOffset = -(now / 100) % 12;
      ctx.strokeStyle = "rgba(58,184,216,0.55)"; ctx.lineWidth = 1.3;
      ctx.beginPath(); ctx.arc(stx(nextIdx), sty(nextIdx), 26, 0, 6.2832); ctx.stroke();
      ctx.restore();
    }

    // Stars: only the completed ones, the active one, and the single next
    // one are drawn — future stars stay hidden until it's their turn.
    for (let i = 0; i < N; i++) {
      const isDone = i < discoveredCount;
      const isActive = i === activeStar;
      const isNext = nextVisible && i === nextIdx;
      if (!isDone && !isActive && !isNext) continue;
      const x = stx(i), y = sty(i);
      const flashing = starAnim && starAnim.idx === i && (now - starAnim.t0) < 80;
      let rad, core, glow, gcol;
      if (isDone || isActive) {
        const col = colorFor(CONCEPTS[i].type);
        rad = 4.4; core = flashing ? "#ffffff" : "#eafdff"; glow = 22; gcol = col;
      } else { // next star — bright, pulsing
        rad = 5.2 + Math.sin(now / 480 + phase[i]) * 2.2; core = "#ffffff"; glow = 30; gcol = "#5ad0f0";
      }
      ctx.shadowBlur = glow; ctx.shadowColor = gcol; ctx.fillStyle = core;
      ctx.beginPath(); ctx.arc(x, y, Math.max(1.6, rad), 0, 6.2832); ctx.fill();
      ctx.beginPath(); ctx.arc(x, y, Math.max(1.6, rad), 0, 6.2832); ctx.fill(); // 2nd pass = stronger glow
      ctx.shadowBlur = 0;
    }
  }

  function spawnParts(x, y, n, dist, dur, color) {
    const parts = [];
    for (let i = 0; i < n; i++) { const a = Math.random() * 6.2832; const d = dist * (0.6 + Math.random() * 0.6); parts.push({ x: x, y: y, dx: Math.cos(a) * d, dy: Math.sin(a) * d, r: 2 }); }
    fx.push({ type: "parts", parts: parts, t0: performance.now(), dur: dur, color: color || "#ffffff" });
  }

  function drawFX(now) {
    for (let i = fx.length - 1; i >= 0; i--) {
      const e = fx[i];
      // A RAF timestamp can be a hair earlier than the performance.now() an fx
      // was queued with, making p slightly negative → a negative arc() radius
      // that throws and kills the loop. Floor it at 0.
      let p = (now - e.t0) / e.dur;
      if (p >= 1) { fx.splice(i, 1); continue; }
      if (p < 0) p = 0;
      if (e.type === "shock") {
        ctx.beginPath(); ctx.arc(e.x, e.y, Math.max(0, e.maxR * p), 0, 6.2832);
        ctx.strokeStyle = hexA(e.color, (1 - p) * 0.8); ctx.lineWidth = e.width * (1 - p); ctx.stroke();
      } else if (e.type === "parts") {
        for (const pt of e.parts) {
          ctx.beginPath(); ctx.arc(pt.x + pt.dx * p, pt.y + pt.dy * p, pt.r, 0, 6.2832);
          ctx.fillStyle = hexA(e.color, (1 - p) * 0.9); ctx.fill();
        }
      } else if (e.type === "aurora") {
        const top = H * 0.3;
        for (let b = 0; b < 3; b++) {
          const off = ((now / 3000 + b * 0.33) % 1) * W * 1.4 - W * 0.2;
          const col = b % 2 === 0 ? "rgba(0,210,210," : "rgba(40,130,220,";
          const g = ctx.createLinearGradient(off, 0, off + W * 0.5, 0);
          g.addColorStop(0, col + "0)"); g.addColorStop(0.5, col + (0.08 * (1 - Math.abs(0.5 - p) * 2)) + ")"); g.addColorStop(1, col + "0)");
          ctx.fillStyle = g; ctx.fillRect(0, 0, W, top);
        }
      }
    }
  }

  function drawTrail(now) {
    for (let i = trail.length - 1; i >= 0; i--) {
      const t = trail[i]; const p = (now - t.t0) / 600;
      if (p >= 1) { trail.splice(i, 1); continue; }
      ctx.beginPath(); ctx.arc(t.x, t.y - p * 3, t.r * (1 + p * 0.6), 0, 6.2832);
      ctx.fillStyle = hexA(t.c, (0.8 * (1 - p)).toFixed(3));
      ctx.shadowBlur = 6; ctx.shadowColor = t.c; ctx.fill(); ctx.shadowBlur = 0;
    }
  }

  // ── perf monitor / graceful degrade ──
  let frames = 0, fpsT = performance.now(), degrade = 0, nebulaAnim = true;
  function perf(now) {
    frames++;
    if (now - fpsT >= 1000) {
      const fps = frames * 1000 / (now - fpsT); frames = 0; fpsT = now;
      if (fps < 50 && degrade < 3) {
        degrade++;
        if (degrade === 1) TRAIL_MAX = 6;
        else if (degrade === 2) nebulaAnim = false;
        else if (degrade === 3) LAYER_BG = LAYER_BG.slice(0, 120);
      }
    }
  }

  function frame(now) {
    perf(now);
    // warmth + brighten easing
    setWarmTarget(); warm += (warmTarget - warm) * 0.04;
    if (brightenBoost > 0) brightenBoost *= 0.97;
    // Never let one bad draw call halt the animation loop.
    try {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = skyGradient(); ctx.fillRect(0, 0, W, H);
      if (nebulaAnim && !REDUCE) { drawNebula(nebulae[0], now); drawNebula(nebulae[1], now); }
      else { drawNebula(nebulae[0], 0); drawNebula(nebulae[1], 0); }
      drawMilky();
      drawLayer(LAYER_BG, 0.008, now);
      drawLayer(LAYER_MID, 0.02, now);
      drawLayer(LAYER_FG, 0.04, now);
      drawMeteors(now);
      drawConstellation(now);
      drawFX(now);
      drawTrail(now);
    } catch (err) { /* skip this frame; keep the sky alive */ }
    requestAnimationFrame(frame);
  }

  // ───────────────────────── HOVER + CLICK ─────────────────────────
  const tooltip = document.getElementById("obs-tooltip");
  // Only the single next-available star is interactive.
  function nextHit(px, py) {
    if (!ready || introActive || activeStar !== null) return -1;
    const i = discoveredCount;
    if (i >= CONSTELLATION_STARS.length) return -1;
    const dx = px - stx(i), dy = py - sty(i);
    return (dx * dx + dy * dy < 42 * 42) ? i : -1;
  }
  // A done star (i < discoveredCount) can be reopened READ-ONLY: content only, no
  // check re-asked, nothing recorded. Only when no star is active and not intro.
  function doneHit(px, py) {
    if (introActive || activeStar !== null || reviewing) return -1;
    for (let i = 0; i < discoveredCount && i < CONSTELLATION_STARS.length; i++) {
      const dx = px - stx(i), dy = py - sty(i);
      if (dx * dx + dy * dy < 42 * 42) return i;
    }
    return -1;
  }
  canvas.addEventListener("mousemove", function (e) {
    const r = canvas.getBoundingClientRect();
    const px = e.clientX - r.left, py = e.clientY - r.top;
    const i = nextHit(px, py);
    hoverIdx = i;
    if (i >= 0) {
      canvas.style.cursor = "pointer";
      hoverTone(i);
      tooltip.hidden = false; tooltip.textContent = CONCEPTS[i].era;
      tooltip.style.left = px + "px"; tooltip.style.top = (py - 30) + "px";
      tooltip.classList.add("show");
    } else {
      hoverTone(-1);
      const dh = doneHit(px, py);   // hovering a completed star: offer a re-read
      if (dh >= 0) {
        canvas.style.cursor = "pointer";
        tooltip.hidden = false; tooltip.textContent = "Re-read: " + CONCEPTS[dh].era;
        tooltip.style.left = px + "px"; tooltip.style.top = (py - 30) + "px";
        tooltip.classList.add("show");
      } else {
        canvas.style.cursor = "default";
        tooltip.classList.remove("show"); tooltip.hidden = true;
      }
    }
  });
  canvas.addEventListener("mouseleave", function () { hoverIdx = -1; hoverTone(-1); tooltip.classList.remove("show"); tooltip.hidden = true; });
  canvas.addEventListener("click", function (e) {
    const r = canvas.getBoundingClientRect();
    const px = e.clientX - r.left, py = e.clientY - r.top;
    if (nextHit(px, py) >= 0) { discover(); return; }
    const d = doneHit(px, py);
    if (d >= 0) openPanel(d, true);   // reopen an already-discovered star, read-only
  });

  // ───────────────────────── DISCOVERY ─────────────────────────
  const hintEl = document.getElementById("sky-hint");
  const countEl = document.getElementById("obs-count");
  const totalEl = document.getElementById("obs-total");
  if (totalEl) totalEl.textContent = CONSTELLATION_STARS.length;  // "CONCEPT x / N DISCOVERED"
  const progFill = document.getElementById("obs-progress-fill");

  // Step A — clicking the next star ignites it and opens its panel + check.
  // The connecting line + completion happen only after the check is passed.
  function discover() {
    if (!ready || introActive || activeStar !== null) return;
    const i = discoveredCount;
    if (i >= CONSTELLATION_STARS.length) return;
    ready = false; activeStar = i;
    starAnim = { idx: i, t0: performance.now() };
    const color = colorFor(CONCEPTS[i].type);
    note(PENTA[i % PENTA.length], 0.28, 0.06);          // ignite blip
    const cx = stx(i), cy = sty(i);
    setTimeout(function () { fx.push({ type: "shock", x: cx, y: cy, color: color, t0: performance.now(), dur: 500, maxR: 130, width: 2.5 }); }, 150);
    hoverTone(-1); if (tooltip) { tooltip.classList.remove("show"); tooltip.hidden = true; }
    if (hintEl) hintEl.style.opacity = "0";
    const cine = document.getElementById("obs-cinematic"); if (cine) cine.style.display = "none";
    setTimeout(function () { openPanel(i); }, 900);
    setTimeout(function () { starAnim = null; }, 1000);
  }

  // Persist a discovered star (per user) so the constellation survives
  // navigation — mirrors the Library's persistRead. Presentation/progress only;
  // never scoring, Trial grading, or research data.
  function persistStar(i) {
    try {
      fetch("/location/" + encodeURIComponent(location) + "/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item: "star-" + i }),
        keepalive: true,
      });
    } catch (e) {}
  }

  // Step B — passing the check completes the star: line draws, finale fires.
  function passCheck(i) {
    const concept = CONCEPTS[i];
    const color = colorFor(concept.type);
    discoveredCount = i + 1;
    persistStar(i);                 // remember it per-user (survives navigation)
    // reach forward: a line grows from this star to the next one as it appears
    if (i + 1 < CONSTELLATION_STARS.length) lineAnims.push({ a: i, b: i + 1, t0: performance.now(), done: false });
    if (countEl) countEl.textContent = discoveredCount;
    if (progFill) progFill.style.width = (discoveredCount / CONSTELLATION_STARS.length * 100) + "%";

    const cx = stx(i), cy = sty(i);
    // The finale (sound + aurora) fires ONCE, at true completion, derived from the
    // FULL star count (the same single source as the unlock gate) and never from a
    // concept type. The type "present" stars (a 5-star-era marker on stars 5 and 8)
    // no longer trigger it; they get the milestone cue like any breakthrough star.
    if (discoveredCount >= CONSTELLATION_STARS.length) {
      soundFinal();
      setTimeout(function () { fx.push({ type: "shock", x: cx, y: cy, color: "#ffffff", t0: performance.now(), dur: 700, maxR: 350, width: 3 }); spawnParts(cx, cy, 12, 90, 600, "#ffffff"); }, 150);
      brightenBoost = 1; fx.push({ type: "aurora", t0: performance.now(), dur: 3000 });
    } else if (concept.type === "breakthrough" || concept.type === "present") {
      soundBreakthrough();
      setTimeout(function () { fx.push({ type: "shock", x: cx, y: cy, color: "#ffffff", t0: performance.now(), dur: 700, maxR: 350, width: 3 }); spawnParts(cx, cy, 12, 90, 600, "#ffffff"); }, 150);
    } else {
      checkOk();
    }
    // The Trial gate unlocks ONLY once EVERY star/concept is mapped — derived from
    // the content length (CONSTELLATION_STARS), never a hardcoded count and never a
    // mid-journey "present" beat (which previously opened it at star 5). Solving
    // N-1 leaves it locked; solving the Nth (last) star opens it. Mirrors the
    // restoreExploration check so both agree.
    if (discoveredCount >= CONSTELLATION_STARS.length) pendingUnlock = true;
    activeStar = null; // star now fully discovered (i < discoveredCount)
  }

  // Fisher-Yates: a fresh, unseeded, uncached random order on every call, so the
  // correct option's on-screen position is never predictable across renders. The
  // ORIGINAL index is passed to answerCheck(), so grading is unaffected.
  function shuffled(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  // The check UI answer handler.
  function answerCheck(i, k, btn, optsEl, fbEl, closeBtn) {
    if (checkPassed) return;
    if (k === CHECKS[i].correct) {
      checkPassed = true;
      btn.classList.add("correct");
      const lt = btn.querySelector(".oc-letter"); if (lt) lt.textContent = "✓";
      optsEl.querySelectorAll(".obs-check-opt").forEach((o) => (o.disabled = true));
      fbEl.hidden = false; fbEl.className = "obs-check-fb ok"; fbEl.textContent = "✓ Correct. The star is charged";
      panel.classList.add("passed");
      passCheck(i);
      if (closeBtn) closeBtn.hidden = false;
    } else {
      btn.classList.add("wrong");
      checkBad();
      fbEl.hidden = false; fbEl.className = "obs-check-fb bad"; fbEl.textContent = "Not quite. Re-read the passage above and try again";
      setTimeout(function () { btn.classList.remove("wrong"); }, 600);
    }
  }

  // ───────────────────────── PANEL ─────────────────────────
  const panel = document.getElementById("obs-panel");
  const closeBtn = document.getElementById("obs-panel-close");
  // Read-aloud button in the concept panel (reads the concept text only).
  const ttsBtn = window.AtlasVoice && window.AtlasVoice.button("#3ab8d8");
  if (ttsBtn) {
    // Read-aloud lives inline on the concept page (reads the concept) — not
    // floating over the header, and never on the quick-check page.
    ttsBtn.classList.add("obs-read-btn");
    (document.getElementById("obs-read-slot") || document.getElementById("obs-panel-inner")).appendChild(ttsBtn);
  }
  function stopVoice() { if (window.AtlasVoice) window.AtlasVoice.stop(); }
  const checkQEl = document.getElementById("obs-check-q");
  const checkOptsEl = document.getElementById("obs-check-opts");
  const checkFbEl = document.getElementById("obs-check-fb");
  let checkPassed = false;
  let reviewing = false;   // a read-only reopen of an already-discovered star (content only, no record)
  const miniCanvas = document.getElementById("obs-mini");
  const miniCtx = miniCanvas.getContext("2d");
  let miniMax = 0, miniOpen = false, miniRAF = null, miniAngle = 0;
  function drawMini() {
    if (!miniOpen || miniMax < 1) return;
    const w = miniCanvas.width, h = miniCanvas.height;
    miniCtx.clearRect(0, 0, w, h);
    // fit the discovered path (stars 0..miniMax-1) into the mini canvas
    const pts = CONSTELLATION_STARS.slice(0, miniMax);
    let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
    pts.forEach((s) => { minX = Math.min(minX, s.x); minY = Math.min(minY, s.y); maxX = Math.max(maxX, s.x); maxY = Math.max(maxY, s.y); });
    const pad = 34, bw = (maxX - minX) || 1, bh = (maxY - minY) || 1;
    const scale = Math.min((w - pad * 2) / bw, (h - pad * 2) / bh);
    const cx = w / 2, cy = h / 2, mxC = (minX + maxX) / 2, myC = (minY + maxY) / 2;
    miniAngle += 0.0026; // ~1deg/sec @60fps
    miniCtx.save(); miniCtx.translate(cx, cy); miniCtx.rotate(miniAngle);
    function P(k) { return { x: (CONSTELLATION_STARS[k].x - mxC) * scale, y: (CONSTELLATION_STARS[k].y - myC) * scale }; }
    for (let k = 1; k < miniMax; k++) {
      const a = P(k - 1), b = P(k);
      miniCtx.strokeStyle = hexA(colorFor(CONCEPTS[k].type), 0.7); miniCtx.lineWidth = 1.4;
      miniCtx.beginPath(); miniCtx.moveTo(a.x, a.y); miniCtx.lineTo(b.x, b.y); miniCtx.stroke();
    }
    const t = performance.now();
    for (let k = 0; k < miniMax; k++) {
      const p = P(k), col = colorFor(CONCEPTS[k].type), r = 2.6 + Math.sin(t / 600 + k) * 0.8;
      miniCtx.beginPath(); miniCtx.arc(p.x, p.y, r, 0, 6.2832); miniCtx.shadowBlur = 8; miniCtx.shadowColor = col; miniCtx.fillStyle = col; miniCtx.fill();
    }
    miniCtx.shadowBlur = 0; miniCtx.restore();
    miniRAF = requestAnimationFrame(drawMini);
  }
  function openPanel(i, readOnly) {
    const concept = CONCEPTS[i];
    document.getElementById("obs-panel-inner").style.setProperty("--era", colorFor(concept.type));
    document.getElementById("obs-era").textContent = concept.era;
    document.getElementById("obs-heading").textContent = concept.heading;
    document.getElementById("obs-content").textContent = concept.content;
    // panel background star dots (once)
    const starsBg = document.getElementById("obs-panel-stars");
    if (starsBg && !starsBg.dataset.filled) {
      starsBg.dataset.filled = "1";
      for (let s = 0; s < 15; s++) { const d = document.createElement("span"); d.className = "obs-pstar"; d.style.left = (Math.random() * 100) + "%"; d.style.top = (Math.random() * 100) + "%"; starsBg.appendChild(d); }
    }
    // A read-only REVISIT of an already-discovered star shows the concept content
    // ONLY: no quick-check is re-asked and nothing is recorded. First-time discovery
    // (readOnly falsey) renders the gated check exactly as before.
    if (readOnly) {
      reviewing = true;
    } else {
      // render the inline check question (gate before the star locks in)
      checkPassed = false;
      panel.classList.remove("passed");
      const chk = CHECKS[i];
      checkQEl.textContent = chk.q;
      checkFbEl.hidden = true; checkFbEl.textContent = ""; checkFbEl.className = "obs-check-fb";
      checkOptsEl.innerHTML = "";
      const letters = ["A", "B", "C", "D"];
      shuffled(chk.options.map(function (opt, k) { return { opt: opt, k: k }; }))
        .forEach(function (o, d) {
          const b = document.createElement("button");
          b.type = "button"; b.className = "obs-check-opt";
          b.innerHTML = '<span class="oc-letter">' + letters[d] + '</span><span class="oc-text">' + escapeHtml(o.opt) + '</span>';
          b.addEventListener("click", function () { answerCheck(i, o.k, b, checkOptsEl, checkFbEl, closeBtn); });
          checkOptsEl.appendChild(b);
        });
    }
    if (closeBtn) closeBtn.hidden = !readOnly;   // a reread can be closed immediately

    // wire read-aloud to THIS concept's text (respects the observatory mute)
    if (ttsBtn) {
      stopVoice();
      ttsBtn.onclick = function () {
        if (muted) { stopVoice(); return; }
        window.AtlasVoice.toggle(concept.content, "#3ab8d8", ttsBtn);
      };
    }

    panel.hidden = false; panel.classList.remove("show"); void panel.offsetWidth; panel.classList.add("show");
    miniMax = i + 1; miniOpen = true; cancelAnimationFrame(miniRAF); miniAngle = 0; drawMini();

    // Tidy the mute control into the card header while the panel is open
    // (same button, same handler/state — just relocated for the reading view).
    const _tools = document.getElementById("obs-card-tools");
    if (muteBtn && _tools) { muteBtn.classList.add("in-card"); _tools.appendChild(muteBtn); }

    // Two-page card: concept first, quick-check on the NEXT page. Reset to page 1.
    const conceptPage = document.getElementById("obs-page-concept");
    const checkPage = document.getElementById("obs-page-check");
    const toCheckBtn = document.getElementById("obs-to-check");
    const contentEl = document.getElementById("obs-content");
    if (contentEl) contentEl.style.display = "";
    if (conceptPage) conceptPage.hidden = false;
    if (checkPage) checkPage.hidden = true;
    const readRow = document.getElementById("obs-read-row");
    if (readRow) readRow.style.display = "";
    if (toCheckBtn) {
      if (readOnly) {
        toCheckBtn.style.display = "none";   // no check to move on to on a reread
      } else {
        toCheckBtn.style.display = "";
        toCheckBtn.onclick = function () {
          stopVoice(); // stop any read-aloud when leaving the concept
          if (conceptPage) conceptPage.hidden = true;
          if (checkPage) {
            checkPage.hidden = false;
            checkPage.classList.remove("obs-page-in"); void checkPage.offsetWidth;
            if (!REDUCE) checkPage.classList.add("obs-page-in");
          }
        };
      }
    }

    // Guess-first hook beat: hide the concept + its controls until the learner
    // makes a quick guess, then reveal. Skipped on a read-only reread. Nothing recorded.
    const hk = readOnly ? null : OBS_HOOKS[i];
    if (hk && !obsHooksShown.has(i) && window.AtlasHook) {
      obsHooksShown.add(i);
      if (contentEl) contentEl.style.display = "none";
      if (toCheckBtn) toCheckBtn.style.display = "none";
      if (readRow) readRow.style.display = "none";
      const host = document.createElement("div");
      host.className = "lh-hook-host obs-hook-host";
      contentEl.parentNode.insertBefore(host, contentEl);
      window.AtlasHook.mount(host, hk, {
        accent: "#3ab8d8",
        onContinue: function () {
          if (host.parentNode) host.parentNode.removeChild(host);
          if (contentEl) contentEl.style.display = "";
          if (toCheckBtn) toCheckBtn.style.display = "";
          if (readRow) readRow.style.display = "";
        },
      });
    }
  }
  function closePanel() {
    if (reviewing) {
      // Read-only reopen: just close, leaving all progress/flow state untouched.
      reviewing = false;
      stopVoice();
      if (muteBtn && muteBtn.classList.contains("in-card")) {
        muteBtn.classList.remove("in-card");
        if (root) root.appendChild(muteBtn);
      }
      panel.classList.remove("show"); panel.hidden = true; miniOpen = false; cancelAnimationFrame(miniRAF);
      return;
    }
    if (!checkPassed) return; // gated — must pass the check before leaving
    stopVoice(); // leaving the concept — stop read-aloud
    // Return the mute control to the sky (fixed top-right).
    if (muteBtn && muteBtn.classList.contains("in-card")) {
      muteBtn.classList.remove("in-card");
      if (root) root.appendChild(muteBtn);
    }
    panel.classList.remove("show"); panel.hidden = true; miniOpen = false; cancelAnimationFrame(miniRAF);
    ready = true; // the next star now becomes clickable and starts pulsing
    if (pendingUnlock) { pendingUnlock = false; ready = false; setTimeout(runUnlock, 300); }
  }
  panel.querySelectorAll("[data-panel-close]").forEach((el) => el.addEventListener("click", closePanel));

  // ───────────────────────── UNLOCK CINEMATIC ─────────────────────────
  const trialGate = document.getElementById("obs-trial-gate");
  const trialReady = document.getElementById("obs-trial-ready");
  function typeInto(el, text, speed, done) {
    el.textContent = ""; let k = 0;
    const iv = setInterval(function () { el.textContent = text.slice(0, ++k); if (k >= text.length) { clearInterval(iv); if (done) done(); } }, speed);
  }
  function runUnlock() {
    soundUnlock();
    if (trialGate) trialGate.hidden = true;
    if (trialReady) trialReady.hidden = false;
    // sync pulse all
    brightenBoost = 0.6;
    const ov = document.getElementById("obs-unlock");
    const l1 = document.getElementById("obs-uline1"), l2 = document.getElementById("obs-uline2"), l3 = document.getElementById("obs-uline3");
    const sweep = document.getElementById("obs-unlock-sweep"), btn = document.getElementById("obs-final-btn");
    l1.textContent = ""; l2.textContent = ""; l3.textContent = ""; if (btn) btn.hidden = true;
    setTimeout(function () { ov.hidden = false; ov.classList.add("show"); }, 1800);
    setTimeout(function () { typeInto(l1, "ALL " + CONSTELLATION_STARS.length + " CONCEPTS MAPPED", 45); }, 2800);
    setTimeout(function () { typeInto(l2, "THE MACHINE LEARNING ATLAS IS COMPLETE", 35); }, 3500);
    setTimeout(function () { typeInto(l3, "FINAL ASSESSMENT UNLOCKED", 45); }, 4200);
    setTimeout(function () { if (sweep) { sweep.classList.remove("go"); void sweep.offsetWidth; sweep.classList.add("go"); } }, 5000);
    setTimeout(function () { if (btn) { btn.hidden = false; btn.classList.add("show"); } }, 5600);
  }

  // ── Silent restore of discovered stars (mirrors the Library). Re-lights the
  //    already-discovered stars + their constellation lines and sets CONCEPT
  //    x/N, WITHOUT replaying the cinematic intro or any discovery animation. ──
  function restoreExploration() {
    let ids = [];
    try { ids = JSON.parse(document.getElementById("obs-explored").textContent) || []; } catch (e) {}
    const N = CONSTELLATION_STARS.length;
    let n = 0;
    for (let i = 0; i < N; i++) { if (ids.indexOf("star-" + i) !== -1) n++; }
    if (n <= 0) return false;
    discoveredCount = Math.min(n, N);   // the draw loop redraws the lines from this
    introActive = false;                // no cinematic
    ready = discoveredCount < N;        // the next star (if any) pulses / is clickable
    if (countEl) countEl.textContent = discoveredCount;
    if (progFill) progFill.style.width = (discoveredCount / N * 100) + "%";
    const hint = document.getElementById("sky-hint"); if (hint) hint.style.display = "none";
    if (discoveredCount >= N) {
      // Whole constellation already mapped — restore the unlocked Trial end
      // state silently (no unlock cinematic / overlay replay).
      if (trialGate) trialGate.hidden = true;
      if (trialReady) trialReady.hidden = false;
    }
    return true;
  }

  // ───────────────────────── CINEMATIC INTRO ─────────────────────────
  (function cinematic() {
    const cine = document.getElementById("obs-cinematic");
    // Returning with progress: skip the intro and restore the constellation.
    if (restoreExploration()) { if (cine) cine.style.display = "none"; return; }
    if (!cine) { introActive = false; return; }
    const lines = [1, 2, 3, 4].map((n) => document.getElementById("obs-cine-" + n));
    const prompt = document.getElementById("obs-cine-prompt");
    const skip = document.getElementById("obs-cine-skip");
    const timers = [];
    function twinkle() { fx.push({ type: "shock", x: Math.random() * W, y: Math.random() * H * 0.8, color: "#ffffff", t0: performance.now(), dur: 600, maxR: 16, width: 2 }); }
    function reveal() {
      lines.forEach((l) => l.classList.remove("show"));
      setTimeout(function () { if (prompt) { prompt.hidden = false; prompt.classList.add("show"); } }, 300);
      introActive = false; // the first star now pulses and becomes clickable
    }
    lines.forEach(function (l, k) {
      timers.push(setTimeout(function () { kick(); l.classList.add("show"); twinkle(); }, 400 + k * 2000));
    });
    timers.push(setTimeout(reveal, 400 + 4 * 2000));
    if (skip) skip.addEventListener("click", function () {
      kick(); timers.forEach(clearTimeout);
      lines.forEach((l) => l.classList.remove("show"));
      if (prompt) prompt.hidden = true;
      introActive = false;
      cine.style.display = "none";
    });
  })();

  // ───────────────────────── BOOT ─────────────────────────
  resize();
  requestAnimationFrame(frame);
})();
