// Apply data-driven layout values (kept out of inline style="" so the
// template stays valid HTML/CSS). Positions pins and the XP bar.
(function () {
  document.querySelectorAll(".map-pin[data-x]").forEach(function (pin) {
    pin.style.left = pin.dataset.x + "%";
    pin.style.top = pin.dataset.y + "%";
  });
  const xp = document.querySelector(".hud-bar-fill[data-pct]");
  if (xp) xp.style.width = xp.dataset.pct + "%";
})();

// Professor Atlas — focused game tutorial on the hub.
// Auto-shows on first visit; re-openable via the "How to Play" button.
// Atlas is "in focus" (overlay dims the map) only while he is speaking.
(function () {
  const overlay = document.getElementById("hub-onboard");
  if (!overlay) return;

  let steps;
  try {
    steps = JSON.parse(document.getElementById("hub-onboard-steps").textContent);
  } catch (e) {
    return;
  }
  if (!steps || !steps.length) return;

  const textEl = document.getElementById("hub-onboard-text");
  const dots = Array.from(overlay.querySelectorAll(".onboard-dot"));
  const prev = document.getElementById("hub-onboard-prev");
  const next = document.getElementById("hub-onboard-next");
  const skip = document.getElementById("hub-onboard-skip");
  const howto = document.getElementById("howto-btn");

  let i = 0;
  let typing = false;
  let timer = null;

  function type(str) {
    clearInterval(timer);
    textEl.textContent = "";
    let n = 0;
    typing = true;
    overlay.classList.add("is-typing");
    timer = setInterval(function () {
      n++;
      textEl.textContent = str.slice(0, n);
      if (n >= str.length) {
        clearInterval(timer);
        typing = false;
        overlay.classList.remove("is-typing");
      }
    }, 16);
  }

  function finishTyping(str) {
    clearInterval(timer);
    textEl.textContent = str;
    typing = false;
    overlay.classList.remove("is-typing");
  }

  function render() {
    type(steps[i]);
    dots.forEach((d, k) => d.classList.toggle("active", k === i));
    prev.disabled = i === 0;
    next.textContent = i === steps.length - 1 ? "Let's begin!" : "Next";
  }

  function show() {
    i = 0;
    overlay.hidden = false;
    overlay.classList.remove("closing");
    document.body.style.overflow = "hidden";
    render();
  }

  function close() {
    clearInterval(timer);
    overlay.classList.add("closing");
    document.body.style.overflow = "";
    setTimeout(function () {
      overlay.hidden = true;
      overlay.classList.remove("closing");
    }, 400);
  }

  next.addEventListener("click", function () {
    if (typing) return finishTyping(steps[i]);
    if (i < steps.length - 1) {
      i++;
      render();
    } else {
      close();
    }
  });
  prev.addEventListener("click", function () {
    if (typing) return finishTyping(steps[i]);
    if (i > 0) {
      i--;
      render();
    }
  });
  skip.addEventListener("click", close);
  if (howto) howto.addEventListener("click", show);

  // Auto-show once per USER (server decides via data-autoshow, from the
  // user's seen_intro flag) — not per browser, so shared machines work and
  // stale localStorage/session state can't suppress it.
  if (overlay.dataset.autoshow === "1") {
    // If the opening cinematic is about to play, let it finish first.
    if (window.ATLAS_CINEMATIC_PENDING) {
      document.addEventListener("atlas:cinematic-done", show, { once: true });
    } else {
      show();
    }
  }
})();
