// ════════════════════════════════════════════════════════════════
//  AtlasHook — the guess-first "hook" beat shown BEFORE a lesson chunk.
//  A 5-second priming moment (pretesting effect): pose a curiosity
//  question, let the learner make a quick guess (or tap through), show a
//  one-line payoff, then continue into the content.
//
//  NOTHING here is logged, graded, or gating — tapping through is fine.
//  Shared by the Library, AI Lab and Observatory; each passes its own
//  accent so the card feels native. Respects the reduce-motion pref.
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
      '<div class="lh-hook-kicker">Before you begin — a quick guess</div>' +
      '<p class="lh-hook-q">' + esc(hook.question) + "</p>" +
      optsHtml +
      '<div class="lh-hook-payoff" hidden></div>' +
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

    var payoff = el.querySelector(".lh-hook-payoff");
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
      payoff.textContent = hook.payoff || "Hold that thought — let's find out.";
      payoff.hidden = false;
      cont.hidden = false;
      try { cont.focus(); } catch (e) {}
      // Auto-advance after a short beat so it never blocks; a tap is faster.
      if (!reduce) {
        el._timer = setTimeout(finish, 1600);
      }
    }

    optButtons.forEach(function (b) {
      b.addEventListener("click", function () { reveal(b); });
    });
    cont.addEventListener("click", function () {
      if (el._timer) clearTimeout(el._timer);
      finish();
    });

    return el;
  }

  window.AtlasHook = { mount: mount };
})();
