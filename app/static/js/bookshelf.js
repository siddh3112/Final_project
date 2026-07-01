// ════════════════════════════════════════════════════════════════
//  Interactive Library — multi-page book reader.
//  Pages: intro → concept → example → quick-check quiz → reward.
//  Passing charges the Knowledge Core, unlocks the deck flashcard, and
//  (when every book is done) unlocks the Trial. Decoys give flavour text.
// ════════════════════════════════════════════════════════════════
(function () {
  const reader = document.getElementById("book-reader");
  if (!reader) return;

  let BOOKS = [];
  try {
    BOOKS = JSON.parse(document.getElementById("library-books").textContent);
  } catch (e) {
    BOOKS = [];
  }

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

  const realBooks = Array.from(document.querySelectorAll(".book-real"));
  const total = BOOKS.length;
  const completed = new Set();

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

  // ── render the current page ──
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
      const kicker = p.type === "intro" ? "" : p.type === "concept" ? "Concept" : "Real-World Example";
      body = p.body;
      keywords = p.keywords;
      html =
        '<div class="bp bp-' + p.type + '">' +
        '<div class="bp-illus">' + art + "</div>" +
        (kicker ? '<div class="bp-kicker">' + kicker + "</div>" : "") +
        '<h2 class="bp-title">' + escapeHtml(p.title) + "</h2>" +
        '<div class="bp-body" id="bp-body"></div>' +
        (p.hint ? atlasHint(p.hint) : "") +
        "</div>";
    } else if (page === quizPage) {
      const q = book.quiz;
      html =
        '<div class="bp bp-quiz">' +
        '<div class="bp-kicker">Quick Check</div>' +
        '<h2 class="bp-title">' + escapeHtml(q.question) + "</h2>" +
        '<div class="bp-options" id="bp-options">' +
        q.options.map((opt, k) => '<button type="button" class="bp-option" data-k="' + k + '"><span class="bp-badge">' + ["A", "B", "C", "D", "E", "F"][k] + '</span><span class="bp-opt-text">' + escapeHtml(opt) + "</span></button>").join("") +
        "</div>" +
        '<div class="bp-feedback" id="bp-feedback"></div>' +
        "</div>";
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
    pageEl.classList.remove("turning");
    void pageEl.offsetWidth;
    pageEl.classList.add("turning");

    if (isContent) typeBody(pageEl.querySelector("#bp-body"), splitSentences(body), keywords);
    if (page === quizPage) wireQuiz();

    // Read-aloud: only on taught content pages (never the quiz or reward).
    if (ttsBtn) {
      if (isContent && body) {
        ttsBtn.hidden = false;
        const say = body;
        ttsBtn.onclick = function () { window.AtlasVoice.toggle(say, "#d4a84b", ttsBtn); };
      } else {
        ttsBtn.hidden = true;
        ttsBtn.onclick = null;
      }
    }

    updateNav();
  }

  // Quick-check: correct → advance; wrong → must re-read the whole book.
  function wireQuiz() {
    const opts = Array.from(pageEl.querySelectorAll(".bp-option"));
    const fb = pageEl.querySelector("#bp-feedback");
    opts.forEach((b) =>
      b.addEventListener("click", function () {
        if (quizPassed || b.disabled) return;
        const k = parseInt(b.dataset.k, 10);
        if (k === book.quiz.answer) {
          quizPassed = true;
          if (window.LibFX) window.LibFX.correct();
          b.classList.add("correct", "sparkle");
          opts.forEach((o) => (o.disabled = true));
          fb.innerHTML = '<span class="fb-ok">Correct! ' + escapeHtml(book.quiz.explanation) + "</span>";
          updateNav();
        } else {
          if (window.LibFX) window.LibFX.wrong();
          b.classList.add("wrong", "shake");
          setTimeout(() => b.classList.remove("shake"), 500);
          opts.forEach((o) => (o.disabled = true));
          fb.innerHTML =
            '<span class="fb-no">Not quite. A true scholar reads again — return to the book, then retry.</span>' +
            '<button type="button" class="bp-reread" id="bp-reread"><i class="bi bi-arrow-counterclockwise"></i> Read the Book Again</button>';
          pageEl.querySelector("#bp-reread").addEventListener("click", function () {
            quizPassed = false;
            page = 0;
            render();
          });
        }
      })
    );
  }

  function updateNav() {
    const quizPage = book.pages.length;
    indicator.textContent = "Page " + (page + 1) + " of " + pageCount;
    prevBtn.disabled = page === 0;
    prevBtn.style.visibility = page >= quizPage ? "hidden" : "visible";
    if (page < quizPage) {
      nextBtn.hidden = false;
      nextBtn.innerHTML = page === 0 ? "Begin Discovery <i class='bi bi-chevron-right'></i>" : "Next <i class='bi bi-chevron-right'></i>";
    } else if (page === quizPage) {
      nextBtn.hidden = !quizPassed;
      nextBtn.innerHTML = "Claim Reward <i class='bi bi-stars'></i>";
    } else {
      nextBtn.hidden = false;
      nextBtn.innerHTML = "Add to Deck <i class='bi bi-check2'></i>";
    }
  }

  function openBook(i) {
    book = BOOKS[i];
    bookIndex = i;
    page = 0;
    quizPassed = completed.has(i);
    pageCount = book.pages.length + 2;
    showModal();
    render();
  }
  function openDecoy() {
    stopVoice();
    if (ttsBtn) ttsBtn.hidden = true; // decoys aren't taught content
    book = null;
    pageCount = 1;
    pageEl.innerHTML =
      '<div class="bp bp-flavour"><div class="bp-illus">🕮</div>' +
      '<p class="bp-body">' + FLAVOURS[Math.floor(Math.random() * FLAVOURS.length)] + "</p></div>";
    indicator.textContent = "";
    prevBtn.style.visibility = "hidden";
    nextBtn.hidden = true;
    showModal();
    pageEl.classList.remove("turning");
    void pageEl.offsetWidth;
    pageEl.classList.add("turning");
  }
  function showModal() {
    reader.hidden = false;
    document.body.style.overflow = "hidden";
    tome.classList.remove("opening");
    void tome.offsetWidth;
    tome.classList.add("opening");
  }
  function closeReader() {
    stopVoice();
    reader.hidden = true;
    document.body.style.overflow = "";
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
    if (completed.size === total) {
      if (core) core.classList.add("active");
      unlockTrial();
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
      render();
    } else if (page === quizPage) {
      if (!quizPassed) return;
      if (window.LibFX) window.LibFX.pageTurn();
      page++;
      render();
    } else {
      completeBook(bookIndex);
      closeReader();
    }
  });
  prevBtn.addEventListener("click", function () {
    if (typing) { finishTyping(); return; }
    if (book && page > 0 && page < book.pages.length) {
      if (window.LibFX) window.LibFX.pageTurn();
      page--;
      render();
    }
  });

  // Book pull: spine slides out of the shelf, then the reader opens.
  realBooks.forEach((b) =>
    b.addEventListener("click", function () {
      if (window.LibFX) window.LibFX.bookPull();
      b.classList.add("pulling");
      const i = parseInt(b.dataset.index, 10);
      setTimeout(function () { b.classList.remove("pulling"); openBook(i); }, 260);
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
})();
