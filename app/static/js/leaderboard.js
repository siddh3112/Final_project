// ════════════════════════════════════════════════════════════════
//  Personal best-runs leaderboard (hub). Slide-in panel showing THIS
//  user's runs only — never a cross-user competition. Display only.
// ════════════════════════════════════════════════════════════════
(function () {
  "use strict";
  var trophy = document.getElementById("lb-trophy");
  var panel = document.getElementById("lb-panel");
  var backdrop = document.getElementById("lb-backdrop");
  var closeBtn = document.getElementById("lb-close");
  if (!trophy || !panel || !backdrop) return;

  function open() {
    backdrop.hidden = false;
    requestAnimationFrame(function () {
      panel.classList.add("open");
      backdrop.classList.add("open");
    });
    panel.setAttribute("aria-hidden", "false");
    document.addEventListener("keydown", onKey);
  }
  function close() {
    panel.classList.remove("open");
    backdrop.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
    document.removeEventListener("keydown", onKey);
    setTimeout(function () { backdrop.hidden = true; }, 320);
    trophy.focus();
  }
  function onKey(e) { if (e.key === "Escape") close(); }

  trophy.addEventListener("click", open);
  if (closeBtn) closeBtn.addEventListener("click", close);
  backdrop.addEventListener("click", close);
})();
