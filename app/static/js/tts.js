// ════════════════════════════════════════════════════════════════
//  AtlasVoice — "Read aloud" for taught lesson text.
//  Browser-local Web Speech API (window.speechSynthesis). No service,
//  no key, no backend. Reads the TAUGHT TEXT only (never quiz answers).
//  Exposes window.AtlasVoice.{speak, stop, toggle, supported}.
// ════════════════════════════════════════════════════════════════
(function () {
  var supported = "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";

  // ── voice selection (handles the async voiceschanged quirk) ──
  var chosenVoice = null;
  function pickVoice() {
    if (!supported) return null;
    var voices = window.speechSynthesis.getVoices() || [];
    if (!voices.length) return null;
    var prefer = function (test) { for (var i = 0; i < voices.length; i++) if (test(voices[i])) return voices[i]; return null; };
    chosenVoice =
      prefer(function (v) { return /en-GB/i.test(v.lang); }) ||
      prefer(function (v) { return /en-US/i.test(v.lang); }) ||
      prefer(function (v) { return /^en/i.test(v.lang); }) ||
      voices[0];
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
