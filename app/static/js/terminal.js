// ════════════════════════════════════════════════════════════════
//  AI Lab — operate a 1990s research terminal.
//  Power-on → typewriter learn cards (screen-roll) → data-sorting
//  machine (card 4 → Q3) → reboot → ticker-tape quiz. Physical sector
//  toggle switches track progress. All audio is synthesised Web-Audio
//  (no files, no canvas, no libs), wrapped in try/catch.
// ════════════════════════════════════════════════════════════════
(function () {
  const page = document.querySelector(".terminal-page");
  if (!page) return;
  const location = page.dataset.location || "";
  const labPassed = page.dataset.passed === "1";   // Trial already conquered

  // ───────────────────────── AUDIO ─────────────────────────
  // Start muted if the hub "Master sound" preference is off (the local mute
  // button below still works to override it on this page).
  let actx = null, master = null, muted = !!(window.ATLAS_PREFS && window.ATLAS_PREFS.sound === false);
  function ac() {
    try {
      if (!actx) {
        const C = window.AudioContext || window.webkitAudioContext; if (!C) return null;
        actx = new C();
        master = actx.createGain(); master.gain.value = muted ? 0 : 1; master.connect(actx.destination);
      }
      if (actx.state === "suspended") actx.resume();
      return actx;
    } catch (e) { return null; }
  }
  function tone(freq, dur, type, vol, offset) {
    try {
      const a = ac(); if (!a) return;
      const o = a.createOscillator(), g = a.createGain();
      o.type = type || "sine"; o.frequency.value = freq;
      o.connect(g); g.connect(master);
      const t = a.currentTime + (offset || 0);
      g.gain.setValueAtTime(vol || 0.2, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.start(t); o.stop(t + dur + 0.03);
    } catch (e) {}
  }

  // Continuous monitor hum (60Hz) — starts at power-on, very quiet.
  let hum = null;
  function startHum() {
    try {
      const a = ac(); if (!a || hum) return;
      const o = a.createOscillator(), g = a.createGain();
      o.type = "sine"; o.frequency.value = 60;
      g.gain.value = 0.015;
      o.connect(g); g.connect(master); o.start();
      hum = { o: o, g: g };
    } catch (e) {}
  }
  function stopHum() { try { if (hum) { hum.o.stop(); hum = null; } } catch (e) {} }

  // Continuous conveyor rumble (filtered 80Hz noise) — only on card 4.
  let rumble = null;
  function startRumble() {
    try {
      const a = ac(); if (!a || rumble) return;
      const node = a.createScriptProcessor(2048, 1, 1);
      let last = 0;
      node.onaudioprocess = function (e) {
        const out = e.outputBuffer.getChannelData(0);
        for (let i = 0; i < out.length; i++) { const w = Math.random() * 2 - 1; last = (last + 0.02 * w) / 1.02; out[i] = last * 3; }
      };
      const lp = a.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 80;
      const g = a.createGain(); g.gain.value = 0.02;
      node.connect(lp); lp.connect(g); g.connect(master);
      rumble = { node: node, g: g };
    } catch (e) {}
  }
  function stopRumble() { try { if (rumble) { rumble.node.disconnect(); rumble = null; } } catch (e) {} }

  // Keyboard keystroke — short noise burst with an 800Hz resonance.
  let kbN = 0;
  function keyClick() {
    if (kbN++ % 2) return; // throttle to every other char
    try {
      const a = ac(); if (!a) return;
      const len = Math.floor(a.sampleRate * 0.02);
      const buf = a.createBuffer(1, len, a.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
      const s = a.createBufferSource(); s.buffer = buf;
      const bp = a.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 800; bp.Q.value = 6;
      const g = a.createGain(); g.gain.value = 0.18;
      s.connect(bp); bp.connect(g); g.connect(master);
      s.start();
    } catch (e) {}
  }
  // Switch flip — two quick clicks.
  function switchFlip() { tone(800, 0.015, "square", 0.26, 0); tone(400, 0.015, "square", 0.26, 0.02); }
  // Item drop — descending thunk.
  function itemDrop() {
    try {
      const a = ac(); if (!a) return;
      const o = a.createOscillator(), g = a.createGain();
      o.type = "square"; o.frequency.setValueAtTime(200, a.currentTime);
      o.frequency.exponentialRampToValueAtTime(80, a.currentTime + 0.1);
      g.gain.setValueAtTime(0.22, a.currentTime); g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + 0.12);
      o.connect(g); g.connect(master); o.start(); o.stop(a.currentTime + 0.14);
    } catch (e) {}
  }
  function rebootSweep() {
    try {
      const a = ac(); if (!a) return;
      const o = a.createOscillator(), g = a.createGain();
      o.type = "sawtooth";
      o.frequency.setValueAtTime(800, a.currentTime);
      o.frequency.linearRampToValueAtTime(200, a.currentTime + 0.6);
      g.gain.setValueAtTime(0.18, a.currentTime);
      g.gain.linearRampToValueAtTime(0.0001, a.currentTime + 0.65);
      o.connect(g); g.connect(master); o.start(); o.stop(a.currentTime + 0.7);
    } catch (e) {}
  }
  // Existing FX, +30% louder.
  const correctChime = () => { tone(523, 0.1, "sine", 0.26, 0); tone(659, 0.14, "sine", 0.26, 0.09); };
  const wrongBuzz = () => tone(80, 0.2, "square", 0.2, 0);
  const machineDone = () => { tone(330, 0.1, "sine", 0.22, 0); tone(440, 0.1, "sine", 0.22, 0.1); tone(660, 0.18, "sine", 0.22, 0.2); };

  // ───────────────── screen flicker (idle) ─────────────────
  const dim = document.getElementById("crt-dim");
  function scheduleFlicker() {
    const wait = 9000 + Math.random() * 5000;
    setTimeout(function () {
      if (dim) { dim.classList.add("on"); setTimeout(() => dim.classList.remove("on"), 120); }
      scheduleFlicker();
    }, wait);
  }

  // ───────────────── toggle switches ─────────────────
  function flipSwitch(n) {
    const sw = document.querySelector('.toggle-switch[data-sector="' + n + '"]');
    if (sw && !sw.classList.contains("on")) { sw.classList.add("on"); switchFlip(); }
  }

  // Persist a cleared sector (per user) so exploration survives navigation —
  // mirrors the Library's persistRead. Presentation/progress only; the sorting
  // game + graded quiz always run fresh, so Trial grading is never touched.
  function persistSector(n) {
    if (!location) return;
    try {
      fetch("/location/" + encodeURIComponent(location) + "/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item: "sector-" + n }),
        keepalive: true,
      });
    } catch (e) {}
  }

  // ───────────────── ASCII Atlas face ─────────────────
  const FACE_NORMAL = " .--.\n|o_o |\n|:_/ |";
  const FACE_HAPPY = " .--.\n|^_^ |\n|:_/ |";
  function atlasFace(happy) { const el = document.getElementById("atlas-ascii"); if (el) el.textContent = happy ? FACE_HAPPY : FACE_NORMAL; }

  // ───────────────── POWER-ON SEQUENCE ─────────────────
  const screenContent = document.getElementById("screen-content");
  const powerOn = document.getElementById("power-on");
  const poWarmup = document.getElementById("po-warmup");
  const poText = document.getElementById("po-text");
  const poBar = document.getElementById("po-bar");
  const poBarFill = document.getElementById("po-bar-fill");
  const powerLed = document.getElementById("power-led");

  function runPowerOn() {
    // 0–400ms: black. 400ms: warmup scan line sweeps top→bottom (300ms).
    setTimeout(function () { if (poWarmup) poWarmup.classList.add("sweep"); }, 400);
    // ~750ms: two quick flickers
    setTimeout(function () { if (poText) poText.classList.add("flick"); }, 760);
    setTimeout(function () { if (poText) poText.classList.remove("flick"); }, 900);
    // ~950ms: type INITIALISING
    setTimeout(function () {
      startHum();
      if (powerLed) powerLed.classList.add("on");
      typeLine(poText, "ATLAS-TERMINAL v2.3 INITIALISING...", 28, function () {
        if (poBar) poBar.hidden = false;
        // progress bar fills 600ms
        requestAnimationFrame(function () { if (poBarFill) poBarFill.style.width = "100%"; });
        setTimeout(function () {
          poText.textContent = "ATLAS-TERMINAL v2.3 INITIALISING...\nSYSTEM READY";
          setTimeout(finishPowerOn, 500);
        }, 700);
      });
    }, 950);
  }
  function finishPowerOn() {
    if (powerOn) powerOn.classList.add("done");
    setTimeout(function () {
      if (powerOn) powerOn.hidden = true;
      if (screenContent) screenContent.hidden = false;
      showBriefing();
      scheduleFlicker();
    }, 350);
  }

  // Mission briefing (instructions) shown before the sectors begin.
  function showBriefing() {
    const brief = document.getElementById("term-briefing");
    const stage = document.getElementById("term-stage");
    if (stage) stage.style.display = "none";
    if (!brief) { if (stage) stage.style.display = ""; typeCard(cards[0]); return; }
    brief.hidden = false;
    const bh = document.getElementById("brief-head");
    const list = document.getElementById("brief-list");
    const begin = document.getElementById("brief-begin");
    typeLine(bh, "> MISSION BRIEFING: SECTOR AI_LAB", 30, function () {
      if (list) list.classList.add("show");
      if (begin) begin.classList.add("show");
    });
    if (begin) begin.addEventListener("click", function () {
      brief.hidden = true;
      if (stage) stage.style.display = "";
      typeCard(cards[0]);
    });
  }
  // small generic line-typer (used by power-on + ticker tape)
  function typeLine(el, text, speed, done) {
    el.textContent = ""; let i = 0;
    const iv = setInterval(function () {
      el.textContent = text.slice(0, ++i); keyClick();
      if (i >= text.length) { clearInterval(iv); if (done) done(); }
    }, speed || 30);
  }

  // ───────────────── LEARN CARDS (typewriter + roll) ─────────────────
  const cards = Array.from(document.querySelectorAll(".term-card"));
  let cardIdx = 0;
  const crtRoll = document.getElementById("crt-roll");

  // Guess-first hooks (per sector, chunk order). Shown once each, never logged.
  let TERM_HOOKS = [];
  try { TERM_HOOKS = JSON.parse(document.getElementById("term-hooks").textContent) || []; } catch (e) { TERM_HOOKS = []; }
  const hooksShown = new Set();

  function showCardHook(card, hook) {
    const host = document.createElement("div");
    host.className = "lh-hook-host term-hook-host";
    (document.getElementById("crt-screen") || screenContent || card).appendChild(host);
    window.AtlasHook.mount(host, hook, {
      accent: "#8ab4d4",   // AI Lab interior accent (matches the CRT scene, not the brighter hub pin)
      onContinue: function () { if (host.parentNode) host.parentNode.removeChild(host); typeCard(card); },
    });
  }

  function typeCard(card) {
    // A quick guess-first beat before this sector's content is revealed.
    const hk = TERM_HOOKS[cardIdx];
    if (hk && !hooksShown.has(cardIdx) && window.AtlasHook) {
      hooksShown.add(cardIdx);
      showCardHook(card, hk);
      return;
    }
    if (card.dataset.machine === "1") { initMachine(card); return; }
    const head = card.querySelector(".term-head");
    const bodyEl = card.querySelector(".term-text");
    const load = card.querySelector(".term-load");
    const cont = card.querySelector(".term-continue");
    const headText = head.dataset.text, bodyText = bodyEl.dataset.text;
    head.textContent = ""; bodyEl.textContent = "";
    cont.disabled = true; cont.classList.remove("ready");
    if (load) load.textContent = "LOADING... 0%";
    head.classList.add("cursor");

    let i = 0;
    card._h = setInterval(function () {
      head.textContent = headText.slice(0, ++i); keyClick();
      if (i >= headText.length) {
        clearInterval(card._h); head.classList.remove("cursor");
        setTimeout(typeBodyNow, 350);
      }
    }, 38);

    function typeBodyNow() {
      let j = 0; bodyEl.classList.add("cursor");
      card._b = setInterval(function () {
        bodyEl.textContent = bodyText.slice(0, ++j); keyClick();
        if (load) load.textContent = "LOADING... " + Math.round((j / bodyText.length) * 100) + "%";
        if (j >= bodyText.length) {
          clearInterval(card._b); bodyEl.classList.remove("cursor");
          if (load) load.textContent = "READY";
          cont.disabled = false; cont.classList.add("ready");
        }
      }, 16);
    }
  }
  function skipCard(card) {
    clearInterval(card._h); clearInterval(card._b);
    const head = card.querySelector(".term-head"), bodyEl = card.querySelector(".term-text");
    if (head && head.dataset.text) { head.textContent = head.dataset.text; head.classList.remove("cursor"); }
    if (bodyEl && bodyEl.dataset.text) { bodyEl.textContent = bodyEl.dataset.text; bodyEl.classList.remove("cursor"); }
    const load = card.querySelector(".term-load"); if (load) load.textContent = "READY";
    const cont = card.querySelector(".term-continue"); cont.disabled = false; cont.classList.add("ready");
  }

  // Screen-roll: current card rolls up, roll bar sweeps, next rolls in.
  function rollToCard(fromCard, toIdx) {
    stopVoice(); // moving to the next sector — stop any read-aloud
    fromCard.classList.add("roll-out");
    if (crtRoll) { crtRoll.classList.remove("go"); void crtRoll.offsetWidth; crtRoll.classList.add("go"); }
    setTimeout(function () {
      fromCard.classList.remove("active", "roll-out");
      cardIdx = toIdx;
      const next = cards[toIdx];
      next.classList.add("active", "roll-in");
      setTimeout(function () { next.classList.remove("roll-in"); }, 220);
      typeCard(next);
    }, 220);
  }

  cards.forEach(function (card) {
    const cont = card.querySelector(".term-continue");
    if (cont) cont.addEventListener("click", function () {
      if (this.disabled) return;
      flipSwitch(cardIdx);           // completing a card lights its sector
      persistSector(cardIdx);        // remember it per-user (survives navigation)
      if (cardIdx === cards.length - 1) { reboot(); }
      else { rollToCard(card, cardIdx + 1); }
    });
    const skip = card.querySelector(".term-skip");
    if (skip) skip.addEventListener("click", () => skipCard(card));
  });

  // ── Read-aloud button per sector card (taught text only; respects mute) ──
  if (window.AtlasVoice && window.AtlasVoice.supported) {
    cards.forEach(function (card) {
      const actions = card.querySelector(".term-actions");
      if (!actions) return;
      const txtEl = card.querySelector(".term-text");
      const machineEl = card.querySelector(".machine-intro");
      const say = txtEl ? (txtEl.dataset.text || txtEl.textContent) : (machineEl ? machineEl.textContent : "");
      if (!say) return;
      const b = window.AtlasVoice.button("#8ab4d4");
      b.addEventListener("click", function () {
        if (muted) { window.AtlasVoice.stop(); return; } // a muted lab shouldn't talk
        window.AtlasVoice.toggle(say, "#8ab4d4", b);
      });
      actions.appendChild(b);
    });
  }
  function stopVoice() { if (window.AtlasVoice) window.AtlasVoice.stop(); }

  // ───────────────── CARD 4: SORTING MACHINE ─────────────────
  let machineReady = false;
  function initMachine(card) {
    if (machineReady) return;
    machineReady = true;
    startRumble();
    const game = card.querySelector(".sorting-game");
    const itemsWrap = card.querySelector("#sort-items");
    const items = Array.from(card.querySelectorAll(".sort-item"));
    const bins = Array.from(card.querySelectorAll(".sort-bin"));
    const cont = card.querySelector(".term-continue");
    const result = card.querySelector("#sort-result");
    const placement = {};
    let dragId = null;

    // items arrive on the conveyor one at a time
    items.forEach((it, k) => {
      it.style.opacity = "0";
      setTimeout(function () { it.classList.add("arrived"); it.style.opacity = ""; itemDrop(); }, 500 + k * 1200);
    });

    items.forEach(function (it) {
      it.addEventListener("dragstart", function (e) { dragId = it.dataset.id; try { e.dataTransfer.setData("text/plain", it.dataset.id); } catch (er) {} it.classList.add("dragging"); });
      it.addEventListener("dragend", function () { it.classList.remove("dragging"); });
    });
    bins.forEach(function (bin) {
      const drop = bin.querySelector(".bin-drop");
      bin.addEventListener("dragover", function (e) {
        e.preventDefault();
        const it = dragId ? card.querySelector('.sort-item[data-id="' + dragId + '"]') : null;
        bin.classList.remove("over-ok", "over-bad");
        if (it) bin.classList.add(it.dataset.bin === bin.dataset.bin ? "over-ok" : "over-bad");
      });
      bin.addEventListener("dragleave", function () { bin.classList.remove("over-ok", "over-bad"); });
      bin.addEventListener("drop", function (e) {
        e.preventDefault(); bin.classList.remove("over-ok", "over-bad");
        let id = ""; try { id = e.dataTransfer.getData("text/plain"); } catch (er) {} id = id || dragId;
        const it = card.querySelector('.sort-item[data-id="' + id + '"]');
        if (it) { drop.appendChild(it); placement[id] = bin.dataset.bin; it.classList.remove("err"); it.classList.add("settled"); itemDrop(); evaluate(); }
      });
    });
    if (itemsWrap) {
      itemsWrap.addEventListener("dragover", (e) => e.preventDefault());
      itemsWrap.addEventListener("drop", function (e) {
        e.preventDefault(); let id = ""; try { id = e.dataTransfer.getData("text/plain"); } catch (er) {} id = id || dragId;
        const it = card.querySelector('.sort-item[data-id="' + id + '"]');
        if (it) { itemsWrap.appendChild(it); delete placement[id]; it.classList.remove("settled"); }
      });
    }

    function evaluate() {
      let placed = 0, correct = 0;
      items.forEach((it) => { const p = placement[it.dataset.id]; if (p) { placed++; if (p === it.dataset.bin) correct++; } });
      if (placed < 6) return;
      if (result) { result.hidden = false; }
      if (correct >= 4) {
        result.textContent = "> CLASSIFICATION COMPLETE — ACCURACY " + correct + "/6 ✓\n> PROCEED TO NEXT SECTOR";
        items.forEach((it) => { if (placement[it.dataset.id] !== it.dataset.bin) it.classList.add("err"); it.setAttribute("draggable", "false"); });
        const ans = document.getElementById("q3-answer"); if (ans) ans.value = game.dataset.correctval;
        machineDone();
        if (cont) { cont.disabled = false; cont.classList.add("ready"); }
        stopRumble();
      } else {
        result.textContent = "> CLASSIFICATION FAILED — ACCURACY " + correct + "/6 ✗\n> REPROCESSING...";
        wrongBuzz();
        setTimeout(function () {
          items.forEach((it) => { itemsWrap.appendChild(it); it.classList.remove("err", "settled"); delete placement[it.dataset.id]; });
          if (result) result.hidden = true;
        }, 1200);
      }
    }
  }

  // ───────────────── REBOOT → QUIZ ─────────────────
  function flash(cls, dur) {
    const el = document.getElementById("crt-colorflash");
    if (!el) return; el.className = "crt-colorflash " + cls;
    setTimeout(function () { el.className = "crt-colorflash"; }, dur || 120);
  }
  function reboot() {
    stopVoice();
    stopRumble();
    rebootSweep();
    flash("white", 90);
    const screen = document.getElementById("reboot-screen");
    const rt = document.getElementById("reboot-text");
    const stage = document.getElementById("term-stage");
    setTimeout(function () {
      if (stage) stage.style.display = "none";
      if (screen) { screen.hidden = false; rt.textContent = ""; }
      const lines = ["SYSTEM REBOOT INITIATED...", "CLEARING MEMORY BANKS...", "LOADING DIAGNOSTIC PROTOCOL...", "ALL SECTORS VERIFIED", "INITIATING ASSESSMENT MODE"];
      let k = 0;
      (function nextLine() {
        if (k < lines.length) { rt.textContent += lines[k] + "\n"; keyClick(); k++; setTimeout(nextLine, 380); }
        else { setTimeout(function () { flash("white", 90); if (screen) screen.hidden = true; revealQuiz(); }, 700); }
      })();
    }, 650);
  }

  // ───────────────── TICKER-TAPE QUIZ ─────────────────
  const consulted = new Set();
  const consultedEl = document.getElementById("consulted");
  const form = document.getElementById("terminal-quiz");
  const tQs = Array.from(document.querySelectorAll(".ticker-q"));
  let tIdx = 0, submitting = false;

  function revealQuiz() {
    const quiz = document.getElementById("term-quiz");
    if (quiz) quiz.hidden = false;
    const tot = document.getElementById("tk-total"); if (tot) tot.textContent = tQs.length;
    showTicker(0);
  }
  function showTicker(i) {
    tIdx = i;
    tQs.forEach((q, k) => q.classList.toggle("active", k === i));
    const cur = document.getElementById("tk-cur"); if (cur) cur.textContent = i + 1;
    const q = tQs[i];
    const tape = q.querySelector(".tape-text");
    if (tape && !tape.dataset.done) {
      typeLine(tape, tape.dataset.text, 16, function () { tape.dataset.done = "1"; });
    }
  }
  function wireTicker(q) {
    const btns = Array.from(q.querySelectorAll(".console-btn"));
    const answerInput = q.querySelector(".q-answer");
    const status = q.querySelector(".ticker-status");
    btns.forEach(function (btn) {
      btn.addEventListener("click", async function () {
        if (q.classList.contains("answered")) return;
        q.classList.add("answered");
        const chosen = btn.dataset.val;
        if (answerInput) answerInput.value = chosen;   // form fallback; server is authoritative
        btns.forEach((b) => (b.disabled = true));      // lock immediately (first commit)

        // Ask the SERVER whether it was right — the answer key is not in the DOM.
        // It records this first commit and returns the correct letter + feedback.
        let ok = false, correct = null, fbmsg = "", known = false;
        try {
          const res = await fetch("/location/" + encodeURIComponent(location) + "/answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ attempt_id: (form && form.dataset.attempt) || "", qkey: q.dataset.qkey, letter: chosen }),
          });
          if (res.ok) { const d = await res.json(); ok = !!d.is_correct; correct = d.correct; fbmsg = d.feedback || ""; known = true; }
        } catch (e) {}

        if (known) {
          if (ok) {
            btn.classList.add("led-green");
            flash("green", 160);
            correctChime();
          } else {
            btn.classList.add("led-red", "shake");
            flash("red", 110);
            wrongBuzz();
            btns.forEach((b) => { if (b.dataset.val === correct) b.classList.add("led-green", "pulse"); else if (b !== btn) b.classList.add("dimmed"); });
          }
        }

        // Manual proceed (Enter or click).
        const last = tIdx >= tQs.length - 1;
        const proceed = function () { if (last) finishQuiz(); else showTicker(tIdx + 1); };
        q._proceed = proceed;
        if (status) {
          status.hidden = false;
          status.className = "ticker-status " + (known ? (ok ? "ok" : "bad") : "");
          status.innerHTML = "";
          const verdict = document.createElement("div");
          verdict.className = "ts-verdict";
          verdict.textContent = known ? (ok ? "VERIFIED ✓" : "INCORRECT — RETRY LOGGED") : "LOGGED";
          status.appendChild(verdict);
          if (fbmsg) {
            const fb = document.createElement("div");
            fb.className = "ts-feedback";
            fb.textContent = "> " + fbmsg;
            status.appendChild(fb);
          }
          const nextBtn = document.createElement("button");
          nextBtn.type = "button";
          nextBtn.className = "term-continue ts-next";
          nextBtn.textContent = last ? "> SUBMIT ASSESSMENT [ENTER]" : "> NEXT QUERY [ENTER]";
          nextBtn.addEventListener("click", proceed, { once: true });
          status.appendChild(nextBtn);
          try { nextBtn.focus(); } catch (err) {}
        } else {
          setTimeout(proceed, 1500);
        }
      });
    });
    // per-question hint → Atlas mini-monitor
    const hintBtn = q.querySelector(".hint-btn");
    const box = q.querySelector(".hint-box");
    if (hintBtn && box) {
      hintBtn.addEventListener("click", async function () {
        consulted.add(q.dataset.qkey);
        if (consultedEl) consultedEl.value = Array.from(consulted).join(",");
        atlasFace(true);
        box.hidden = false; box.textContent = "> ATLAS: processing query…";
        hintBtn.disabled = true;
        const fallback = q.dataset.hint || "Think about which option lacks neat rows and columns.";
        try {
          const res = await fetch("/npc/chat", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: "Give me a hint without revealing the answer: " + q.dataset.question, location: location }),
          });
          const data = await res.json();
          const good = data && data.response && !data.is_fallback;
          box.textContent = "> ATLAS: " + (good ? data.response : fallback);
        } catch (e) { box.textContent = "> ATLAS: " + fallback; }
        finally { hintBtn.disabled = false; setTimeout(() => atlasFace(false), 1200); }
      });
    }
  }
  tQs.forEach(wireTicker);

  function finishQuiz() {
    if (submitting || !form) return;
    submitting = true;
    flash("white", 90);
    setTimeout(function () { stopHum(); form.submit(); }, 600);
  }

  // ───────────────── ENTER key = press the active CONTINUE ─────────────────
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    const tag = (e.target && e.target.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA") return; // let the Atlas chat handle Enter
    // briefing first
    const brief = document.getElementById("term-briefing");
    if (brief && !brief.hidden) {
      const begin = document.getElementById("brief-begin");
      if (begin && begin.classList.contains("show")) { e.preventDefault(); begin.click(); }
      return;
    }
    // active quiz question awaiting proceed (after answering)
    const activeTq = document.querySelector(".ticker-q.active.answered");
    if (activeTq) {
      const nb = activeTq.querySelector(".ts-next");
      if (nb) { e.preventDefault(); nb.click(); }
      return;
    }
    // active learn / machine card continue
    const activeCard = document.querySelector(".term-card.active");
    if (activeCard) {
      const cont = activeCard.querySelector(".term-continue");
      if (cont && !cont.disabled) { e.preventDefault(); cont.click(); }
    }
  });

  // ───────────────── MUTE TOGGLE ─────────────────
  const muteBtn = document.getElementById("term-mute");
  if (muteBtn && muted) {  // reflect the inherited master-sound preference
    muteBtn.textContent = "🔇";
    muteBtn.classList.add("muted");
    muteBtn.setAttribute("aria-label", "Sound off");
  }
  if (muteBtn) muteBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    muted = !muted;
    ac(); // ensure context + master exist
    try { if (master) master.gain.value = muted ? 0 : 1; } catch (err) {}
    if (muted) stopVoice(); // muting also silences read-aloud
    muteBtn.textContent = muted ? "🔇" : "🔊";
    muteBtn.classList.toggle("muted", muted);
    muteBtn.setAttribute("aria-label", muted ? "Sound off" : "Sound on");
  });

  // ── Silent restore of cleared-sector exploration (mirrors the Library).
  //    Skips the power-on + briefing intro and resumes at the first uncleared
  //    sector with the earlier switches already lit — no replay. The sorting
  //    card (which feeds the graded Q3) and the quiz always run fresh, so the
  //    resume is capped at the sorting card and Trial grading is untouched. ──
  function restoreExploration() {
    let ids = [];
    try { ids = JSON.parse(document.getElementById("term-explored").textContent) || []; } catch (e) {}
    let cleared = 0;
    for (let i = 0; i < cards.length; i++) { if (ids.indexOf("sector-" + i) !== -1) cleared++; }
    if (cleared <= 0) return false;
    const resumeIdx = Math.min(cleared, cards.length - 1); // never skip the sorting card / Trial

    if (powerOn) powerOn.hidden = true;
    if (screenContent) screenContent.hidden = false;
    const brief = document.getElementById("term-briefing"); if (brief) brief.hidden = true;
    const stage = document.getElementById("term-stage"); if (stage) stage.style.display = "";
    if (powerLed) powerLed.classList.add("on");
    scheduleFlicker();

    for (let s = 0; s < resumeIdx; s++) {
      const sw = document.querySelector('.toggle-switch[data-sector="' + s + '"]');
      if (sw) sw.classList.add("on");   // light it silently (no flip sound)
      hooksShown.add(s);                // never replay a cleared sector's guess-first hook
    }
    cards.forEach(function (c) { c.classList.remove("active"); });
    cardIdx = resumeIdx;
    const card = cards[resumeIdx];
    card.classList.add("active");
    typeCard(card);                     // reveal the first uncleared sector
    return true;
  }

  // ── Already-mastered view: shown when the Trial is passed, so re-entry lands
  //    on a clear "completed" state instead of being dropped back into the
  //    sorting mission every time. Presentation only — no scoring/flow change. ──
  function showMastered() {
    if (powerOn) powerOn.hidden = true;
    if (screenContent) screenContent.hidden = false;
    const brief = document.getElementById("term-briefing"); if (brief) brief.hidden = true;
    const stage = document.getElementById("term-stage"); if (stage) stage.style.display = "none";
    if (powerLed) powerLed.classList.add("on");
    scheduleFlicker();
    for (let i = 0; i < cards.length; i++) {           // all sectors verified
      const sw = document.querySelector('.toggle-switch[data-sector="' + i + '"]');
      if (sw) sw.classList.add("on");
    }
    const m = document.getElementById("term-mastered"); if (m) m.hidden = false;
  }

  // "Re-run diagnostic": leave the mastered view and re-attempt the Trial. Jumps
  // straight to the sorting card (sectors already read) so the graded Q3 mechanic
  // runs fresh — grading/logging unchanged.
  function rerunDiagnostic() {
    const m = document.getElementById("term-mastered"); if (m) m.hidden = true;
    const stage = document.getElementById("term-stage"); if (stage) stage.style.display = "";
    const sortIdx = cards.length - 1;
    for (let i = 0; i < sortIdx; i++) {
      const sw = document.querySelector('.toggle-switch[data-sector="' + i + '"]');
      if (sw) sw.classList.add("on");
      hooksShown.add(i);                               // don't replay cleared sectors' hooks
    }
    machineReady = false;                              // let the sorting game re-initialise
    cards.forEach(function (c) { c.classList.remove("active"); });
    cardIdx = sortIdx;
    cards[sortIdx].classList.add("active");
    typeCard(cards[sortIdx]);
  }
  const rerunBtn = document.getElementById("term-rerun");
  if (rerunBtn) rerunBtn.addEventListener("click", rerunDiagnostic);

  // ───────────────── BOOT ─────────────────
  atlasFace(false);
  if (cards.length) {
    if (labPassed) showMastered();                     // Trial done → completed view
    else if (!restoreExploration()) runPowerOn();      // partial → resume; fresh → full intro
  }
  window.addEventListener("pagehide", stopHum);
})();
