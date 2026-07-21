// ════════════════════════════════════════════════════════════════
//  Confirmation for "Start a New Run".
//
//  Starting a replay re-locks all four locations, so the learner confirms
//  first. Progressive enhancement: this intercepts the submit only once it has
//  found every piece it needs, so if the script fails to load the form still
//  posts normally and the feature is never stranded.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  var form = document.getElementById("replay-form");
  var trigger = document.getElementById("replay-btn");
  var backdrop = document.getElementById("rc-backdrop");
  var dialog = document.getElementById("rc-dialog");
  var cancelBtn = document.getElementById("rc-cancel");
  var confirmBtn = document.getElementById("rc-confirm");
  if (!form || !trigger || !backdrop || !dialog || !cancelBtn || !confirmBtn) return;

  var confirmed = false;

  function open() {
    backdrop.hidden = false;
    dialog.hidden = false;
    // Defer so the element is laid out before the transition class lands.
    requestAnimationFrame(function () {
      backdrop.classList.add("open");
      dialog.classList.add("open");
    });
    document.addEventListener("keydown", onKey);
    try { confirmBtn.focus({ preventScroll: true }); } catch (e) { confirmBtn.focus(); }
  }

  function close() {
    backdrop.classList.remove("open");
    dialog.classList.remove("open");
    document.removeEventListener("keydown", onKey);
    setTimeout(function () {
      backdrop.hidden = true;
      dialog.hidden = true;
    }, 200);
    try { trigger.focus({ preventScroll: true }); } catch (e) { trigger.focus(); }
  }

  function onKey(e) {
    if (e.key === "Escape") { e.preventDefault(); close(); return; }
    // Keep tabbing inside the dialog while it is open.
    if (e.key === "Tab") {
      var focusables = [cancelBtn, confirmBtn];
      var i = focusables.indexOf(document.activeElement);
      if (i === -1) return;
      e.preventDefault();
      focusables[(i + (e.shiftKey ? -1 : 1) + focusables.length) % focusables.length].focus();
    }
  }

  // Intercept the submit rather than the click, so pressing Enter in the form
  // is caught too.
  form.addEventListener("submit", function (e) {
    if (confirmed) return;          // second pass: let it through
    e.preventDefault();
    open();
  });

  confirmBtn.addEventListener("click", function () {
    confirmed = true;
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Starting…";
    form.submit();                  // bypasses the listener, so it posts
  });

  cancelBtn.addEventListener("click", close);
  backdrop.addEventListener("click", close);
})();
