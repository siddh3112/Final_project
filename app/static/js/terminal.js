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

  // ───────────────────────── AUDIO ─────────────────────────
  let actx = null, master = null, muted = false;
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

  function typeCard(card) {
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
      btn.addEventListener("click", function () {
        if (q.classList.contains("answered")) return;
        q.classList.add("answered");
        const chosen = btn.dataset.val;
        const correct = q.dataset.correct;
        if (answerInput) answerInput.value = chosen;
        const ok = chosen === correct;
        if (ok) {
          btn.classList.add("led-green");
          flash("green", 160);
          correctChime();
          if (status) { status.hidden = false; status.textContent = "VERIFIED ✓"; status.className = "ticker-status ok"; }
        } else {
          btn.classList.add("led-red", "shake");
          flash("red", 110);
          wrongBuzz();
          btns.forEach((b) => { if (b.dataset.val === correct) b.classList.add("led-green", "pulse"); else if (b !== btn) b.classList.add("dimmed"); });
          if (status) { status.hidden = false; status.textContent = "INCORRECT — RETRY LOGGED"; status.className = "ticker-status bad"; }
        }
        btns.forEach((b) => (b.disabled = true));
        setTimeout(function () {
          if (tIdx < tQs.length - 1) { showTicker(tIdx + 1); }
          else { finishQuiz(); }
        }, 1500);
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
    // active learn / machine card continue
    const activeCard = document.querySelector(".term-card.active");
    if (activeCard) {
      const cont = activeCard.querySelector(".term-continue");
      if (cont && !cont.disabled) { e.preventDefault(); cont.click(); }
    }
  });

  // ───────────────── MUTE TOGGLE ─────────────────
  const muteBtn = document.getElementById("term-mute");
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

  // ───────────────── BOOT ─────────────────
  atlasFace(false);
  if (cards.length) runPowerOn();
  window.addEventListener("pagehide", stopHum);
})();
