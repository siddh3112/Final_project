// ════════════════════════════════════════════════════════════════
//  The Trial — one question at a time, instant feedback, auto-advance,
//  floating +XP, and a per-question "Ask Professor Atlas" hint.
// ════════════════════════════════════════════════════════════════
(function () {
  const form = document.getElementById("quiz-form");
  if (!form) return;

  const questions = Array.from(form.querySelectorAll(".quiz-question"));
  if (!questions.length) return;

  const total = questions.length;
  const curEl = document.getElementById("q-cur");
  const fillEl = document.getElementById("q-fill");
  const consultedEl = document.getElementById("consulted");
  const location = form.dataset.location || "";
  const XP_PER = 25;

  let idx = 0;
  let locked = false;
  const consulted = new Set(); // question keys the user took a hint on

  function show() {
    questions.forEach((q, i) => q.classList.toggle("active", i === idx));
    if (curEl) curEl.textContent = idx + 1;
    if (fillEl) fillEl.style.width = ((idx + 1) / total) * 100 + "%";
    locked = false;
  }

  // Floating "+25 XP" that rises and fades from the chosen option.
  function floatXP(target) {
    const el = document.createElement("div");
    el.className = "xp-float";
    el.textContent = "+" + XP_PER + " XP";
    const r = target.getBoundingClientRect();
    el.style.left = r.left + r.width / 2 + "px";
    el.style.top = r.top + "px";
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1400);
  }

  // Answer a question: instant green/red feedback, then auto-advance.
  function answer(q, opt) {
    if (locked) return;
    locked = true;

    const correct = q.dataset.correct;
    const opts = Array.from(q.querySelectorAll(".q-option"));
    opts.forEach((o) => {
      o.classList.add("locked");
      if (o.querySelector("input").value === correct) o.classList.add("correct");
    });

    if (opt.querySelector("input").value === correct) {
      opt.classList.add("flash-ok");
      floatXP(opt);
    } else {
      opt.classList.add("flash-no", "shake");
    }

    setTimeout(function () {
      if (idx < total - 1) {
        idx++;
        show();
      } else {
        form.submit(); // server grades + records, then shows results
      }
    }, 1500);
  }

  // Per-question hint → Professor Atlas (logged as consulted for this question).
  function wireHint(q) {
    const btn = q.querySelector(".hint-btn");
    if (!btn) return;
    const box = q.querySelector(".hint-box");
    const textEl = box ? box.querySelector(".hint-text") : null;

    btn.addEventListener("click", async function () {
      const qkey = q.dataset.qkey;
      consulted.add(qkey);
      if (consultedEl) consultedEl.value = Array.from(consulted).join(",");

      if (box) box.hidden = false;
      if (textEl) textEl.textContent = "Professor Atlas ponders…";
      btn.disabled = true;

      try {
        const res = await fetch("/npc/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: "Give me a hint for this question without revealing the answer: " + q.dataset.question,
            location: location,
          }),
        });
        const data = await res.json();
        // Use Atlas's live (Granite) reply only if it's a real, non-fallback answer;
        // otherwise fall back to the authored Socratic hint for this question.
        const useAtlas = data && data.response && !data.is_fallback;
        const fallbackHint = q.dataset.hint || "Consider what the question is really testing — rule out the options that don't fit.";
        if (textEl) textEl.textContent = useAtlas ? data.response : fallbackHint;
      } catch (e) {
        if (textEl) textEl.textContent = q.dataset.hint || "Consider what the question is really testing — rule out the options that don't fit.";
      } finally {
        btn.innerHTML = '<span class="hint-owl"><span class="atlas-glyph" aria-hidden="true"></span></span> Hint given';
        btn.disabled = false;
      }
    });
  }

  questions.forEach(function (q) {
    q.querySelectorAll(".q-option").forEach((opt) => opt.addEventListener("click", () => answer(q, opt)));
    wireHint(q);
  });

  show();
})();
