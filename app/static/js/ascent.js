// ════════════════════════════════════════════════════════════════
//  The Final Ascent — cinematic 4-act capstone for the post-test.
//  Drives (a) the one-question-at-a-time chapter flow, and (b) the
//  results reveal (score count-up + Atlas Sage unlock + seal + review).
//  This page is intentionally SILENT — no sound effects. No Professor Atlas.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  var reduce = (window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches) ||
    (window.ATLAS_PREFS && window.ATLAS_PREFS.reduce_motion === true);

  // ════════════════════════════════════════════════════════════════
  //  (A) THE ASCENT FLOW — instructions → Back/Forward questions → submit.
  //  No auto-advance; answers are editable; option order is stable (single
  //  server render); total + per-question time logged silently.
  // ════════════════════════════════════════════════════════════════
  function initFlow() {
    var form = document.getElementById("ascent-form");
    if (!form) return;

    var all = Array.prototype.slice.call(form.querySelectorAll("[data-step]"));
    var intro = all.filter(function (s) { return s.getAttribute("data-step") === "intro"; })[0];
    var questions = all.filter(function (s) { return s.getAttribute("data-step") === "question"; });
    var chapterCards = {};
    all.forEach(function (s) {
      if (s.getAttribute("data-step") === "chapter") chapterCards[s.getAttribute("data-chapter")] = s;
    });
    var railNodes = Array.prototype.slice.call(document.querySelectorAll("#ascent-rail .rail-node"));
    var nav = document.getElementById("ascent-nav");
    var backBtn = document.getElementById("asc-back");
    var nextBtn = document.getElementById("asc-next");
    var progressEl = document.getElementById("asc-nav-progress");
    var totalQ = questions.length;

    var answers = {};   // qkey -> chosen letter
    var perQ = {};      // qkey -> accumulated milliseconds
    var qIdx = -1;      // current question index (-1 before start)
    var startMs = 0, enterMs = 0;
    var cardTimer = null, cardArmed = false, submitting = false;

    function hideAll() { all.forEach(function (s) { s.hidden = true; }); }

    function accumulateCurrent() {
      if (qIdx >= 0 && enterMs) {
        var k = questions[qIdx].getAttribute("data-key");
        perQ[k] = (perQ[k] || 0) + (Date.now() - enterMs);
        enterMs = 0;
      }
    }

    function updateRail() {
      railNodes.forEach(function (n, i) {
        var q = questions[i];
        n.classList.toggle("filled", !!(q && answers[q.getAttribute("data-key")]));
        n.classList.toggle("current", i === qIdx);
      });
    }

    function restoreSelection(qEl) {
      var k = qEl.getAttribute("data-key");
      var chosen = answers[k];
      var input = qEl.querySelector('input[type="hidden"]');
      if (input) input.value = chosen || "";
      Array.prototype.forEach.call(qEl.querySelectorAll(".ascent-opt"), function (o) {
        o.classList.toggle("chosen", o.getAttribute("data-letter") === chosen);
      });
    }

    function showQuestion(i) {
      accumulateCurrent();
      qIdx = i;
      hideAll();
      var q = questions[i];
      q.hidden = false;
      q.classList.remove("q-in");
      void q.offsetWidth;
      if (!reduce) q.classList.add("q-in");
      restoreSelection(q);

      nav.hidden = false;
      backBtn.style.visibility = (i === 0) ? "hidden" : "visible";
      var last = (i === totalQ - 1);
      nextBtn.innerHTML = last
        ? 'Submit<i class="bi bi-check2 ms-1"></i>'
        : 'Next<i class="bi bi-arrow-right ms-1"></i>';
      nextBtn.classList.toggle("is-submit", last);
      if (progressEl) progressEl.textContent = "Question " + (i + 1) + " of " + totalQ;
      updateRail();
      window.scrollTo(0, 0);
      enterMs = Date.now();
    }

    // Show a chapter card (forward crossing only), then the pending question.
    function showChapterThen(chNum, qi) {
      accumulateCurrent();
      hideAll();
      nav.hidden = true;
      var card = chapterCards[chNum];
      if (!card) { showQuestion(qi); return; }
      card.hidden = false;
      window.scrollTo(0, 0);
      cardArmed = true;
      var proceed = function () {
        if (!cardArmed) return;
        cardArmed = false;
        if (cardTimer) { clearTimeout(cardTimer); cardTimer = null; }
        card._proceed = null;
        showQuestion(qi);
      };
      card.onclick = proceed;
      card._proceed = proceed;
      if (!reduce) cardTimer = setTimeout(proceed, 2500);
    }

    function goForward() {
      if (qIdx < 0) return;
      if (qIdx >= totalQ - 1) { doSubmit(); return; }
      var curCh = questions[qIdx].getAttribute("data-chapter");
      var nextCh = questions[qIdx + 1].getAttribute("data-chapter");
      if (nextCh !== curCh) showChapterThen(nextCh, qIdx + 1);  // crossing into a new chapter
      else showQuestion(qIdx + 1);
    }
    function goBack() { if (qIdx > 0) showQuestion(qIdx - 1); }  // no chapter card going back

    function start() {
      startMs = Date.now();
      showChapterThen(questions[0].getAttribute("data-chapter"), 0);
    }

    function doSubmit() {
      accumulateCurrent();
      if (submitting) return;
      var unanswered = questions.filter(function (q) { return !answers[q.getAttribute("data-key")]; }).length;
      if (unanswered > 0) {
        var ok = window.confirm("You have " + unanswered + " unanswered question" +
          (unanswered > 1 ? "s" : "") + ". Submit anyway?");
        if (!ok) { enterMs = Date.now(); return; }  // stay put, keep timing
      }
      submitting = true;
      var totalSec = Math.round((Date.now() - startMs) / 1000);
      var tf = form.querySelector('input[name="time_spent_seconds"]');
      if (tf) tf.value = totalSec;
      var pq = {};
      Object.keys(perQ).forEach(function (k) { pq[k] = Math.round(perQ[k] / 1000); });
      var pf = form.querySelector('input[name="per_question_seconds"]');
      if (pf) pf.value = JSON.stringify(pq);
      form.submit();  // scoring/saving happen server-side, unchanged
    }

    // Option selection — marks the answer; does NOT advance.
    questions.forEach(function (q) {
      var input = q.querySelector('input[type="hidden"]');
      var opts = Array.prototype.slice.call(q.querySelectorAll(".ascent-opt"));
      opts.forEach(function (opt) {
        opt.addEventListener("click", function () {
          var k = q.getAttribute("data-key");
          answers[k] = opt.getAttribute("data-letter");  // stable identity for grading
          if (input) input.value = answers[k];
          opts.forEach(function (o) { o.classList.toggle("chosen", o === opt); });
          updateRail();
        });
      });
    });

    var beginBtn = form.querySelector("[data-advance]");
    if (beginBtn) beginBtn.addEventListener("click", start);
    backBtn.addEventListener("click", goBack);
    nextBtn.addEventListener("click", goForward);

    // Enter advances the intro / chapter cards only (never a question).
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      var openCard = null;
      Object.keys(chapterCards).forEach(function (k) {
        if (!chapterCards[k].hidden) openCard = chapterCards[k];
      });
      if (openCard && openCard._proceed) { e.preventDefault(); openCard._proceed(); return; }
      if (intro && !intro.hidden && beginBtn) { e.preventDefault(); beginBtn.click(); }
    });

    // Initial state: instructions only.
    hideAll();
    if (intro) intro.hidden = false;
    if (nav) nav.hidden = true;
  }

  // ════════════════════════════════════════════════════════════════
  //  (B) THE RESULTS REVEAL
  // ════════════════════════════════════════════════════════════════
  function initResults() {
    var root = document.getElementById("ascent-results");
    if (!root) return;

    var score = parseInt(root.getAttribute("data-score"), 10) || 0;
    var xp = parseInt(root.getAttribute("data-xp"), 10) || 0;

    var calc = document.getElementById("rv-calc");
    var stage = document.getElementById("rv-stage");
    var scoreNum = document.getElementById("rv-score-num");
    var sage = document.getElementById("rv-sage");
    var xpNum = document.getElementById("rv-xp-num");
    var seal = document.getElementById("rv-seal");
    var pb = document.getElementById("rv-pb");
    var isPB = root.getAttribute("data-pb") === "1";
    var passed = root.getAttribute("data-passed") === "1";
    var actions = document.getElementById("rv-actions");

    // Frame-based count-up: caps the number of ticks so a large XP total
    // (e.g. 0 → 300) finishes in ~0.7s, while a small score (0 → 10) still
    // ticks one-by-one.
    function countTo(el, target, cb) {
      target = target || 0;
      if (target <= 0) { el.textContent = "0"; if (cb) setTimeout(cb, reduce ? 60 : 160); return; }
      var frames = Math.min(target, 24);
      var dur = reduce ? 160 : 700;
      var stepMs = Math.max(reduce ? 16 : 28, Math.round(dur / frames));
      var i = 0;
      var step = function () {
        i++;
        el.textContent = (i >= frames) ? target : Math.round(target * i / frames);
        if (i < frames) setTimeout(step, stepMs);
        else if (cb) setTimeout(cb, reduce ? 90 : 320);
      };
      setTimeout(step, reduce ? 30 : 120);
    }

    function particles(hostId) {
      var host = document.getElementById(hostId || "rv-particles");
      if (!host || reduce) return;
      for (var i = 0; i < 28; i++) {
        var ang = (Math.PI * 2 / 28) * i, d = 90 + Math.random() * 120;
        var s = document.createElement("span");
        s.className = "rv-spark";
        s.style.setProperty("--dx", (Math.cos(ang) * d).toFixed(0) + "px");
        s.style.setProperty("--dy", (Math.sin(ang) * d).toFixed(0) + "px");
        s.style.animationDelay = (Math.random() * 0.12).toFixed(2) + "s";
        host.appendChild(s);
      }
    }

    function showPB() {
      if (!pb) return;
      pb.hidden = false;
      if (isPB) particles("rv-pb-particles");  // visual only (page is silent)
    }

    // Reveal the action row (Return / View your review / certificate). The full
    // per-question review is a separate page, opened via "View your review".
    // On a passing run, signal the epilogue that the sequence is complete.
    function finish(withEpilogue) {
      if (actions) actions.hidden = false;
      if (withEpilogue) document.dispatchEvent(new Event("ascent:reveal-done"));
    }

    function runSage() {
      sage.hidden = false;
      particles();
      countTo(xpNum, xp, function () {
        seal.hidden = false;
        setTimeout(showPB, reduce ? 100 : 700);
        setTimeout(function () { finish(true); }, reduce ? 220 : 1500);
      });
    }

    // Below the pass mark: skip the Atlas Sage celebration; show the retake
    // prompt (already in the DOM) then the action row.
    function runFail() {
      var fail = document.getElementById("rv-fail");
      if (fail) fail.hidden = false;
      setTimeout(function () { finish(false); }, reduce ? 200 : 900);
    }

    function runScore() {
      stage.hidden = false;
      countTo(scoreNum, score, passed ? runSage : runFail);
    }

    setTimeout(function () {
      if (calc) calc.hidden = true;
      runScore();
    }, reduce ? 300 : 1000);
  }

  // Boot whichever page we're on — exactly once.
  var booted = false;
  function boot() {
    if (booted) return;
    booted = true;
    initFlow();
    initResults();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
