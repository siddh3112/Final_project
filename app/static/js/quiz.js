// ════════════════════════════════════════════════════════════════
//  The Trial — one question at a time, instant feedback, auto-advance,
//  floating +XP, a per-question "Ask Professor Atlas" hint, and (the Chronicle)
//  drag/keyboard "Broken Timeline" ordering items. Grading is server-side; the
//  answer key / correct sequence is NEVER in the DOM — the client asks /answer,
//  which reveals the truth only after the (locked) first commit.
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
  const attemptId = form.dataset.attempt || "";
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

  // Floating "+25 XP" that rises and fades from the chosen element.
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

  function advance() {
    if (idx < total - 1) {
      idx++;
      show();
    } else {
      form.submit(); // server grades + records, then shows results
    }
  }

  // Shared: reveal the per-question feedback panel, then wait for Continue.
  function revealFeedback(q, known, isRight, feedbackText) {
    const fb = q.querySelector(".q-feedback");
    if (!fb) { setTimeout(advance, 1500); return; }
    const txt = fb.querySelector(".q-feedback-text");
    if (txt) txt.textContent = known ? feedbackText : "Answer recorded.";
    fb.classList.toggle("is-ok", known && isRight);
    fb.classList.toggle("is-no", known && !isRight);
    fb.hidden = false;
    const nextBtn = fb.querySelector(".q-next-btn");
    if (nextBtn) {
      nextBtn.textContent = idx < total - 1 ? "Continue" : "See results";
      nextBtn.focus();
      nextBtn.addEventListener("click", advance, { once: true });
    }
  }

  // ── MCQ answer: instant green/red feedback + elaborative explanation. ──
  async function answer(q, opt) {
    if (locked) return;
    locked = true;

    const chosenInput = opt.querySelector("input");
    chosenInput.checked = true; // the committed answer is the one that gets graded
    const chosen = chosenInput.value;
    const opts = Array.from(q.querySelectorAll(".q-option"));
    // Data-level lock immediately: once committed, no switching to another option.
    opts.forEach((o) => {
      o.classList.add("locked");
      if (o !== opt) o.querySelector("input").disabled = true;
    });

    // Ask the SERVER whether it was right. The answer key is NOT in the DOM; the
    // server records this (first) commit and returns the correct letter + feedback.
    let isRight = false, correctLetter = null, feedback = "", known = false;
    try {
      const res = await fetch("/location/" + encodeURIComponent(location) + "/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attempt_id: attemptId, qkey: q.dataset.qkey, letter: chosen }),
      });
      if (res.ok) {
        const d = await res.json();
        isRight = !!d.is_correct; correctLetter = d.correct; feedback = d.feedback || ""; known = true;
      }
    } catch (e) {}

    if (known && correctLetter != null) {
      opts.forEach((o) => { if (o.querySelector("input").value === correctLetter) o.classList.add("correct"); });
      if (isRight) { opt.classList.add("flash-ok"); floatXP(opt); }
      else { opt.classList.add("flash-no", "shake"); }
    }
    revealFeedback(q, known, isRight, feedback);
  }

  // ── Broken Timeline (ordering item): drag or the ▲/▼ buttons to reorder, then
  //    "Seal this record" commits the arranged sequence. The correct order is not
  //    in the DOM; the server returns it only after this first commit is locked. ──
  function wireOrder(q) {
    const rail = q.querySelector(".order-rail");
    const valueEl = q.querySelector(".order-value");
    const confirmBtn = q.querySelector(".order-confirm");
    if (!rail || !confirmBtn) return;
    let itemLocked = false;

    const chips = () => Array.from(rail.querySelectorAll(".order-chip"));
    const sync = () => { if (valueEl) valueEl.value = chips().map((c) => c.dataset.ev).join(","); };
    sync(); // initialise the hidden value to the shuffled order

    // ▲/▼ buttons — keyboard-accessible reordering (the keyboard fallback).
    rail.addEventListener("click", function (e) {
      if (itemLocked) return;
      const btn = e.target.closest(".order-move");
      if (!btn) return;
      const chip = btn.closest(".order-chip");
      if (btn.classList.contains("order-up") && chip.previousElementSibling) {
        rail.insertBefore(chip, chip.previousElementSibling);
      } else if (btn.classList.contains("order-down") && chip.nextElementSibling) {
        rail.insertBefore(chip.nextElementSibling, chip);
      }
      sync();
      chip.focus();
    });

    // Pointer drag reordering.
    let dragEl = null;
    rail.addEventListener("dragstart", function (e) {
      if (itemLocked) { e.preventDefault(); return; }
      dragEl = e.target.closest(".order-chip");
      if (dragEl) dragEl.classList.add("dragging");
    });
    rail.addEventListener("dragend", function () {
      if (dragEl) dragEl.classList.remove("dragging");
      dragEl = null; sync();
    });
    rail.addEventListener("dragover", function (e) {
      if (itemLocked || !dragEl) return;
      e.preventDefault();
      const after = chips().filter((c) => c !== dragEl).find((c) => {
        const box = c.getBoundingClientRect();
        return e.clientY < box.top + box.height / 2;
      });
      if (after) rail.insertBefore(dragEl, after);
      else rail.appendChild(dragEl);
    });

    confirmBtn.addEventListener("click", async function () {
      if (itemLocked) return;
      itemLocked = true; locked = true;
      sync();
      const order = valueEl ? valueEl.value : "";
      chips().forEach((c) => { c.setAttribute("draggable", "false"); c.classList.add("locked"); });
      q.querySelectorAll(".order-move").forEach((b) => (b.disabled = true));
      confirmBtn.disabled = true;

      let known = false, isRight = false, feedback = "", correctOrder = null;
      try {
        const res = await fetch("/location/" + encodeURIComponent(location) + "/answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ attempt_id: attemptId, qkey: q.dataset.qkey, order: order }),
        });
        if (res.ok) {
          const d = await res.json();
          known = true; isRight = !!d.is_correct; feedback = d.feedback || ""; correctOrder = d.correct_order || null;
        }
      } catch (e) {}

      if (known && correctOrder) {
        // Re-form the rail into the TRUE order (post-commit reveal) and light it.
        const byId = {};
        chips().forEach((c) => (byId[c.dataset.ev] = c));
        correctOrder.split(",").forEach((id) => { if (byId[id]) rail.appendChild(byId[id]); });
        chips().forEach((c) => c.classList.add(isRight ? "ok" : "was"));
        rail.classList.add(isRight ? "order-solved" : "order-revealed");
        if (isRight) floatXP(confirmBtn);
      }
      revealFeedback(q, known, isRight, feedback);
    });
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
    if (q.dataset.kind === "order") {
      wireOrder(q);
    } else {
      q.querySelectorAll(".q-option").forEach((opt) => opt.addEventListener("click", () => answer(q, opt)));
    }
    wireHint(q);
  });

  show();
})();
