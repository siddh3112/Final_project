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
