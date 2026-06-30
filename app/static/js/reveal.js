// Reveal the location's sections one by one (after Atlas finishes, if he speaks).
(function () {
  const blocks = Array.from(document.querySelectorAll(".loc-reveal"));
  if (!blocks.length) return;

  blocks.forEach((b) => b.classList.add("pre-reveal"));

  function run() {
    blocks.forEach((b, i) => {
      setTimeout(() => b.classList.remove("pre-reveal"), 120 + i * 200);
    });
  }

  // If Professor Atlas is giving an onboarding overlay, wait until he's done;
  // otherwise reveal right away on load.
  const overlay = document.getElementById("atlas-onboard");
  if (overlay) {
    document.addEventListener("atlas:onboard-done", run, { once: true });
  } else {
    run();
  }
})();
