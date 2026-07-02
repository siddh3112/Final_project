// ════════════════════════════════════════════════════════════════
//  Settings panel (hub). Slide-in, front-of-house controls only:
//  audio, accessibility, replay tutorial, progress (read-only), account.
//  Nothing here touches scoring, unlocking, or research data.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var gear = document.getElementById("settings-gear");
  var panel = document.getElementById("settings-panel");
  var backdrop = document.getElementById("settings-backdrop");
  var closeBtn = document.getElementById("settings-close");
  if (!gear || !panel || !backdrop) return;

  var P = window.AtlasPrefs;

  // ── open / close ──
  function open() {
    backdrop.hidden = false;
    // next frame so the transition runs
    requestAnimationFrame(function () {
      panel.classList.add("open");
      backdrop.classList.add("open");
    });
    panel.setAttribute("aria-hidden", "false");
    document.addEventListener("keydown", onKey);
  }
  function close() {
    panel.classList.remove("open");
    backdrop.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
    document.removeEventListener("keydown", onKey);
    setTimeout(function () { backdrop.hidden = true; }, 320);
    gear.focus();
  }
  function onKey(e) { if (e.key === "Escape") close(); }

  gear.addEventListener("click", open);
  closeBtn.addEventListener("click", close);
  backdrop.addEventListener("click", close);

  // ── a tiny confirmation chime (respects the sound preference) ──
  function chime() {
    if (!P || !P.soundOn()) return;
    try {
      var C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      var a = new C();
      [659.25, 987.77].forEach(function (f, i) {
        var o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        var t = a.currentTime + i * 0.08;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.15, t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);
        o.connect(g); g.connect(a.destination);
        o.start(t); o.stop(t + 0.45);
      });
      setTimeout(function () { try { a.close(); } catch (e) {} }, 900);
    } catch (e) {}
  }

  // ── AUDIO: master sound ──
  var sound = document.getElementById("set-sound");
  if (sound) sound.addEventListener("change", function () {
    if (!P) return;
    P.set("sound", sound.checked);
    if (sound.checked) chime();           // audible confirmation that sound is back
  });

  // ── AUDIO: Atlas voice (hide row if the browser can't speak) ──
  var voice = document.getElementById("set-voice");
  var voiceRow = document.getElementById("set-voice-row");
  var ttsOk = window.AtlasVoice && window.AtlasVoice.supported;
  if (!ttsOk && voiceRow) voiceRow.style.display = "none";
  if (voice && ttsOk) voice.addEventListener("change", function () {
    if (P) P.set("voice", voice.checked);
    if (voice.checked) {
      window.AtlasVoice.speak("Read aloud is now on.", "#8a5cf0");
    } else {
      window.AtlasVoice.stop();
    }
  });

  // ── ACCESSIBILITY: reduce motion ──
  var motion = document.getElementById("set-motion");
  var motionNote = document.getElementById("set-motion-note");
  if (motion) {
    if (P && P.osReduce) {              // OS forces it — reflect & lock the control
      motion.checked = true;
      motion.disabled = true;
      if (motionNote) motionNote.textContent = "On — forced by your system settings";
    }
    motion.addEventListener("change", function () {
      if (P) P.set("reduce_motion", motion.checked);
    });
  }

  // ── ACCESSIBILITY: larger text ──
  var text = document.getElementById("set-text");
  if (text) text.addEventListener("change", function () {
    if (P) P.set("large_text", text.checked);
  });

  // ── GAME: replay the how-to-play tutorial (reuse existing wiring) ──
  var replay = document.getElementById("set-replay");
  if (replay) replay.addEventListener("click", function () {
    close();
    var howto = document.getElementById("howto-btn");
    if (howto) setTimeout(function () { howto.click(); }, 320);
  });
})();
