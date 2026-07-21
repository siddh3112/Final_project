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

  // ── AUDIO: voice picker (populated at runtime from the browser's voices) ──
  var vSelect = document.getElementById("set-voice-select");
  var vPreview = document.getElementById("set-voice-preview");
  var vpRow = document.getElementById("set-voicepick-row");
  var vHint = document.getElementById("set-voice-hint");
  if (!ttsOk && vpRow) vpRow.style.display = "none";

  function friendly(v) { return v.name + (v.lang ? " (" + v.lang + ")" : ""); }
  function byName(a, b) { return (a.name || "").localeCompare(b.name || ""); }

  // macOS/browsers ship several novelty/robotic voices (Grandpa, Grandma,
  // Zarvox, Bubbles, …). Hide them so the picker only lists real, usable
  // voices — mirrors the BAD_NAMES filter tts.js uses for the "Automatic" pick.
  var NOVELTY = /compact|eloquence|fred|albert|zarvox|trinoids|whisper|bells|bad news|boing|bubbles|cellos|deranged|good news|jester|organ|superstar|wobble|bahh|grandma|grandpa|reed|rocko|sandy|shelley/i;

  function populateVoices() {
    if (!ttsOk || !vSelect || !window.speechSynthesis) return;
    var voices = window.speechSynthesis.getVoices() || [];
    if (!voices.length) return;          // wait for the 'voiceschanged' event
    var current = (window.ATLAS_PREFS && window.ATLAS_PREFS.voice_name) || "";
    while (vSelect.options.length > 1) vSelect.remove(1);  // keep only "Automatic"
    // English voices only, excluding novelty/robotic ones.
    var en = voices.filter(function (v) {
      return (v.lang || "").toLowerCase().indexOf("en") === 0 && !NOVELTY.test(v.name || "");
    });
    en.sort(byName);
    en.forEach(function (v) {
      var o = document.createElement("option");
      o.value = v.name; o.textContent = friendly(v); vSelect.appendChild(o);
    });
    // pre-select the saved voice; fall back to "Automatic" if it's gone
    vSelect.value = current;
    if (vSelect.value !== current) vSelect.value = "";
  }

  if (ttsOk && vSelect) {
    populateVoices();
    try { window.speechSynthesis.addEventListener("voiceschanged", populateVoices); } catch (e) {}

    vSelect.addEventListener("change", function () {
      var name = vSelect.value;
      if (P && P.setValue) P.setValue("voice_name", name);   // persist like other prefs
      window.AtlasVoice.setVoiceName(name);                  // take effect immediately
    });

    if (vPreview) vPreview.addEventListener("click", function () {
      if (window.AtlasVoice.speaking && window.AtlasVoice.speaking()) {
        window.AtlasVoice.stop();                            // click again = cancel
        return;
      }
      if (!P || !P.voiceOn()) {                              // master voice off → hint
        if (vHint) { vHint.hidden = false; clearTimeout(vPreview._t);
          vPreview._t = setTimeout(function () { vHint.hidden = true; }, 2800); }
        return;
      }
      if (vHint) vHint.hidden = true;
      window.AtlasVoice.preview(vSelect.value);
    });
  }

  // ── THEME: 3 swatch cards reskin the shared frame live (persisted pref) ──
  var themePicker = document.getElementById("theme-picker");
  if (themePicker) {
    var THEMES = ["midnight", "parchment", "ocean"];
    var swatches = themePicker.querySelectorAll(".theme-swatch");
    var root = document.documentElement;

    function markSelected(name) {
      swatches.forEach(function (s) {
        var on = s.getAttribute("data-theme") === name;
        s.classList.toggle("selected", on);
        s.setAttribute("aria-checked", on ? "true" : "false");
      });
    }
    function applyTheme(name) {
      THEMES.forEach(function (t) { root.classList.remove("theme-" + t); });
      root.classList.add("theme-" + name);
    }

    var currentTheme = (window.ATLAS_PREFS && window.ATLAS_PREFS.theme) || "midnight";
    if (THEMES.indexOf(currentTheme) === -1) currentTheme = "midnight";
    markSelected(currentTheme);

    swatches.forEach(function (s) {
      s.addEventListener("click", function () {
        var name = s.getAttribute("data-theme");
        if (THEMES.indexOf(name) === -1) return;
        applyTheme(name);          // live, no reload
        markSelected(name);
        if (P && P.setValue) P.setValue("theme", name);   // persist like other prefs
        chime();
      });
    });
  }

  // ── ACCESSIBILITY: reduce motion ──
  var motion = document.getElementById("set-motion");
  var motionNote = document.getElementById("set-motion-note");
  if (motion) {
    if (P && P.osReduce) {              // OS forces it — reflect & lock the control
      motion.checked = true;
      motion.disabled = true;
      if (motionNote) motionNote.textContent = "On, forced by your system settings";
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

  // ── GAME: skip the guess-first hook prompts (presentation only, never gating) ──
  var skipHooks = document.getElementById("set-skip-hooks");
  if (skipHooks) skipHooks.addEventListener("change", function () {
    if (P) P.set("skip_hooks", skipHooks.checked);
  });

  // ── GAME: replay the how-to-play tutorial (reuse existing wiring) ──
  var replay = document.getElementById("set-replay");
  if (replay) replay.addEventListener("click", function () {
    close();
    var howto = document.getElementById("howto-btn");
    if (howto) setTimeout(function () { howto.click(); }, 320);
  });

  // ── GAME: replay the opening cinematic ──
  var replayIntro = document.getElementById("set-replay-intro");
  if (replayIntro) replayIntro.addEventListener("click", function () {
    close();
    setTimeout(function () {
      if (window.AtlasCinematic) window.AtlasCinematic.play();
    }, 320);
  });

  // ── Display name (leaderboard) ──
  // Not a pref: prefs live in the session and are wiped at login, whereas this is
  // a durable User column, so it POSTs to its own endpoint. A taken name comes
  // back as 409 with a message we show inline rather than failing silently.
  var nameInput = document.getElementById("set-display-name");
  var nameSave = document.getElementById("set-name-save");
  var nameMsg = document.getElementById("set-name-msg");

  function showNameMsg(text, ok) {
    if (!nameMsg) return;
    nameMsg.textContent = text;
    nameMsg.className = "set-name-msg " + (ok ? "is-ok" : "is-error");
    nameMsg.hidden = false;
  }

  if (nameInput && nameSave) {
    nameSave.addEventListener("click", function () {
      var value = (nameInput.value || "").trim();
      nameSave.disabled = true;
      fetch("/display-name", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: value }),
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (res.ok && res.d && res.d.ok) {
            nameInput.value = res.d.display_name;
            showNameMsg("Saved. This is the name shown on the leaderboard.", true);
          } else {
            showNameMsg((res.d && res.d.error) || "Could not save that name.", false);
          }
        })
        .catch(function () { showNameMsg("Could not save that name.", false); })
        .finally(function () { nameSave.disabled = false; });
    });
    nameInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); nameSave.click(); }
    });
  }
})();
