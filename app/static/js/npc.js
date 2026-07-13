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

  function openChat() {
    if (window.AtlasVoice) window.AtlasVoice.stop(); // don't let a lesson read-aloud overlap Atlas
    chat.hidden = false;
    widget.classList.add("open");
    if (window.LibFX) window.LibFX.atlasChime();
    setTimeout(() => input.focus(), 50);
  }
  function closeChat() {
    chat.hidden = true;
    widget.classList.remove("open");
  }

  launcher.addEventListener("click", openChat);
  closeBtn.addEventListener("click", closeChat);

  // ── One-time arrival attention cue (presentation only) ──
  // Briefly draw the eye to the tutor button the first time a game-condition
  // learner lands on a location this session, then settle to normal. This lives
  // inside npc.js, which is loaded ONLY for the game condition and returns early
  // above if the widget is absent — so control users never see the cue.
  (function arrivalCue() {
    if (!chat.hidden) return; // chat already open (shouldn't happen on fresh load)
    try {
      if (sessionStorage.getItem("atlasCueShown")) return; // first location visit per session
      sessionStorage.setItem("atlasCueShown", "1");
    } catch (e) { /* private mode: just play it once here */ }

    const reduceMotion =
      (window.ATLAS_PREFS && window.ATLAS_PREFS.reduce_motion) ||
      document.documentElement.classList.contains("reduce-motion") ||
      (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

    // A small, dismissible, non-blocking hint label above the button.
    const tip = document.createElement("div");
    tip.className = "atlas-cue-tip";
    tip.textContent = "Need a hint? Ask Professor Atlas";
    tip.setAttribute("role", "status");
    widget.appendChild(tip);

    const timers = [];
    function dismissCue() {
      launcher.classList.remove("atlas-cue");
      tip.classList.remove("show");
      timers.forEach(clearTimeout);
      setTimeout(function () { if (tip.parentNode) tip.remove(); }, 350);
    }
    tip.addEventListener("click", dismissCue);
    // Opening the chat cancels the cue immediately.
    launcher.addEventListener("click", dismissCue, { once: true });

    // Fade the label in shortly after arrival.
    timers.push(setTimeout(function () { tip.classList.add("show"); }, 400));
    // Pulse the button a couple of times — skipped for reduced-motion users.
    if (!reduceMotion) {
      launcher.classList.add("atlas-cue");
      timers.push(setTimeout(function () { launcher.classList.remove("atlas-cue"); }, 2000));
    }
    // Settle back to normal after a couple of seconds.
    timers.push(setTimeout(dismissCue, 2600));
  })();

  function addMessage(text, who) {
    const el = document.createElement("div");
    el.className = "atlas-msg atlas-msg-" + who;
    el.textContent = text;
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
      addMessage(data.response || "…the Professor seems distracted. Try again.", "bot");
    } catch (err) {
      typing.remove();
      addMessage("…a connection to the Professor could not be made.", "bot");
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });
})();
