// ════════════════════════════════════════════════════════════════
//  AtlasHook — the guess-first "hook" beat shown BEFORE a lesson chunk.
//  A priming moment (pretesting effect): pose a curiosity question and let
//  the learner make a quick guess. After the guess, Professor Atlas replies
//  with a short AUTHORED insight (instant, never an LLM call) that sets up
//  the concept, then Continue carries on into the lesson. Guessing is the
//  primary action; a secondary "Skip" bypasses the hook with no insight.
//
//  NOTHING here is logged, graded, or gating — skipping or guessing changes
//  nothing about progression. Shared by all four learn scenes; each passes
//  its own accent so the card feels native. Respects reduce-motion. The
//  insight rides on hook.insight (authored in game_content.HOOKS); it falls
//  back to hook.payoff if a hook has none.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  function reduceMotion() {
    return !!(window.AtlasPrefs && window.AtlasPrefs.effective("reduce_motion"));
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // Build + mount a hook card into `host`. Calls opts.onContinue() once, when
  // the learner proceeds. Returns the element (self-removing on continue).
  //   hook: { question, options?[], payoff }
  //   opts: { accent, onContinue, label? }
  function mount(host, hook, opts) {
    opts = opts || {};
    // Global "skip guess prompts" preference: bypass the hook entirely and go
    // straight to the lesson. Presentation only, never logged or gating.
    if (window.AtlasPrefs && window.AtlasPrefs.effective && window.AtlasPrefs.effective("skip_hooks")) {
      if (typeof opts.onContinue === "function") opts.onContinue();
      return null;
    }
    var reduce = reduceMotion();
    var el = document.createElement("div");
    el.className = "lh-hook" + (reduce ? "" : " lh-in");
    if (opts.accent) el.style.setProperty("--hook-accent", opts.accent);

    var hasOptions = hook.options && hook.options.length;
    var optsHtml = "";
    if (hasOptions) {
      optsHtml = '<div class="lh-hook-opts">' +
        hook.options.map(function (o, i) {
          return '<button type="button" class="lh-hook-opt" data-i="' + i + '">' + esc(o) + "</button>";
        }).join("") + "</div>";
    } else {
      optsHtml = '<div class="lh-hook-opts"><button type="button" class="lh-hook-opt lh-hook-guess" data-i="0">Make your guess…</button></div>';
    }

    el.innerHTML =
      '<div class="lh-hook-inner">' +
      '<div class="lh-hook-kicker">Before you begin, a quick guess</div>' +
      '<p class="lh-hook-q">' + esc(hook.question) + "</p>" +
      optsHtml +
      '<button type="button" class="lh-hook-skip">Skip for now</button>' +
      '<div class="lh-hook-insight" hidden>' +
        '<span class="lh-hook-owl"><span class="atlas-glyph" aria-hidden="true"></span></span>' +
        '<div class="lh-hook-insight-body">' +
        '<span class="lh-hook-atlas">Professor Atlas</span>' +
        '<p class="lh-hook-insight-text"></p>' +
        "</div>" +
      "</div>" +
      '<button type="button" class="lh-hook-continue" hidden>Continue <span aria-hidden="true">→</span></button>' +
      "</div>";

    host.appendChild(el);

    var done = false;
    function finish() {
      if (done) return;
      done = true;
      var go = function () {
        if (el.parentNode) el.parentNode.removeChild(el);
        if (typeof opts.onContinue === "function") opts.onContinue();
      };
      if (reduce) { go(); return; }
      el.classList.add("lh-out");
      setTimeout(go, 260);
    }

    var insight = el.querySelector(".lh-hook-insight");
    var insightText = el.querySelector(".lh-hook-insight-text");
    var skip = el.querySelector(".lh-hook-skip");
    var cont = el.querySelector(".lh-hook-continue");
    var optButtons = Array.prototype.slice.call(el.querySelectorAll(".lh-hook-opt"));
    var guessed = false;

    function reveal(chosenBtn) {
      if (guessed) return;
      guessed = true;                       // records NOTHING — priming only
      optButtons.forEach(function (b) {
        b.disabled = true;
        if (b === chosenBtn) b.classList.add("lh-hook-picked");
      });
      if (skip) skip.hidden = true;         // a guess was made; skip is no longer offered
      // Professor Atlas responds to the guess with an authored insight (instant, no
      // LLM call) that sets up the concept; Continue then carries on into the lesson.
      insightText.textContent = hook.insight || hook.payoff || "Hold that thought. Let us find out.";
      insight.hidden = false;
      cont.hidden = false;
      // No auto-advance: let the learner read Atlas before moving on. Continue is
      // focused, so a click, Enter or Space flows naturally into the lesson.
      try { cont.focus(); } catch (e) {}
    }

    optButtons.forEach(function (b) {
      b.addEventListener("click", function () { reveal(b); });
    });
    if (skip) {
      // Deliberate, secondary bypass: leave WITHOUT guessing, so no insight shows.
      skip.addEventListener("click", function () { finish(); });
    }
    cont.addEventListener("click", function () { finish(); });

    return el;
  }

  window.AtlasHook = { mount: mount };
})();
