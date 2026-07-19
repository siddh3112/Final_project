// ════════════════════════════════════════════════════════════════
//  The Lexicon — the Library's CLICK-TO-INK matching board. Click a concept,
//  then the case that proves it; an amber line inks between them. Click a line to
//  erase it. No dragging. Cards are <button>s, so Tab + Enter works natively.
//  Grading is server-side (the correct pairings are never in the DOM); this only
//  writes the chosen scenario id into each concept's hidden field, then submits.
// ════════════════════════════════════════════════════════════════
(function () {
  const form = document.getElementById("lexicon-form");
  if (!form) return;
  const board = document.getElementById("lex-board");
  const svg = document.getElementById("lex-lines");
  const submitBtn = document.getElementById("lex-submit");
  const countEl = document.getElementById("lex-count");
  const location = form.dataset.location || "";
  const SVGNS = "http://www.w3.org/2000/svg";

  const concepts = Array.from(form.querySelectorAll(".lex-concept"));
  const scenarios = Array.from(form.querySelectorAll(".lex-scenario"));
  const total = concepts.length;

  let selected = null;              // the concept currently picked for linking
  const links = {};                 // conceptKey -> { sid, g (the <g> line group) }

  function reduceMotion() {
    return (
      (window.AtlasPrefs && window.AtlasPrefs.effective && window.AtlasPrefs.effective("reduce_motion")) ||
      (window.ATLAS_PREFS && window.ATLAS_PREFS.reduce_motion) ||
      document.documentElement.classList.contains("reduce-motion") ||
      (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)
    );
  }

  function conceptEl(k) { return form.querySelector('.lex-concept[data-concept="' + k + '"]'); }
  function scenarioEl(sid) { return form.querySelector('.lex-scenario[data-scenario="' + sid + '"]'); }
  function setAnswer(k, sid) {
    const inp = form.querySelector('.lex-answer[data-concept="' + k + '"]');
    if (inp) inp.value = sid || "";
  }
  function linkedCount() { return Object.keys(links).length; }
  function refresh() {
    if (countEl) countEl.textContent = linkedCount();
    if (submitBtn) { const ready = linkedCount() >= total; submitBtn.disabled = !ready; submitBtn.classList.toggle("ready", ready); }
  }
  function clearSelect() { if (selected) selected.classList.remove("selected"); selected = null; }
  function selectConcept(c) { clearSelect(); selected = c; c.classList.add("selected"); }

  // ── line geometry (SVG overlay, board-relative pixels) ──
  function nodeCenter(el, sel) {
    const n = el.querySelector(sel) || el;
    const r = n.getBoundingClientRect(), b = board.getBoundingClientRect();
    return { x: r.left + r.width / 2 - b.left, y: r.top + r.height / 2 - b.top };
  }
  function sizeSvg() {
    const b = board.getBoundingClientRect();
    svg.setAttribute("width", b.width); svg.setAttribute("height", b.height);
    svg.setAttribute("viewBox", "0 0 " + b.width + " " + b.height);
  }
  function mkLine(p1, p2, cls) {
    const l = document.createElementNS(SVGNS, "line");
    l.setAttribute("x1", p1.x); l.setAttribute("y1", p1.y);
    l.setAttribute("x2", p2.x); l.setAttribute("y2", p2.y);
    l.setAttribute("class", cls);
    return l;
  }
  function endpoints(cKey, sid) {
    return [nodeCenter(conceptEl(cKey), ".lex-node-r"), nodeCenter(scenarioEl(sid), ".lex-node-l")];
  }
  function drawLine(cKey, sid) {
    sizeSvg();                              // match the viewBox to the board before drawing
    const [p1, p2] = endpoints(cKey, sid);
    const g = document.createElementNS(SVGNS, "g");
    g.setAttribute("class", "lex-line-g");
    const hit = mkLine(p1, p2, "lex-line-hit");   // wide transparent click target
    const vis = mkLine(p1, p2, "lex-line");        // the visible amber rule
    g.appendChild(hit); g.appendChild(vis);
    g.addEventListener("click", function (e) { e.stopPropagation(); erase(cKey); });
    if (!reduceMotion()) {
      const len = Math.hypot(p2.x - p1.x, p2.y - p1.y);
      vis.style.strokeDasharray = len; vis.style.strokeDashoffset = len;
      requestAnimationFrame(function () {
        vis.style.transition = "stroke-dashoffset 0.28s ease";
        vis.style.strokeDashoffset = 0;
      });
    }
    svg.appendChild(g);
    return g;
  }
  function redrawAll() {
    sizeSvg();
    Object.keys(links).forEach(function (cKey) {
      const g = links[cKey].g; if (!g) return;
      const [p1, p2] = endpoints(cKey, links[cKey].sid);
      g.querySelectorAll("line").forEach(function (l) {
        l.setAttribute("x1", p1.x); l.setAttribute("y1", p1.y);
        l.setAttribute("x2", p2.x); l.setAttribute("y2", p2.y);
      });
    });
  }

  function erase(cKey) {
    const link = links[cKey]; if (!link) return;
    if (link.g && link.g.parentNode) link.g.parentNode.removeChild(link.g);
    const s = scenarioEl(link.sid); if (s) s.classList.remove("spent");
    const c = conceptEl(cKey); if (c) c.classList.remove("linked");
    delete links[cKey];
    setAnswer(cKey, "");
    refresh();
  }
  function link(cKey, sid) {
    if (links[cKey]) erase(cKey);               // relink: drop this concept's old line
    links[cKey] = { sid: sid, g: drawLine(cKey, sid) };
    const s = scenarioEl(sid); if (s) s.classList.add("spent");
    const c = conceptEl(cKey); if (c) c.classList.add("linked");
    setAnswer(cKey, sid);
    refresh();
  }

  concepts.forEach(function (c) {
    c.addEventListener("click", function () { selectConcept(c); });   // Enter/Space fire click natively
  });
  scenarios.forEach(function (s) {
    s.addEventListener("click", function () {
      if (!selected) return;                       // pick a concept first
      if (s.classList.contains("spent")) return;   // a case takes at most one line
      link(selected.dataset.concept, s.dataset.scenario);
      clearSelect();
    });
  });

  sizeSvg();
  refresh();
  window.addEventListener("resize", redrawAll);
  // The board can reflow after first paint (web-font load, images or layout
  // settling) or change size for any reason. Each of these re-syncs the SVG viewBox
  // and every line to the live node positions, so links never drift from their cards
  // or knot up against a stale viewBox.
  if (window.ResizeObserver) new ResizeObserver(function () { redrawAll(); }).observe(board);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(redrawAll);
  window.addEventListener("load", redrawAll);
  requestAnimationFrame(redrawAll);

  submitBtn.addEventListener("click", function () {
    if (linkedCount() < total) return;
    form.submit();   // hidden fields carry each concept's inked scenario id
  });

  // ── Hint → Professor Atlas (same /npc/chat flow as every other Trial) ──
  const hintBtn = document.getElementById("lex-hint");
  if (hintBtn) {
    const box = form.querySelector(".hint-box");
    const textEl = box ? box.querySelector(".hint-text") : null;
    const consultedEl = document.getElementById("consulted");
    hintBtn.addEventListener("click", async function () {
      if (consultedEl && selected) {
        const set = new Set((consultedEl.value || "").split(",").filter(Boolean));
        set.add(selected.dataset.concept);
        consultedEl.value = Array.from(set).join(",");
      }
      if (box) box.hidden = false;
      if (textEl) textEl.textContent = "Professor Atlas ponders…";
      hintBtn.disabled = true;
      const topic = selected ? selected.dataset.question : "telling these AI concepts apart";
      const fallback = "Match each concept to the case that shows it in action — and rule out the cases that fit a different concept.";
      try {
        const res = await fetch("/npc/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: "Give me a hint without revealing the answer, about: " + topic, location: location }),
        });
        const data = await res.json();
        const good = data && data.response && !data.is_fallback;
        if (textEl) textEl.textContent = good ? data.response : fallback;
      } catch (e) {
        if (textEl) textEl.textContent = fallback;
      } finally {
        hintBtn.disabled = false;
        if (box) box.scrollIntoView({ behavior: "smooth", block: "end" });  // keep the whole hint on-screen
      }
    });
  }
})();
