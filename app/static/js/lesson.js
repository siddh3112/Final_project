// Paged lesson journey + Trial unlock — vanilla JS, no framework.
(function () {
  const cards = Array.from(document.querySelectorAll(".lesson-card"));
  if (!cards.length) return;

  const total = cards.length;
  const curEl = document.getElementById("lesson-cur");
  const fillEl = document.getElementById("lesson-fill");
  const prevBtn = document.getElementById("lesson-prev");
  const nextBtn = document.getElementById("lesson-next");
  const stage = document.getElementById("lesson-stage");

  const trialGate = document.getElementById("trial-gate");
  const trialContent = document.getElementById("trial-content");
  const trialStage = document.getElementById("trial-stage");

  let idx = 0;
  let trialUnlocked = false;

  function render() {
    cards.forEach((c, i) => c.classList.toggle("active", i === idx));
    curEl.textContent = idx + 1;
    fillEl.style.width = ((idx + 1) / total) * 100 + "%";

    prevBtn.disabled = idx === 0;

    if (idx === total - 1) {
      nextBtn.innerHTML = trialUnlocked
        ? 'Go to Trial <i class="bi bi-arrow-down"></i>'
        : 'Begin the Trial <i class="bi bi-unlock-fill"></i>';
      nextBtn.classList.add("to-trial");
    } else {
      nextBtn.innerHTML = 'Next <i class="bi bi-chevron-right"></i>';
      nextBtn.classList.remove("to-trial");
    }
  }

  function unlockTrial() {
    if (!trialUnlocked) {
      trialUnlocked = true;
      trialGate.hidden = true;
      trialContent.hidden = false;
      trialStage.classList.add("unlocked");
    }
    trialStage.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  nextBtn.addEventListener("click", function () {
    if (idx < total - 1) {
      idx++;
      render();
      stage.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      unlockTrial();
    }
  });

  prevBtn.addEventListener("click", function () {
    if (idx > 0) {
      idx--;
      render();
      stage.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  render();
})();
