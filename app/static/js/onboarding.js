// Professor Atlas interactive onboarding — typewriter dialogue with Next/Back/Skip.
(function () {
  const box = document.getElementById("atlas-onboard");
  if (!box) return;

  let steps;
  try {
    steps = JSON.parse(document.getElementById("onboard-steps").textContent);
  } catch (e) {
    return;
  }
  if (!steps || !steps.length) return;

  const textEl = document.getElementById("onboard-text");
  const dots = Array.from(box.querySelectorAll(".onboard-dot"));
  const prev = document.getElementById("onboard-prev");
  const next = document.getElementById("onboard-next");
  const skip = document.getElementById("onboard-skip");

  let i = 0;
  let typing = false;
  let timer = null;

  function type(str) {
    clearInterval(timer);
    textEl.textContent = "";
    let n = 0;
    typing = true;
    box.classList.add("is-typing");
    timer = setInterval(function () {
      n++;
      textEl.textContent = str.slice(0, n);
      if (n >= str.length) {
        clearInterval(timer);
        typing = false;
        box.classList.remove("is-typing");
      }
    }, 16);
  }

  function finishTyping(str) {
    clearInterval(timer);
    textEl.textContent = str;
    typing = false;
    box.classList.remove("is-typing");
  }

  function render() {
    type(steps[i]);
    dots.forEach((d, k) => d.classList.toggle("active", k === i));
    prev.disabled = i === 0;
    next.textContent = i === steps.length - 1 ? "Let's begin!" : "Next";
  }

  function close() {
    clearInterval(timer);
    box.classList.add("closing");
    document.body.style.overflow = "";
    document.dispatchEvent(new Event("atlas:onboard-done"));
    setTimeout(function () {
      box.hidden = true;
      box.style.display = "none";
    }, 400);
  }

  next.addEventListener("click", function () {
    if (typing) {
      finishTyping(steps[i]);
      return;
    }
    if (i < steps.length - 1) {
      i++;
      render();
    } else {
      close();
    }
  });

  prev.addEventListener("click", function () {
    if (typing) {
      finishTyping(steps[i]);
      return;
    }
    if (i > 0) {
      i--;
      render();
    }
  });

  skip.addEventListener("click", close);

  document.body.style.overflow = "hidden"; // focus on Atlas while he speaks
  render();
})();
