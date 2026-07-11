// ════════════════════════════════════════════════════════════════
//  Interactive Library — the "real book" reader.
//  An open two-page parchment spread: shelf → fly-to-centre → cover
//  opens → page 1; page-turns fold in 3D. PRESENTATION ONLY — the flow
//  (intro → concept → example → quick-check → reward), the hook beat,
//  quick-check logic, read persistence, and everything graded are
//  UNCHANGED from before.
// ════════════════════════════════════════════════════════════════
(function () {
  const reader = document.getElementById("book-reader");
  if (!reader) return;

  let BOOKS = [];
  try { BOOKS = JSON.parse(document.getElementById("library-books").textContent); } catch (e) { BOOKS = []; }

  // Guess-first hooks (chunk order), shown before a book's content. Never logged.
  let LIB_HOOKS = [];
  try { LIB_HOOKS = JSON.parse(document.getElementById("library-hooks").textContent) || []; } catch (e) { LIB_HOOKS = []; }

  const tome = document.getElementById("book-tome");
  const pageEl = document.getElementById("book-page");
  const prevBtn = document.getElementById("book-prev");
  const nextBtn = document.getElementById("book-next");
  const indicator = document.getElementById("book-indicator");

  const readEl = document.getElementById("books-read");
  const coreFill = document.getElementById("core-fill");
  const core = document.getElementById("knowledge-core");
  const hint = document.getElementById("shelf-hint");

  const trialGate = document.getElementById("trial-gate");
  const trialContent = document.getElementById("trial-content");
  const navWrap = reader.querySelector(".book-reader-nav");

  const realBooks = Array.from(document.querySelectorAll(".book-real"));
  const total = BOOKS.length;
  const completed = new Set();

  function reduceMotion() {
    return !!((window.AtlasPrefs && window.AtlasPrefs.effective && window.AtlasPrefs.effective("reduce_motion")) ||
      (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches));
  }

  const FLAVOURS = [
    "A handsome binding — but its pages have long since faded to blank.",
    "Dust and cobwebs. This volume holds nothing for you today.",
    "An old novel, charming but quite unrelated to your studies.",
    "The ink has run; not a single word survives.",
    "Written in a script you cannot read.",
    "Heavy and gilded, yet utterly empty within.",
  ];

  let book = null;
  let bookIndex = -1;
  let page = 0;
  let pageCount = 0;
  let quizPassed = false;

  // "Read aloud" button (Web Speech). Lives on the tome; wired per content page.
  const ttsBtn = window.AtlasVoice && window.AtlasVoice.button("#d4a84b");
  if (ttsBtn) { ttsBtn.classList.add("tts-corner"); ttsBtn.hidden = true; tome.appendChild(ttsBtn); }
  function stopVoice() { if (window.AtlasVoice) window.AtlasVoice.stop(); }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }
  function highlight(body, keywords) {
    let html = escapeHtml(body);
    (keywords || []).forEach((kw) => {
      const re = new RegExp("(" + kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
      html = html.replace(re, '<mark class="kw">$1</mark>');
    });
    return html;
  }
  function atlasHint(text) {
    return (
      '<div class="atlas-hint"><span class="atlas-hint-avatar"><span class="atlas-glyph" aria-hidden="true"></span></span>' +
      '<div><div class="atlas-hint-name">Professor Atlas</div>' +
      '<p class="atlas-hint-text">' + escapeHtml(text) + "</p></div></div>"
    );
  }
  function splitSentences(body) {
    const m = body.match(/[^.!?]+[.!?]+/g);
    return m && m.length ? m.map((s) => s.trim()) : [body.trim()];
  }

  // ── live typing of body text ──
  let typing = false;
  let typeTimer = null;
  let typeCtx = null;
  function typeBody(bodyEl, sentences, keywords) {
    clearTimeout(typeTimer);
    bodyEl.innerHTML = "";
    const lineEls = sentences.map(function () {
      const p = document.createElement("p");
      p.className = "bp-sentence";
      bodyEl.appendChild(p);
      return p;
    });
    // reduce-motion: no typewriter — show the finished text instantly.
    if (reduceMotion()) {
      lineEls.forEach(function (el, i) { el.innerHTML = highlight(sentences[i], keywords); });
      typing = false;
      return;
    }
    typeCtx = { sentences: sentences, keywords: keywords, lineEls: lineEls };
    typing = true;
    let si = 0, ci = 0;
    function tick() {
      if (si >= sentences.length) { finishTyping(); return; }
      if (ci === 0) lineEls[si].classList.add("typing-line");
      ci++;
      lineEls[si].textContent = sentences[si].slice(0, ci);
      if (ci >= sentences[si].length) {
        lineEls[si].classList.remove("typing-line");
        lineEls[si].innerHTML = highlight(sentences[si], keywords);
        si++; ci = 0;
      }
      typeTimer = setTimeout(tick, 14);
    }
    tick();
  }
  function finishTyping() {
    clearTimeout(typeTimer);
    if (typeCtx) {
      typeCtx.lineEls.forEach(function (el, i) {
        el.classList.remove("typing-line");
        el.innerHTML = highlight(typeCtx.sentences[i], typeCtx.keywords);
      });
    }
    typing = false;
  }

  // ── render the current page into the open-book spread ──
  function render() {
    clearTimeout(typeTimer);
    typing = false;
    stopVoice(); // page changed — never let audio linger on a page you left

    const contentPages = book.pages.length;
    const quizPage = contentPages;

    let html = "";
    const isContent = page < contentPages;
    let body = null, keywords = null;

    if (isContent) {
      const p = book.pages[page];
      const art = book.art || "📖";
      const kicker = p.type === "intro" ? "Prologue" : p.type === "concept" ? "The Concept" : "In the World";
      body = p.body;
      keywords = p.keywords;
      // LEFT leaf: illuminated plate + heading. RIGHT leaf: the body (drop cap).
      html =
        '<div class="bp bp-' + p.type + ' bp-spread">' +
          '<div class="leaf leaf-left">' +
            '<figure class="art-plate"><span class="art-plate-art">' + art + '</span></figure>' +
            '<div class="bp-kicker">' + kicker + '</div>' +
            '<h2 class="bp-title">' + escapeHtml(p.title) + '</h2>' +
          '</div>' +
          '<div class="leaf leaf-right">' +
            '<div class="bp-body" id="bp-body"></div>' +
            (p.hint ? atlasHint(p.hint) : "") +
          '</div>' +
        '</div>';
    } else if (page === quizPage) {
      const q = book.quiz;
      html =
        '<div class="bp bp-quiz">' +
          '<div class="bp-spread">' +
            '<div class="leaf leaf-left">' +
              '<div class="bp-kicker">Quick Check</div>' +
              '<h2 class="bp-title">' + escapeHtml(q.question) + '</h2>' +
              '<div class="quiz-quill" aria-hidden="true">✒</div>' +
            '</div>' +
            '<div class="leaf leaf-right">' +
              '<div class="bp-options" id="bp-options">' +
              q.options.map((opt, k) => '<button type="button" class="bp-option" data-k="' + k + '"><span class="bp-badge">' + ["A", "B", "C", "D", "E", "F"][k] + '</span><span class="bp-opt-text">' + escapeHtml(opt) + "</span></button>").join("") +
              '</div>' +
              '<div class="bp-feedback" id="bp-feedback"></div>' +
            '</div>' +
          '</div>' +
          '<div class="bp-quiz-foot" id="bp-quiz-foot"></div>' +  /* Claim Reward appears here, centred, only after a correct answer */
        '</div>';
    } else {
      const f = book.flashcard;
      html =
        '<div class="bp bp-reward">' +
        '<div class="bp-reward-burst">✦</div>' +
        '<h2 class="bp-title">Concept Card Acquired</h2>' +
        '<div class="reward-card rarity-' + f.rarity.toLowerCase() + '">' +
        '<div class="fc-rarity">' + escapeHtml(f.rarity) + "</div>" +
        '<div class="fc-icon">' + (book.art || '<i class="bi bi-cpu"></i>') + "</div>" +
        '<div class="fc-name">' + escapeHtml(book.concept) + "</div>" +
        '<div class="fc-type">' + escapeHtml(f.type) + "</div>" +
        "</div>" +
        '<p class="reward-xp">+' + book.xp + " XP &nbsp;•&nbsp; Knowledge Core charged</p>" +
        "</div>";
    }

    pageEl.innerHTML = html;

    // Concept Card acquired page — play the reward sparkle.
    if (page > quizPage && window.LibFX && window.LibFX.reward) window.LibFX.reward();

    if (isContent) typeBody(pageEl.querySelector("#bp-body"), splitSentences(body), keywords);
    if (page === quizPage) wireQuiz();

    // Read-aloud: narrates the taught text on content pages, and the question
    // on the quick-check page. Hidden on the reward/flavour pages (nothing to read).
    if (ttsBtn) {
      let say = null;
      if (isContent && body) say = body;
      else if (page === quizPage && book && book.quiz) say = book.quiz.question;
      if (say) {
        ttsBtn.hidden = false;
        const text = say;
        ttsBtn.onclick = function () { window.AtlasVoice.toggle(text, "#d4a84b", ttsBtn); };
      } else {
        ttsBtn.hidden = true;
        ttsBtn.onclick = null;
      }
    }

    updateNav();
  }

  // Advance to the reward page (only reachable once the quick-check is passed).
  function claimReward() {
    if (!quizPassed) return;
    if (window.LibFX) window.LibFX.pageTurn();
    page++;
    turnPage(1, render);
  }

  // Quick-check (unlogged learning gate): correct → reveal the bottom-centre
  // Claim Reward; wrong → try again / re-read. Compares to book.quiz.answer by
  // the option's stable data-k index, so shuffling never breaks the check.
  function wireQuiz() {
    const opts = Array.from(pageEl.querySelectorAll(".bp-option"));
    const fb = pageEl.querySelector("#bp-feedback");
    const foot = pageEl.querySelector("#bp-quiz-foot");
    opts.forEach(function (b) {
      b.addEventListener("click", function () {
        if (quizPassed) return;                    // already answered correctly — locked
        const k = parseInt(b.dataset.k, 10);
        if (k === book.quiz.answer) {
          quizPassed = true;
          if (window.LibFX) window.LibFX.correct();
          opts.forEach(function (o) { o.disabled = true; o.classList.remove("wrong"); });
          b.classList.add("correct", "sparkle");
          if (fb) fb.innerHTML = '<span class="fb-ok"><i class="bi bi-check-lg me-1"></i>Correct! ' + escapeHtml(book.quiz.explanation) + "</span>";
          if (foot) {
            foot.innerHTML = '<button type="button" class="bp-claim" id="bp-claim">Claim Reward <i class="bi bi-stars ms-1"></i></button>';
            const cb = foot.querySelector("#bp-claim");
            if (cb) cb.addEventListener("click", claimReward);
          }
          updateNav();
        } else {
          if (window.LibFX) window.LibFX.wrong();
          b.classList.add("wrong", "shake");
          setTimeout(function () { b.classList.remove("shake"); }, 500);
          // Lock the options after a wrong answer: no instant correction. The only
          // way forward is the existing "Read the Book Again" gate, which resets
          // and re-renders fresh (re-enabled) options. (Ungraded learning gate.)
          opts.forEach(function (o) { o.disabled = true; });
          if (fb) {
            fb.innerHTML =
              '<span class="fb-no"><i class="bi bi-x-lg me-1"></i>Not quite — ' + escapeHtml(book.quiz.explanation) + '</span>' +
              '<button type="button" class="bp-reread" id="bp-reread"><i class="bi bi-arrow-counterclockwise"></i> Read the Book Again</button>';
            const rr = fb.querySelector("#bp-reread");
            if (rr) rr.addEventListener("click", function () { quizPassed = false; page = 0; turnPage(-1, render); });
          }
        }
      });
    });
  }

  function updateNav() {
    const quizPage = book.pages.length;
    // Page indicator becomes an ink notation: "— 2 —"
    indicator.textContent = "— " + (page + 1) + " —";
    prevBtn.disabled = page === 0;
    prevBtn.style.visibility = page >= quizPage ? "hidden" : "visible";
    if (page < quizPage) {
      nextBtn.hidden = false;
      nextBtn.innerHTML = page === 0 ? "Begin Discovery <i class='bi bi-chevron-right'></i>" : "Next <i class='bi bi-chevron-right'></i>";
    } else if (page === quizPage) {
      // The reward is claimed via the bottom-centre "Claim Reward" button that
      // appears only after a correct answer — no right-margin nav pill here.
      nextBtn.hidden = true;
    } else {
      nextBtn.hidden = false;
      nextBtn.innerHTML = "Add to Deck <i class='bi bi-check2'></i>";
    }
  }

  // ── 3D page-turn: the current page folds away at the spine, revealing the
  //    freshly-rendered page beneath. reduce-motion → instant swap. ──
  function turnPage(dir, renderFn) {
    if (reduceMotion()) { renderFn(); return; }
    let flip;
    try {
      const r = pageEl.getBoundingClientRect();
      const tr = tome.getBoundingClientRect();
      flip = document.createElement("div");
      flip.className = "page-flip " + (dir >= 0 ? "flip-fwd" : "flip-back");
      flip.style.left = (r.left - tr.left) + "px";
      flip.style.top = (r.top - tr.top) + "px";
      flip.style.width = r.width + "px";
      flip.style.height = r.height + "px";
      // clone the outgoing page (strip ids to avoid brief duplicates)
      const clone = pageEl.cloneNode(true);
      clone.removeAttribute("id");
      clone.querySelectorAll("[id]").forEach((n) => n.removeAttribute("id"));
      flip.innerHTML = '<div class="page-flip-inner"></div><div class="page-flip-shade"></div>';
      flip.firstChild.appendChild(clone);
      tome.appendChild(flip);
    } catch (e) { renderFn(); return; }

    renderFn(); // new content underneath the folding clone

    requestAnimationFrame(function () {
      requestAnimationFrame(function () { flip.classList.add("go"); });
    });
    setTimeout(function () { if (flip.parentNode) flip.parentNode.removeChild(flip); }, 500);
  }

  function openBook(i) {
    book = BOOKS[i];
    bookIndex = i;
    page = 0;
    // The quick-check is ALWAYS answerable — even re-reading a completed book —
    // so clicking an option always registers. (It's an unlogged learning gate.)
    quizPassed = false;
    pageCount = book.pages.length + 2;
    showModal(true);
    // Guess-first hook beat — only before a book you haven't studied yet.
    const hook = (!completed.has(i)) ? LIB_HOOKS[i] : null;
    if (hook && window.AtlasHook) {
      if (navWrap) navWrap.style.visibility = "hidden";
      pageEl.innerHTML = "";
      window.AtlasHook.mount(pageEl, hook, {
        accent: "#d4a84b",
        onContinue: function () { if (navWrap) navWrap.style.visibility = ""; render(); },
      });
    } else {
      render();
    }
  }
  function openDecoy() {
    stopVoice();
    if (ttsBtn) ttsBtn.hidden = true; // decoys aren't taught content
    book = null;
    pageCount = 1;
    pageEl.innerHTML =
      '<div class="bp bp-flavour"><figure class="art-plate art-plate-lg"><span class="art-plate-art">🕮</span></figure>' +
      '<p class="bp-body">' + FLAVOURS[Math.floor(Math.random() * FLAVOURS.length)] + "</p></div>";
    indicator.textContent = "";
    prevBtn.style.visibility = "hidden";
    nextBtn.hidden = true;
    if (navWrap) navWrap.style.visibility = "";
    showModal(true);
  }

  // Show the reader; `coverOpen` plays the leather cover swinging open to page 1.
  function showModal(coverOpen) {
    reader.hidden = false;
    document.body.style.overflow = "hidden";
    tome.classList.remove("opening", "closing");
    void tome.offsetWidth;
    if (!reduceMotion()) {
      tome.classList.add("opening");
      if (coverOpen) {
        const cover = document.createElement("div");
        cover.className = "tome-cover";
        cover.innerHTML = '<span class="tome-cover-rule"></span><span class="tome-cover-emboss">✦</span>';
        tome.appendChild(cover);
        requestAnimationFrame(function () { requestAnimationFrame(function () { cover.classList.add("swing"); }); });
        setTimeout(function () { if (cover.parentNode) cover.parentNode.removeChild(cover); }, 760);
      }
    }
  }
  function closeReader() {
    stopVoice();
    if (reduceMotion()) { reader.hidden = true; document.body.style.overflow = ""; return; }
    tome.classList.add("closing");
    setTimeout(function () {
      reader.hidden = true;
      tome.classList.remove("closing", "opening");
      document.body.style.overflow = "";
    }, 380);
  }

  function completeBook(i) {
    if (completed.has(i)) return;
    completed.add(i);
    const tomeBtn = realBooks.find((b) => b.dataset.index == i);
    if (tomeBtn) tomeBtn.classList.add("studied");
    const card = document.querySelector('.flashcard[data-index="' + i + '"]');
    if (card) card.classList.remove("locked");
    if (readEl) readEl.textContent = completed.size;
    if (coreFill) coreFill.style.width = (completed.size / total) * 100 + "%";
    if (core) core.classList.add("charging");
    if (window.LibFX) window.LibFX.coreBurst(core);
    if (window.LibFX) window.LibFX.coreCharge();   // audible "core charged" sweep
    persistRead(i);                                // remember this per-user (server session)
    if (completed.size === total) {
      if (core) core.classList.add("active");
      unlockTrial();
    }
  }

  // Fly the reward card toward the Concept Deck, then complete + close.
  function cardToDeck(i, done) {
    const src = pageEl.querySelector(".reward-card");
    const dest = document.querySelector('.flashcard[data-index="' + i + '"]');
    if (!src || !dest || reduceMotion()) { done(); return; }
    try {
      const s = src.getBoundingClientRect(), d = dest.getBoundingClientRect();
      const fly = src.cloneNode(true);
      fly.className += " card-fly";
      fly.style.left = s.left + "px"; fly.style.top = s.top + "px";
      fly.style.width = s.width + "px"; fly.style.height = s.height + "px";
      document.body.appendChild(fly);
      const dx = (d.left + d.width / 2) - (s.left + s.width / 2);
      const dy = (d.top + d.height / 2) - (s.top + s.height / 2);
      const sc = Math.max(0.2, Math.min(1, d.width / s.width));
      requestAnimationFrame(function () {
        fly.style.transform = "translate(" + dx + "px," + dy + "px) scale(" + sc + ") rotate(8deg)";
        fly.style.opacity = "0.15";
      });
      setTimeout(function () { if (fly.parentNode) fly.parentNode.removeChild(fly); done(); }, 480);
    } catch (e) { done(); }
  }

  // ── Persist / restore reading progress (per user, server session) so a
  //    failed Trial never forces a full re-read. Presentation/progress only. ──
  function persistRead(i) {
    const b = BOOKS[i];
    const loc = reader.dataset.loc;
    if (!b || !b.id || !loc) return;
    try {
      fetch("/location/" + encodeURIComponent(loc) + "/read", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ book: b.id }),
        keepalive: true,
      });
    } catch (e) {}
  }

  function restoreProgress() {
    let readIds = [];
    try { readIds = JSON.parse(document.getElementById("library-read").textContent) || []; } catch (e) {}
    if (!readIds.length) return;
    readIds.forEach(function (id) {
      const i = BOOKS.findIndex(function (b) { return b.id === id; });
      if (i < 0 || completed.has(i)) return;
      completed.add(i);
      const tomeBtn = realBooks.find((b) => b.dataset.index == i);
      if (tomeBtn) tomeBtn.classList.add("studied");
      const card = document.querySelector('.flashcard[data-index="' + i + '"]');
      if (card) card.classList.remove("locked");
    });
    if (!completed.size) return;
    if (readEl) readEl.textContent = completed.size;
    if (coreFill) coreFill.style.width = (completed.size / total) * 100 + "%";
    if (completed.size >= total && total > 0) {
      // Already fully studied — restore the UNLOCKED end state silently
      // (no celebration replay on every reload).
      if (core) core.classList.add("active");
      if (trialGate) trialGate.hidden = true;
      if (trialContent) trialContent.hidden = false;
      if (hint) {
        hint.innerHTML = "Every tome has been mastered. <strong>The Trial</strong> awaits — or revisit any volume at your leisure.";
        hint.classList.add("all-done");
      }
    } else if (core) {
      core.classList.add("charging");
    }
  }
  function unlockTrial() {
    if (trialGate) trialGate.hidden = true;
    if (trialContent) trialContent.hidden = false;
    if (window.LibFX) window.LibFX.celebrate();
    if (hint) {
      hint.innerHTML = "Every tome has been mastered. <strong>The Trial</strong> awaits below.";
      hint.classList.add("all-done");
    }
  }

  nextBtn.addEventListener("click", function () {
    if (!book) return;
    if (typing) { finishTyping(); return; }
    const quizPage = book.pages.length;
    if (page < quizPage) {
      if (window.LibFX) window.LibFX.pageTurn();
      page++;
      turnPage(1, render);
    } else if (page === quizPage) {
      if (!quizPassed) return;
      if (window.LibFX) window.LibFX.pageTurn();
      page++;
      turnPage(1, render);
    } else {
      const bi = bookIndex;
      cardToDeck(bi, function () { completeBook(bi); closeReader(); });
    }
  });
  prevBtn.addEventListener("click", function () {
    if (typing) { finishTyping(); return; }
    if (book && page > 0 && page < book.pages.length) {
      if (window.LibFX) window.LibFX.pageTurn();
      page--;
      turnPage(-1, render);
    }
  });

  // ── The signature moment: a clicked tome flies from its shelf spot to the
  //    centre, turning spine → front cover, then the reader opens page 1. ──
  function flyOpen(spineEl, i) {
    if (reduceMotion()) { openBook(i); return; }
    let fly;
    try {
      const r = spineEl.getBoundingClientRect();
      fly = document.createElement("div");
      fly.className = "book-fly";
      fly.style.left = r.left + "px";
      fly.style.top = r.top + "px";
      fly.style.width = r.width + "px";
      fly.style.height = r.height + "px";
      const title = (BOOKS[i] && BOOKS[i].concept) ? BOOKS[i].concept : "";
      fly.innerHTML = '<div class="book-fly-inner"><span class="book-fly-plate">' +
        ((BOOKS[i] && BOOKS[i].art) || "📖") + '</span><span class="book-fly-title">' + escapeHtml(title) + '</span></div>';
      document.body.appendChild(fly);
      const cx = window.innerWidth / 2, cy = window.innerHeight / 2;
      const sx = r.left + r.width / 2, sy = r.top + r.height / 2;
      const scale = Math.max(1, Math.min(6, 240 / Math.max(1, r.height)));
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          fly.classList.add("go");
          fly.style.transform = "translate(" + (cx - sx) + "px," + (cy - sy) + "px) scale(" + scale + ")";
        });
      });
    } catch (e) { openBook(i); return; }

    // Hand off to the reader (cover swings open) just before the flight ends.
    setTimeout(function () { openBook(i); }, 520);
    setTimeout(function () { if (fly && fly.parentNode) fly.parentNode.removeChild(fly); }, 640);
  }

  // Book pull: spine slides out of the shelf, then flies open.
  realBooks.forEach((b) =>
    b.addEventListener("click", function () {
      if (window.LibFX) window.LibFX.bookPull();
      b.classList.add("pulling");
      const i = parseInt(b.dataset.index, 10);
      setTimeout(function () { b.classList.remove("pulling"); flyOpen(b, i); }, 260);
    })
  );
  document.querySelectorAll(".book-decoy").forEach((b) =>
    b.addEventListener("click", function () {
      if (window.LibFX) window.LibFX.bookPull();
      b.classList.add("pulling");
      setTimeout(function () { b.classList.remove("pulling"); openDecoy(); }, 200);
    })
  );
  reader.querySelectorAll("[data-close]").forEach((el) => el.addEventListener("click", closeReader));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !reader.hidden) closeReader();
  });

  document.querySelectorAll(".flashcard").forEach((card) =>
    card.addEventListener("click", function () {
      if (card.classList.contains("locked")) return;
      card.classList.toggle("flipped");
    })
  );

  // Restore any previously-read volumes (per-user session) so leaving for the
  // Trial and coming back never resets the Knowledge Core or the Concept Deck.
  restoreProgress();
})();
