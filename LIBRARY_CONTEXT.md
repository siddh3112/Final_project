# Atlas Quest — The Library (deep dive)

> Paste this whole file into a new Claude session for full context on the Library location.
> It assumes the app-level context in `PROJECT_CONTEXT.md` (Flask + vanilla-JS, SQLite, per-user
> auth, condition = game|control, Professor Atlas via Ollama). Everything below is the current code.

## 1. What the Library is
The Library is the **first location** (`LOCATION_ORDER[0]`, always unlocked) and the gateway of the
game. Its topic is **"What is Artificial Intelligence?"**. Instead of a page of text, it's an
**interactive bookshelf**: most books are atmospheric decoys, but **5 "glowing tomes"** hold the real
lessons. The learner reads each tome, passes a low-stakes quick-check to collect a **Concept Card**
and charge the **Knowledge Core**; filling the Core unlocks **The Trial** (a graded 4-question quiz).
Passing the Trial (3/4) completes the Library, awards the **First Steps** badge, and unlocks the AI Lab.

- **key:** `library`  **theme:** `archive`  **accent:** amber `#d4a84b`  **interaction:** `bookshelf`
- **icon:** 📚  **order:** 1  **always unlocked** (start of the unlock chain)

## 2. What it teaches (5 concepts)
Authored from IBM "Introduction to AI". The 5 tomes, in order (`LIBRARY_BOOKS`):
1. **`ai`** — *Artificial Intelligence*: AI = a machine learning patterns from data to make predictions; it **adds to** human judgement, doesn't replace it; mostly invisible (search, recommendations, voice).
2. **`augmented`** — *Augmented Intelligence*: AI that assists humans with impractical tasks (read 1000 pages/hr) and **keeps a human in charge** (e.g. bank pre-screens loans, officer decides). Contrast with full AI, which aims to mimic human thinking.
3. **`does`** — *Analysis & Prediction*: AI does two things — **analyse** data to find patterns, then **predict** an outcome (e.g. spot fraud patterns → flag a suspicious charge).
4. **`predict`** — *AI Predictions*: real applications — vision/diagnosis, reading road signs, fraud detection, customer service.
5. **`levels`** — *The Three Levels of AI*: **Narrow** (one task, e.g. chess/spam), **Broad** (IBM's term for today's integrated systems, e.g. a self-driving car), **General** (human-level, doesn't exist yet).

## 3. Content data — `app/game_content.py`
Everything the Library renders comes from here.

### 3a. `LIBRARY_BOOKS` (the 5 tomes)
A list of dicts, serialized to the page as JSON `#library-books`. Each book:
```python
{
  "id": "ai",                     # stable identity (used for read-progress persistence)
  "title": "The Book of Artificial Intelligence",
  "concept": "Artificial Intelligence",   # shown on the shelf spine + Concept Card
  "art": "🤖",                    # emoji illustration
  "xp": 100,
  "pages": [                      # the reader flow, in order
    {"type": "intro",   "title": ..., "body": ...},
    {"type": "concept", "title": ..., "body": ..., "keywords": [...]},   # keywords get highlighted
    {"type": "example", "title": ..., "body": ..., "hint": ...},         # hint → Professor Atlas aside
  ],
  "quiz": {                       # the in-book QUICK-CHECK (a learning gate, NOT logged)
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "answer": 1,                  # 0-based index into options
    "explanation": "...",
  },
  "flashcard": {"type": "Core Concept", "rarity": "Common",   # the collectible Concept Card
    "meaning": "...", "example": "...", "remember": "..."},
}
```
Rarities used: Common / Uncommon / Rare (drives the card's CSS glow).

### 3b. `LOCATIONS["library"]` (metadata)
key, name "The Library", icon, tagline, topic, description, `order: 1`, `accent: "#d4a84b"`,
`theme: "archive"`, `interaction: "bookshelf"`, `books: LIBRARY_BOOKS`, a `guide_intro` line, a
3-step `atlas_steps` onboarding script (Professor Atlas explains the shelves → Concept Cards/Core →
the Trial), `learn_cards` (5 prose cards — in the Library these are **only** used for the Trial-gate
count "Study all 5 volumes"; the actual teaching is the books), and 5 `learning_objectives`.

### 3c. `QUIZZES["library"]` — the graded Trial bank
A **bank of 5 scenario questions** `lib_s1`…`lib_s5` (application, not recall). Each:
```python
{"key": "lib_s1", "question": "...",
 "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
 "correct": "A",                       # a LETTER
 "feedback_correct": "...", "feedback_wrong": "...",   # elaborative feedback on the results page
 "explanation": "...", "hint": "..."}                  # hint feeds Professor Atlas, never the answer
```
The Trial **draws `TRIAL_COUNT = 4` of the 5 at random per attempt** and grades only those 4.
`PASS_THRESHOLD = 3` (3/4 to pass). Option positions are shuffled on render (the `shuffle_options`
Jinja filter) but grading compares the option **letter**, so shuffling never changes the answer.

### 3d. `HOOKS["library"]` — guess-first priming (Learning Loop)
A list of 5 hooks, **aligned by index to `LIBRARY_BOOKS`**. Each `{question, options:[2-3], payoff}`.
Shown as a quick guess card **before** a not-yet-studied book's content. **Never logged, graded, or
gating** — pure pretesting-effect priming.

### 3e. `REFLECTION_PROMPTS["library"]`
`{"key": "narrow_vs_general", "text": "In one sentence: what's the difference between narrow AI and
general AI?"}` — offered once, after passing the Trial (see §7).

### 3f. Helper functions (in `game_content.py`)
- `build_library_shelves(items, rows=3, per_row=8, seed=7)` — lays out the bookcase: scatters the 5
  real books among `DECOY_TITLES` at **deterministic** positions (fixed seed → stable layout). Returns
  rows of `{type:'real'|'decoy', index, title, color, h, w}`.
- `select_trial_questions("library")` — randomly picks 4 of the 5 `lib_s*` keys (Library has no pinned
  questions). Stored per attempt so graded == shown.
- `get_questions_by_keys`, `grade_quiz` — grade only the shown subset; attach `feedback` per answer.

## 4. Template — `app/templates/game/location.html` (the `bookshelf` branch)
Rendered for `interaction == "bookshelf"`. Key pieces:
- **Atmosphere:** candle vignette (`.lib-vignette`), drifting dust (`#lib-dust`), mute toggle (`#lib-mute`).
- **Professor Atlas onboarding** overlay driven by `loc.atlas_steps` (skippable, typewriter).
- **Knowledge Core panel:** the orb (`#knowledge-core`) with a read counter (`#books-read` / `#books-total`),
  a fill bar (`#core-fill`), and the shelf hint (`#shelf-hint`).
- **3-column layout** (`.library-layout`):
  - **LEFT — Concept Deck** (`.concept-deck`): one `.flashcard[data-index]` per book, `locked` until
    that book is read; click a flipped card to see meaning/example/remember.
  - **CENTER — bookcase** (`.bookcase`): shelves of `.book-real[data-index]` (glowing tomes) and
    `.book-decoy` (flavour) from `build_library_shelves`.
  - **RIGHT — Trial gate** (`#trial-stage`): `#trial-gate` (locked message "Study all 5 volumes")
    swaps to `#trial-content` ("The Path is Open" + **Enter the Trial** → `game.trial`) once all read.
- **Book reader modal** (`#book-reader`, `data-loc="library"`): tome (`#book-tome`), page (`#book-page`),
  prev/next nav (`.book-reader-nav`), page indicator.
- **JSON data tags:** `#library-books` (the 5 books), `#library-read` (ids the user has already
  studied — per-user session), `#library-hooks` (the 5 hooks).
- **Scripts loaded:** `hooks.js`, `library-ambience.js`, `bookshelf.js` (+ `quiz.js`, `onboarding.js`,
  `reveal.js`, and `npc.js` only in the `game` condition).

## 5. The book reader — `app/static/js/bookshelf.js`
Drives the whole shelf. In-memory `completed` Set tracks which books are done (mirrored to the server —
see §8). Flow when you click a glowing tome:
1. **Book pull:** spine slides out, `LibFX.bookPull()` sound, then `openBook(i)`.
2. **Hook beat** (guess-first): if the book isn't completed and a hook exists, `AtlasHook.mount()`
   shows the guess card first; on continue → the reader renders page 0. (Completed books skip the hook.)
3. **Reader pages** (`render()`): `intro → concept → example` — body text **types in live**, `keywords`
   are highlighted, a **read-aloud** (Web Speech) button appears on taught pages; then the **quick-check**
   page; then the **reward** page.
4. **Quick-check** (`wireQuiz`): correct → `LibFX.correct()`, advance enabled; wrong → `LibFX.wrong()`
   and a "Read the Book Again" button (must re-read). This is a learning gate — **not logged**.
5. **Reward page:** "Concept Card Acquired" — plays `LibFX.reward()` (sparkle). "Add to Deck" →
   `completeBook(i)` then closes the reader.
6. **`completeBook(i)`:** marks the tome `studied`, unlocks its flashcard, bumps the read counter,
   charges the Core (`coreBurst` visual + `coreCharge` sound), **POSTs the read to the server**
   (`persistRead`), and when all 5 are done → `unlockTrial()` (celebration FX + hint update + reveal
   the Trial button).
- **Decoys:** `openDecoy()` shows random flavour text (no content).
- **Restore on load** (`restoreProgress`): reads `#library-read` and silently re-applies studied books,
  unlocked cards, Core fill, and the unlocked-Trial end state (no celebration replay) — so leaving for
  the Trial and coming back never resets your reading (see §8).

## 6. Audio & FX — `app/static/js/library-ambience.js` (`window.LibFX`)
Web Audio synth (no files except one mp3), all wrapped in try/catch. Also **auto-scales the shelf scene
to fit one screen** (non-scrolling) and spawns 30 dust motes; `#lib-mute` toggles sound.
- `bookPull` / `pageTurn` — real `book-open.mp3` (synth fallback), `correct` / `wrong` chimes,
  `atlasChime`, **`coreCharge`** (rising "charged" sweep), **`reward`** (bright card-acquire sparkle),
  `coreBurst` (visual sparks), `celebrate` (candle frenzy + gold shockwave on full completion).
- (Note: `coreCharge` and `reward` were wired into `completeBook`/the reward page in the Learning-Loop
  work — earlier they were defined-but-silent.)

## 7. The Trial (graded) & reflection
- **Enter:** `GET /location/library/trial` → `trial()` calls `select_trial_questions` (random 4 of 5),
  stores the shown keys in the session + a hidden form field, renders the shared `trial.html`
  (stepped one-question-at-a-time UI, `quiz.js`): instant feedback, floating XP, and **Professor Atlas
  hints** via `/npc/chat` (game condition only; Atlas never gives the answer).
- **Submit:** `POST /location/library/submit` → `submit_quiz()` grades **only the 4 shown**, writes one
  **`QuizAttempt`** row per question (with `npc_consulted`), updates **`LocationProgress`**
  (`best_score`, `passed`, `attempts_count`), grants achievements, and renders `results.html` with
  per-question elaborative feedback.
- **On PASS:** the results/celebration screen shows a one-time **reflection card** (the
  `narrow_vs_general` prompt) — "Seal it in the Atlas" saves a `Reflection` row (`skipped=False`),
  "Skip" saves `skipped=True`; shown at most once per user until a real (non-skipped) one exists.
  Ungraded; never blocks returning to the hub.

## 8. Reading-progress persistence (per-user, session)
The book-completion state is saved **per-user in the `book_reads` DB table** (survives logins), so a
failed Trial never forces a re-read:
- `POST /location/library/read` → `mark_read()` inserts a `BookRead` row (user_id, location, book id)
  (validated against real book ids). `bookshelf.js` calls this from `completeBook`.
- `location()` passes `read_books = library_read_ids("library")` → template `#library-read` →
  `restoreProgress()` re-applies it on load.
- Per-user by construction (DB rows keyed by user_id) — new users start empty automatically.
- This is **progress/presentation state, not research data** — it's never scored or logged to a table.

## 9. Routes — `app/routes/game.py`
- `GET  /location/library` → `location()` — books, shelves, `read_books`, `hooks`.
- `GET  /location/library/trial` → `trial()` — random 4-question draw.
- `POST /location/library/submit` → `submit_quiz()` — grade shown 4, log, update progress, reflection.
- `POST /location/library/read` → `mark_read()` — persist a studied book (session).
- `POST /location/library/reflect` → `reflect()` — save the post-Trial reflection.
- `POST /npc/chat` (blueprint `npc`) — Professor Atlas hints, **game condition only** (403 for control).

## 10. What is (and isn't) recorded as research data
**Logged:** `QuizAttempt` (per Trial question, incl. `npc_consulted`), `LocationProgress`
(passed/best_score/attempts), `Achievement` **`first_steps`** on pass, `Reflection` (post-Trial),
`NpcInteraction` (every Atlas chat), `GameSession` (time-on-task).
**NOT logged (deliberately):** the in-book quick-checks, the guess-first hooks, and the reading-progress
(`read_books`) — these are learning gates / priming / convenience state only.

## 11. Files that make up the Library
- `app/game_content.py` — `LIBRARY_BOOKS`, `LOCATIONS["library"]`, `QUIZZES["library"]`,
  `HOOKS["library"]`, `REFLECTION_PROMPTS["library"]`, `build_library_shelves`, `select_trial_questions`,
  `grade_quiz`, `DECOY_TITLES`.
- `app/templates/game/location.html` — the bookshelf scene + book reader (branch on `interaction`).
- `app/templates/game/trial.html`, `app/templates/game/results.html` — the graded Trial + results.
- `app/static/js/bookshelf.js` — reader, hooks, Core/cards, Trial unlock, read-progress restore.
- `app/static/js/library-ambience.js` — audio/FX (`window.LibFX`) + auto-fit + dust + mute.
- `app/static/js/hooks.js` (`AtlasHook`), `reflection.js` (post-Trial), `quiz.js` (Trial), `npc.js`,
  `onboarding.js`, `reveal.js`, `tts.js` (read-aloud).
- `app/routes/game.py` — the routes above; `app/services/progress.py` (unlock chain, `all_passed`);
  `app/services/achievements.py` (`first_steps`); `app/services/npc_service.py` (Atlas RAG:
  `COURSE_KNOWLEDGE["library"]`).
- `app/static/css/style.css` — `.theme-archive` scene, `.bookcase`/`.book-*`, `.knowledge-core`,
  `.concept-deck`/`.flashcard`, `.book-reader`, `.lh-hook` (hook card, amber via `--hook-accent`).

## 12. Guardrails (do not change without intent)
- Keep the **amber `#d4a84b`** accent and `theme-archive` scene (matches the hub's Library zone).
- The in-book quick-checks and hooks stay **ungraded/unlogged**; only the 4-question Trial is scored.
- Keep `PASS_THRESHOLD = 3`, `TRIAL_COUNT = 4`, the random draw, and per-question `QuizAttempt` logging.
- Professor Atlas is **game-condition only** and must never reveal a Trial answer.
