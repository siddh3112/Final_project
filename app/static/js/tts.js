// ════════════════════════════════════════════════════════════════
//  AtlasVoice — "Read aloud" for taught lesson text.
//  Browser-local Web Speech API (window.speechSynthesis). No service,
//  no key, no backend. Reads the TAUGHT TEXT only (never quiz answers).
//  Exposes window.AtlasVoice.{speak, stop, toggle, supported}.
// ════════════════════════════════════════════════════════════════
(function () {
  var supported = "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";

  // ── voice selection: pick the most NATURAL English voice available ──
  // Quality depends on the OS's installed voices; we score them so the best
  // (Siri / Premium / Enhanced / Google) wins and the robotic/novelty ones lose.
  var chosenVoice = null;
  var GOOD_NAMES = ["samantha", "ava", "serena", "allison", "susan", "zoe", "kate",
    "stephanie", "alex", "daniel", "ryan", "aria", "jenny", "libby", "sonia", "natasha", "tom"];
  var BAD_NAMES = /compact|eloquence|fred|albert|zarvox|trinoids|whisper|bells|bad news|boing|bubbles|cellos|deranged|good news|jester|organ|superstar|wobble|bahh|bad|grandma|grandpa|reed|rocko|sandy|shelley/i;

  function scoreVoice(v) {
    var name = (v.name || "").toLowerCase();
    var lang = (v.lang || "").toLowerCase();
    if (lang.indexOf("en") !== 0) return -1;          // English only
    var s = 0;
    if (lang.indexOf("en-gb") === 0) s += 3;
    else if (lang.indexOf("en-us") === 0) s += 2;
    else s += 1;
    if (/premium|enhanced|natural|neural/.test(name)) s += 12; // downloadable HQ voices
    if (/siri/.test(name)) s += 11;
    if (/google/.test(name)) s += 8;                  // Chrome's voices are much nicer
    if (GOOD_NAMES.some(function (g) { return name.indexOf(g) !== -1; })) s += 5;
    if (BAD_NAMES.test(name)) s -= 15;                // novelty / low-quality voices
    if (v.localService === false) s += 1;             // often the higher-quality ones
    return s;
  }

  function pickVoice() {
    if (!supported) return null;
    var voices = window.speechSynthesis.getVoices() || [];
    if (!voices.length) return null;
    // honour a saved user choice if it still exists
    try {
      var saved = localStorage.getItem("atlas_voice");
      if (saved) {
        for (var k = 0; k < voices.length; k++) if (voices[k].name === saved) { chosenVoice = voices[k]; return chosenVoice; }
      }
    } catch (e) {}
    var best = null, bestScore = -Infinity;
    for (var i = 0; i < voices.length; i++) {
      var sc = scoreVoice(voices[i]);
      if (sc > bestScore) { bestScore = sc; best = voices[i]; }
    }
    chosenVoice = best || voices[0];
    return chosenVoice;
  }
  if (supported) {
    pickVoice();
    // voices are often empty on first call — grab them when they load
    try { window.speechSynthesis.addEventListener("voiceschanged", pickVoice, { once: false }); } catch (e) {}
  }

  function plainText(text) {
    if (text == null) return "";
    // strip HTML tags, collapse whitespace
    var tmp = document.createElement("div");
    tmp.innerHTML = String(text);
    var out = tmp.textContent || tmp.innerText || "";
    return out.replace(/\s+/g, " ").trim();
  }

  // The button currently showing a "speaking" state, so we can revert it.
  var activeBtn = null;
  function markSpeaking(btn, accent) {
    activeBtn = btn || null;
    if (!btn) return;
    btn.classList.add("speaking");
    if (accent) btn.style.setProperty("--tts-accent", accent);
    var icon = btn.querySelector("i");
    if (icon) { icon.className = icon.className.replace("bi-volume-up", "bi-volume-mute"); }
    btn.setAttribute("aria-pressed", "true");
  }
  function clearSpeaking() {
    var btn = activeBtn; activeBtn = null;
    if (!btn) return;
    btn.classList.remove("speaking");
    var icon = btn.querySelector("i");
    if (icon) { icon.className = icon.className.replace("bi-volume-mute", "bi-volume-up"); }
    btn.setAttribute("aria-pressed", "false");
  }

  function isSpeaking() {
    return supported && (window.speechSynthesis.speaking || window.speechSynthesis.pending);
  }

  function stop() {
    if (!supported) return;
    try { window.speechSynthesis.cancel(); } catch (e) {}
    clearSpeaking();
  }

  // speak(text, accentColor, btn) — btn is optional (the button to show state on).
  function speak(text, accentColor, btn) {
    if (!supported) return;
    var say = plainText(text);
    if (!say) return;
    stop(); // only one thing speaks at a time

    var u = new SpeechSynthesisUtterance(say);
    u.rate = 0.95; u.pitch = 1.0; u.volume = 1.0;
    var v = chosenVoice || pickVoice();
    if (v) { u.voice = v; u.lang = v.lang; }
    u.onend = clearSpeaking;
    u.onerror = clearSpeaking;
    markSpeaking(btn, accentColor);
    try { window.speechSynthesis.speak(u); } catch (e) { clearSpeaking(); }
  }

  // toggle(text, accentColor, btn) — speak if idle, stop if this button is speaking.
  function toggle(text, accentColor, btn) {
    if (!supported) return;
    // If something is speaking, stop. If it was THIS button, we're done (toggle off).
    var wasThis = activeBtn === btn && isSpeaking();
    if (isSpeaking()) { stop(); if (wasThis) return; }
    speak(text, accentColor, btn);
  }

  // Factory: a ready-styled "Read aloud" button (or null if unsupported, so
  // callers simply don't add it in browsers without speechSynthesis).
  function makeButton(accent) {
    if (!supported) return null;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tts-btn";
    b.setAttribute("aria-label", "Read aloud");
    b.setAttribute("title", "Read aloud");
    b.setAttribute("aria-pressed", "false");
    if (accent) b.style.setProperty("--tts-accent", accent);
    b.innerHTML = '<i class="bi bi-volume-up"></i>';
    return b;
  }

  window.AtlasVoice = { speak: speak, stop: stop, toggle: toggle, button: makeButton, supported: supported };

  // Safety net: stop speech if the page is hidden/unloaded.
  window.addEventListener("pagehide", stop);
  document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); });
})();
