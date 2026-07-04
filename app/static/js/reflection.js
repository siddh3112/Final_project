// ════════════════════════════════════════════════════════════════
//  Post-Trial reflection — a single-sentence generative-learning beat
//  shown once per location (after the celebration) when a Trial is passed.
//  UNGRADED and skippable; it only POSTs qualitative data to /location/
//  <key>/reflect and never blocks the learner from returning to the hub.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var card = document.getElementById("reflect-card");
  if (!card) return;

  var key = card.dataset.key;
  var input = document.getElementById("reflect-input");
  var submitBtn = document.getElementById("reflect-submit");
  var skipBtn = document.getElementById("reflect-skip");
  var doneEl = document.getElementById("reflect-done");
  var actions = card.querySelector(".reflect-actions");

  var P = window.AtlasPrefs;
  function reduce() { return P ? !!P.effective("reduce_motion") : false; }
  function soundOn() { return P ? P.soundOn() : true; }

  // Soft gold "sealed" chime (respects the sound preference).
  function chime() {
    if (!soundOn() || reduce()) return;
    try {
      var C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      var a = new C();
      [523.25, 659.25, 880.0].forEach(function (f, i) {
        var o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        var t = a.currentTime + i * 0.08;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.13, t + 0.03);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.5);
        o.connect(g); g.connect(a.destination);
        o.start(t); o.stop(t + 0.55);
      });
      setTimeout(function () { try { a.close(); } catch (e) {} }, 1100);
    } catch (e) {}
  }

  var sent = false;
  function send(skipped) {
    if (sent) return;
    sent = true;
    var response = skipped ? "" : (input.value || "").trim();
    try {
      fetch("/location/" + encodeURIComponent(key) + "/reflect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ response: response, skipped: skipped }),
        keepalive: true,
      });
    } catch (e) {}
  }

  function seal() {
    var text = (input.value || "").trim();
    if (!text) { skip(); return; }         // empty submit is treated as a skip
    send(false);
    if (actions) actions.hidden = true;
    input.disabled = true;
    if (!reduce) card.classList.add("reflect-sealed");
    if (doneEl) doneEl.hidden = false;
    chime();
  }

  function skip() {
    send(true);
    // Fade the whole card away — nothing blocks the return to the map.
    if (reduce) { card.hidden = true; return; }
    card.classList.add("reflect-dismiss");
    setTimeout(function () { card.hidden = true; }, 300);
  }

  submitBtn.addEventListener("click", seal);
  skipBtn.addEventListener("click", skip);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); seal(); }
  });

  // Reveal after the celebration has had its moment.
  var delay = reduce() ? 200 : 1400;
  setTimeout(function () {
    card.hidden = false;
    if (!reduce()) card.classList.add("reflect-in");
    try { input.focus({ preventScroll: true }); } catch (e) { try { input.focus(); } catch (e2) {} }
  }, delay);
})();
