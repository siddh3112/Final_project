// ════════════════════════════════════════════════════════════════
//  Atlas Quest — front-of-house preferences (audio / accessibility).
//  Reads window.ATLAS_PREFS (emitted by the server from the session),
//  applies the reduce-motion / large-text classes, and exposes
//  window.AtlasPrefs for the Settings panel to read & save.
//  Presentation only — never touches scoring or research data.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var prefs = window.ATLAS_PREFS || (window.ATLAS_PREFS = {});
  var root = document.documentElement;

  // The OS "reduce motion" setting forces reduce-motion ON regardless of choice.
  var osReduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function applyClasses() {
    root.classList.toggle("reduce-motion", !!prefs.reduce_motion || osReduce);
    root.classList.toggle("large-text", !!prefs.large_text);
  }
  applyClasses();

  function save(updates) {
    // Fire-and-forget; the session is the source of truth on next load.
    try {
      fetch("/prefs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
        keepalive: true,
      });
    } catch (e) {}
  }

  window.AtlasPrefs = {
    get: function (key) { return prefs[key]; },
    // Effective value: reduce_motion is also forced by the OS setting.
    effective: function (key) {
      if (key === "reduce_motion") return !!prefs.reduce_motion || osReduce;
      return prefs[key];
    },
    osReduce: osReduce,
    soundOn: function () { return prefs.sound !== false; },
    voiceOn: function () { return prefs.voice !== false; },
    set: function (key, value) {
      value = !!value;
      prefs[key] = value;
      applyClasses();
      var update = {};
      update[key] = value;
      save(update);
      document.dispatchEvent(new CustomEvent("atlas:prefchange", { detail: { key: key, value: value } }));
      return value;
    },
    // Like set(), but keeps the raw value (for string prefs such as voice_name).
    setValue: function (key, value) {
      prefs[key] = value;
      var update = {};
      update[key] = value;
      save(update);
      document.dispatchEvent(new CustomEvent("atlas:prefchange", { detail: { key: key, value: value } }));
      return value;
    },
  };
})();
