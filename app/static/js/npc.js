// Professor Atlas — floating tutor widget (bottom-right). Talks to /npc/chat.
(function () {
  const widget = document.getElementById("atlas-widget");
  if (!widget) return; // control condition: no widget

  const location = widget.dataset.location;
  const chat = document.getElementById("atlas-chat");
  const launcher = document.getElementById("atlas-launcher");
  const closeBtn = document.getElementById("atlas-close");
  const log = document.getElementById("atlas-log");
  const form = document.getElementById("atlas-form");
  const input = document.getElementById("atlas-input");
  const sendBtn = document.getElementById("atlas-send");

  function openChat(opts) {
    opts = opts || {};
    if (window.AtlasVoice) window.AtlasVoice.stop(); // don't let a lesson read-aloud overlap Atlas
    chat.hidden = false;
    chat.classList.remove("atlas-closing");
    widget.classList.add("open");
    if (!opts.silent && window.LibFX) window.LibFX.atlasChime();
    if (!opts.noFocus) setTimeout(() => input.focus(), 50);
  }
  function closeChat() {
    chat.classList.remove("atlas-closing");
    chat.hidden = true;
    widget.classList.remove("open");
  }
  function atlasReduceMotion() {
    return (
      (window.ATLAS_PREFS && window.ATLAS_PREFS.reduce_motion) ||
      document.documentElement.classList.contains("reduce-motion") ||
      (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)
    );
  }

  launcher.addEventListener("click", () => openChat());
  closeBtn.addEventListener("click", closeChat);

  // ── On-arrival: the Atlas panel AUTO-OPENS so the tutor is unmissable ──
  // Presentation/UX only. The panel opens exactly as if the learner opened it and
  // Atlas is already greeting (the panel's existing authored greeting sets the
  // "I give hints, not answers" expectation); it stays open for a few seconds, then
  // closes gracefully — UNLESS the learner engages with it, which cancels the
  // auto-close and leaves it open as a normal session. This NEVER calls the language
  // model and never touches /npc/chat, the guardrails, the unlock gate, or logging.
  // It REPLACES the old arrival speech-bubble, so there is no double announcement.
  //
  // Tunables:
  //   ATLAS_AUTO_OPEN_MS        — how long the panel stays open before auto-closing.
  //   ATLAS_AUTO_OPEN_FREQUENCY — "always" (every arrival, as now) or "session"
  //                               (first visit per location per browser session).
  const ATLAS_AUTO_OPEN_MS = 5000;
  const ATLAS_OPEN_DELAY_MS = 450;          // a brief beat after arrival before it opens
  const ATLAS_CLOSE_ANIM_MS = 260;          // graceful close duration (skipped under reduce-motion)
  const ATLAS_AUTO_OPEN_FREQUENCY = "always";

  function atlasAutoOpenKey() { return "atlas_auto_open_" + (location || "loc"); }
  function atlasShouldAutoOpen() {
    if (ATLAS_AUTO_OPEN_FREQUENCY !== "session") return true;
    try { return !sessionStorage.getItem(atlasAutoOpenKey()); } catch (e) { return true; }
  }
  function atlasMarkAutoOpened() {
    if (ATLAS_AUTO_OPEN_FREQUENCY !== "session") return;
    try { sessionStorage.setItem(atlasAutoOpenKey(), "1"); } catch (e) {}
  }

  (function arrivalAutoOpen() {
    if (!chat.hidden) return;            // already open — nothing to announce
    if (!atlasShouldAutoOpen()) return;  // frequency gate (e.g. once per session)

    let autoCloseTimer = null;
    let closeTimer = null;
    let engaged = false;

    // Any REAL interaction with the widget cancels the auto-close and keeps the
    // panel open as a normal session: clicking/tapping inside the panel, focusing
    // or typing in the input (focusin bubbles up from it), or clicking the owl. If
    // a graceful close is already animating, interrupt it and stay open — never
    // close the panel out from under someone who is interacting with it.
    function cancelAutoClose() {
      engaged = true;
      if (autoCloseTimer) { clearTimeout(autoCloseTimer); autoCloseTimer = null; }
      if (closeTimer) {
        clearTimeout(closeTimer); closeTimer = null;
        chat.classList.remove("atlas-closing");
        chat.hidden = false; widget.classList.add("open");
      }
    }
    widget.addEventListener("pointerdown", cancelAutoClose);
    widget.addEventListener("focusin", cancelAutoClose);

    function gracefulClose() {
      if (chat.hidden || engaged) return;
      if (atlasReduceMotion()) { closeChat(); return; }   // no motion: just disappear
      chat.classList.add("atlas-closing");
      closeTimer = setTimeout(function () {
        closeTimer = null;
        if (!engaged) closeChat();       // closeChat also clears .atlas-closing
      }, ATLAS_CLOSE_ANIM_MS);
    }

    function open() {
      if (engaged || !chat.hidden) return;         // learner already opened/engaged during the delay
      openChat({ silent: true, noFocus: true });   // no chime on load; don't steal focus (that would read as engagement)
      atlasMarkAutoOpened();
      autoCloseTimer = setTimeout(gracefulClose, ATLAS_AUTO_OPEN_MS);
    }

    setTimeout(open, ATLAS_OPEN_DELAY_MS);
  })();

  function addMessage(text, who, source) {
    const el = document.createElement("div");
    el.className = "atlas-msg atlas-msg-" + who;
    el.textContent = text;
    // On a real Atlas reply, label which engine produced it (keyed on the accurate
    // server `source`, never is_fallback, so a rule-based hint never reads as Granite).
    if (source) {
      const granite = source === "granite";
      const tag = document.createElement("span");
      tag.className = "atlas-msg-source src-" + (granite ? "granite" : "rules");
      tag.textContent = granite ? "Granite generated" : "System generated";
      el.appendChild(tag);
    }
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    input.value = "";
    sendBtn.disabled = true;
    const typing = addMessage("Professor Atlas is thinking…", "bot");
    typing.classList.add("typing");

    try {
      const res = await fetch("/npc/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, location: location }),
      });
      const data = await res.json();
      typing.remove();
      addMessage(data.response || "…the Professor seems distracted. Try again.", "bot",
                 data.response ? data.source : null);
    } catch (err) {
      typing.remove();
      addMessage("…a connection to the Professor could not be made.", "bot");
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });
})();
