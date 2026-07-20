// ════════════════════════════════════════════════════════════════
//  AI Lab — Dark Data Visualiser.
//  Chaotic "dark data" particles organise into a structured grid as the
//  student reads each card. By the quiz, all particles form an amber grid.
//  Pure canvas + arithmetic, no libraries. Graceful fps fallback.
// ════════════════════════════════════════════════════════════════
(function () {
  const canvas = document.getElementById("dd-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const labelEl = document.getElementById("dd-label");
  const waveEl = document.getElementById("dd-wave");

  const PALETTE = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#c77dff", "#ffffff"];
  const ORGANISED = ["#4d96ff", "#6bb6ff", "#a8d0ff", "#ffffff"];
  const AMBER = "#d4a84b";

  const LABELS = {
    0: "",
    1: "DARK DATA DETECTED: 2.5 BILLION RECORDS UNPROCESSED",
    2: "PATTERN RECOGNITION INITIALISING…",
    3: "STRUCTURE EMERGING: AI PROCESSING",
    4: "DARK DATA STRUCTURED: READY FOR ANALYSIS",
  };

  let COUNT = 200;
  let W = 0, H = 0;
  let particles = [];
  let grid = [];
  let stage = 0;
  let pulse = 0; // gentle breathing once grid is formed

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
    computeGrid();
    // re-point any organised particles at the new grid
    if (stage > 0) assignTargets();
  }

  function computeGrid() {
    const cols = Math.max(1, Math.round(Math.sqrt(COUNT * (W / H))));
    const rows = Math.ceil(COUNT / cols);
    const mx = W * 0.12, my = H * 0.18;
    const gw = W - 2 * mx, gh = H - 2 * my;
    grid = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (grid.length >= COUNT) break;
        grid.push({
          x: mx + (cols > 1 ? (gw * c) / (cols - 1) : gw / 2),
          y: my + (rows > 1 ? (gh * r) / (rows - 1) : gh / 2),
        });
      }
    }
  }

  function makeParticles() {
    particles = [];
    for (let i = 0; i < COUNT; i++) {
      particles.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 1.7,
        vy: (Math.random() - 0.5) * 1.7,
        size: 2 + Math.random() * 6,
        colour: PALETTE[(Math.random() * PALETTE.length) | 0],
        targetX: 0,
        targetY: 0,
        organised: false,
      });
    }
  }

  // Mark the first `want` particles organised and point them at grid cells.
  function assignTargets() {
    const want = Math.floor((stage / 4) * COUNT);
    for (let i = 0; i < COUNT; i++) {
      const p = particles[i];
      if (i < want) {
        p.organised = true;
        const g = grid[i] || grid[grid.length - 1];
        p.targetX = g.x;
        p.targetY = g.y;
        if (stage >= 4) {
          p.colour = AMBER;
          p.size = 4;
        } else {
          p.colour = ORGANISED[i % ORGANISED.length];
        }
      } else {
        p.organised = false;
      }
    }
  }

  function setStage(n) {
    stage = n;
    assignTargets();
    if (labelEl) {
      labelEl.textContent = LABELS[n] || "";
      labelEl.classList.toggle("done", n >= 4);
    }
    if (n >= 4) goldWave();
  }

  function goldWave() {
    if (!waveEl) return;
    waveEl.classList.remove("run");
    void waveEl.offsetWidth;
    waveEl.classList.add("run");
  }

  // ── animation loop with fps fallback ──
  let lastFpsCheck = performance.now();
  let frames = 0;
  let reduced = false;

  function frame(now) {
    ctx.clearRect(0, 0, W, H);
    pulse += 0.02;
    const breathe = stage >= 4 ? 1 + Math.sin(pulse) * 0.25 : 1;

    for (let i = 0; i < COUNT; i++) {
      const p = particles[i];
      if (p.organised) {
        p.x += (p.targetX - p.x) * 0.05;
        p.y += (p.targetY - p.y) * 0.05;
      } else {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1;
        if (p.y < 0 || p.y > H) p.vy *= -1;
      }
      ctx.beginPath();
      ctx.fillStyle = p.colour;
      ctx.globalAlpha = stage >= 4 ? 0.55 + Math.sin(pulse + i) * 0.25 : 0.85;
      ctx.arc(p.x, p.y, p.size * (p.organised && stage >= 4 ? breathe : 1), 0, 6.2832);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    // fps check every ~1s; drop particle budget if struggling
    frames++;
    if (now - lastFpsCheck > 1000) {
      const fps = (frames * 1000) / (now - lastFpsCheck);
      frames = 0;
      lastFpsCheck = now;
      if (fps < 50 && !reduced) {
        if (COUNT > 150) COUNT = 150;
        else if (COUNT > 100) { COUNT = 100; reduced = true; }
        particles = particles.slice(0, COUNT);
        computeGrid();
        assignTargets();
      }
    }
    requestAnimationFrame(frame);
  }

  // ── card flow ──
  const cards = Array.from(document.querySelectorAll(".dd-card"));
  let cardIdx = 0;

  function setCountLabels(target) {
    document.querySelectorAll(".dd-count").forEach((el) => {
      el.textContent = "PARTICLES ORGANISED: " + target + "/" + COUNT;
    });
  }
  function animateCount(toStage) {
    const target = Math.floor((toStage / 4) * COUNT);
    const start = Math.floor(((toStage - 1) / 4) * COUNT);
    let v = start;
    const step = Math.max(1, Math.round((target - start) / 40));
    const id = setInterval(() => {
      v = Math.min(target, v + step);
      setCountLabels(v);
      if (v >= target) clearInterval(id);
    }, 40);
  }

  function continueCard() {
    const isLast = cardIdx === cards.length - 1;
    const nextStage = cardIdx + 1;
    cards[cardIdx].classList.add("leaving");
    startSound(nextStage);
    setStage(nextStage);
    animateCount(nextStage);

    setTimeout(function () {
      cards[cardIdx].classList.remove("active", "leaving");
      if (isLast) {
        revealQuiz();
      } else {
        cardIdx++;
        cards[cardIdx].classList.add("active");
      }
    }, isLast ? 1800 : 1000);
  }

  function revealQuiz() {
    const quiz = document.getElementById("dd-quiz");
    if (labelEl) labelEl.textContent = "ANALYSIS COMPLETE: INITIATING ASSESSMENT";
    setTimeout(function () {
      if (quiz) {
        quiz.hidden = false;
        quiz.classList.add("rise");
        quiz.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      stopSound();
    }, 1400);
  }

  document.querySelectorAll(".dd-continue").forEach((b) => b.addEventListener("click", continueCard));

  // ── optional ambient sound (best-effort) ──
  let ac = null, osc = null, gain = null;
  function startSound(toStage) {
    try {
      if (!ac) {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return;
        ac = new Ctx();
        osc = ac.createOscillator();
        gain = ac.createGain();
        osc.type = "sine";
        osc.frequency.value = 60;
        gain.gain.value = 0.04;
        osc.connect(gain);
        gain.connect(ac.destination);
        osc.start();
      }
      if (ac.state === "suspended") ac.resume();
      const freq = 60 + (toStage / 4) * 380; // rises toward 440hz
      osc.frequency.linearRampToValueAtTime(freq, ac.currentTime + 1.5);
    } catch (e) {}
  }
  function stopSound() {
    try {
      if (osc && gain && ac) {
        osc.frequency.linearRampToValueAtTime(440, ac.currentTime + 0.4);
        gain.gain.linearRampToValueAtTime(0.0001, ac.currentTime + 1.6);
        osc.stop(ac.currentTime + 1.7);
      }
    } catch (e) {}
  }

  // ── Atlas orbit: scatter briefly when a hint is requested ──
  document.addEventListener("click", function (e) {
    if (e.target.closest(".hint-btn")) {
      const orbit = document.getElementById("atlas-orbit");
      if (orbit) {
        orbit.classList.add("scatter");
        setTimeout(() => orbit.classList.remove("scatter"), 900);
      }
    }
  });

  // ── boot ──
  window.addEventListener("resize", resize);
  resize();
  makeParticles();
  setStage(0);
  requestAnimationFrame(frame);
})();
