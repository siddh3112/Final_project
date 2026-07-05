// ════════════════════════════════════════════════════════════════
//  Trial SKINS — per-location progress motif (presentation only).
//
//  This drives each realm's decorative progress indicator:
//    • Library    → illuminated folios I–IV light as you answer
//    • Chronicle  → a clock hand + arc sweep forward as entries are sealed
//    • Observatory→ a mini-constellation charts one star per answer
//
//  It only OBSERVES the graded flow (quiz.js) — it never grades, submits,
//  logs, or alters answers. It reacts to a question becoming answered
//  (quiz.js locks the options) and to the active question changing.
//  Respects prefers-reduced-motion. If anything is missing it no-ops.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var root = document.querySelector(".trial-skin");
  var form = document.getElementById("quiz-form");
  if (!root || !form) return;

  var skin = root.dataset.skin || "";
  var questions = Array.prototype.slice.call(form.querySelectorAll(".quiz-question"));
  var total = questions.length;
  if (!total) return;

  var P = window.AtlasPrefs;
  var REDUCE = !!((P && P.effective && P.effective("reduce_motion")) ||
    (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches));

  var motif = document.getElementById("tskin-motif");
  var answered = 0;               // questions answered so far
  var counted = {};               // guard: light each question's node once

  // ── Skin-specific painters ───────────────────────────────────────
  var folios = motif ? Array.prototype.slice.call(motif.querySelectorAll(".tskin-folio")) : [];
  var stars = motif ? Array.prototype.slice.call(motif.querySelectorAll(".tskin-star")) : [];
  var links = motif ? Array.prototype.slice.call(motif.querySelectorAll(".tskin-link")) : [];
  var clockHand = document.getElementById("tskin-clock-hand");
  var clockArc = document.getElementById("tskin-clock-arc");

  function paintNodes(nodes) {
    nodes.forEach(function (el, i) {
      el.classList.remove("charted", "current");
      if (i < answered) el.classList.add("charted");
      else if (i === answered) el.classList.add("current");
    });
  }

  // A filled-pie arc from 12 o'clock, clockwise, covering `frac` of the dial.
  function arcPath(frac, r) {
    if (frac <= 0) return "M60 60 Z";
    if (frac >= 1) frac = 0.9999;
    var a = frac * 2 * Math.PI - Math.PI / 2;   // start at top (−90°)
    var x = 60 + r * Math.cos(a), y = 60 + r * Math.sin(a);
    var large = frac > 0.5 ? 1 : 0;
    return "M60 60 L60 " + (60 - r) + " A" + r + " " + r + " 0 " + large + " 1 " + x.toFixed(2) + " " + y.toFixed(2) + " Z";
  }

  function paint() {
    if (skin === "library") {
      paintNodes(folios);
    } else if (skin === "observatory") {
      paintNodes(stars);
      links.forEach(function (ln) {
        var i = parseInt(ln.dataset.i, 10);   // link leads INTO star i
        ln.classList.toggle("drawn", i <= answered && i > 0 && (i - 1) < answered);
      });
    } else if (skin === "chronicle") {
      var frac = total ? answered / total : 0;
      if (clockHand) {
        var ang = frac * 360;
        clockHand.setAttribute("transform", "rotate(" + ang.toFixed(2) + " 60 60)");
      }
      if (clockArc) clockArc.setAttribute("d", arcPath(frac, 48));
    }
  }

  // ── React when a question gets answered (quiz.js locks its options) ──
  function markAnswered(q) {
    var i = parseInt(q.dataset.qindex, 10);
    if (counted[i]) return;
    counted[i] = true;
    answered = Math.min(answered + 1, total);
    if (root.classList) root.classList.add("tskin-answered-" + answered);
    if (REDUCE) { paint(); return; }
    paint();
    if (motif) { motif.classList.remove("tskin-pulse"); void motif.offsetWidth; motif.classList.add("tskin-pulse"); }
  }

  questions.forEach(function (q) {
    q.querySelectorAll(".q-option").forEach(function (opt) {
      opt.addEventListener("click", function () {
        // Let quiz.js apply its lock/feedback first, then reflect it.
        setTimeout(function () {
          if (q.querySelector(".q-option.locked")) markAnswered(q);
        }, 0);
      });
    });
  });

  paint();   // initial state: node 0 is "current"
})();
