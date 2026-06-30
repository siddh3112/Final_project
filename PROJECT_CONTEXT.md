# Atlas Quest — Project Context

> Paste this whole file into a new Claude session to give it full context about the project.

## 1. What it is
**Atlas Quest** is a **gamified, web-based learning environment for AI literacy**, built as an **MSc dissertation artefact + research study**. It turns an IBM "Introduction to Artificial Intelligence" curriculum into an explorable fantasy world: a world-map hub with three themed locations, each teaching one strand of AI, each ending in a 4-question quiz ("Trial"), culminating in a 10-question post-test.

**Research aim:** a between-subjects experiment comparing a **`game` condition** (gamified UI + an AI tutor, "Professor Atlas") vs a **`control` condition**, studying whether game-based learning with an AI tutor improves AI-concept knowledge/engagement. Every user has a `condition` field; content is held constant, delivery is the independent variable. The most visible differentiator currently implemented is that **Professor Atlas (the AI tutor) appears only in the `game` condition**.

## 2. Tech stack
- **Language:** Python 3 (3.14).
- **Web framework:** Flask (application-factory + blueprints pattern).
- **DB/ORM:** Flask-SQLAlchemy over **SQLite** (`instance/atlas_quest.db`).
- **Auth/session:** Flask-Login; Werkzeug password hashing.
- **AI tutor:** **IBM Granite 3.3 8B** run locally via **Ollama** (HTTP API at `http://localhost:11434`), with lightweight RAG + a rule-based fallback.
- **Templating:** Jinja2 (server-side rendered HTML).
- **Frontend:** **vanilla JavaScript** (no frameworks), **HTML5 Canvas 2D** (constellation/particles), **Web Audio API** (synthesised sound + one mp3), **CSS3**, Bootstrap 5 + Bootstrap Icons, Google Fonts (Rye, Inter, Source Serif 4, Courier New).
- **Run:** `python run.py` → dev server on **`localhost:5001`** (5000 is taken by macOS AirPlay), Flask debug auto-reload.

## 3. Repository structure (key files)
```
run.py                      # entry point: create_app(), runs on :5001
main.py                     # unused/empty leftover
app/
  __init__.py               # app factory: config, db, login, blueprints, create_all, AUTH_DISABLED guest auto-login
  game_content.py           # LOCATIONS, QUIZZES, LIBRARY_BOOKS, GAME_INTRO_STEPS, LOCATION_ORDER, PASS_THRESHOLD, grade_quiz(), build_library_shelves()
  eval_content.py           # POST_TEST: the 10-question final assessment
  models/__init__.py        # SQLAlchemy db + 7 model classes (tables)
  routes/
    __init__.py             # empty package marker
    game.py                 # game_bp: hub, location, trial, submit_quiz
    auth.py                 # auth_bp (/auth): register, login, logout
    eval_routes.py          # eval_bp (/eval): post_test, submit_post_test
    npc.py                  # npc_bp (/npc): /npc/chat (Professor Atlas JSON endpoint)
  services/
    __init__.py             # empty package marker
    progress.py             # unlock chain + progress (UNLOCK_ALL flag)
    gamification.py         # computed XP/level/rank/badges
    achievements.py         # persisted achievements (grant_new, earned_map, 5 rules)
    npc_service.py          # Professor Atlas brain: Ollama/Granite + RAG + fallback
  templates/
    base.html               # shared skeleton
    game/hub.html           # world map landing page
    game/location.html      # Library (bookshelf) + generic paged layout
    game/terminal.html      # AI Lab (CRT terminal)
    game/observatory.html   # Observatory (constellation)
    game/trial.html         # stepped Trial quiz (Library/Observatory)
    game/results.html       # quiz results + celebration
    game/coming_soon.html, game/darkdata.html (unused)
    eval/post_test.html, eval/post_test_done.html
    auth/...
  static/
    css/style.css           # ~3400+ lines, all theming/animation
    js/                     # see section 8
    images/                 # images.jpeg (map), atlas-glyph.svg (Atlas icon)
    sounds/book-open.mp3
instance/atlas_quest.db     # the SQLite database (auto-created)
```

## 4. Configuration & TESTING FLAGS (important)
In `app/__init__.py`:
- `AUTH_DISABLED = True` → a `@before_request` **auto-logs-in a shared "guest" user** (condition="game") so you can test without registering. **Set False for real participants** (then real auth + random condition assignment is used).
- `OLLAMA_ENABLED = True`, `OLLAMA_BASE_URL = "http://localhost:11434"`, `OLLAMA_MODEL = "granite3.3:8b"`, `OLLAMA_TIMEOUT = 30`.
- `SQLALCHEMY_DATABASE_URI = "sqlite:///atlas_quest.db"`, `SECRET_KEY` (dev).

In `app/services/progress.py`:
- `UNLOCK_ALL = True` → opens every location regardless of progress (for testing). **Set False to restore the unlock chain** for participants.

`db.create_all()` runs in `create_app()` → tables auto-created on startup.

## 5. Database (7 tables, `app/models/__init__.py`)
- **users**: id, username, email, password_hash, **condition** ("game"|"control"), post_test_done, created_at.
- **game_sessions**: id, user_id, location, started_at, ended_at. (time-on-task)
- **npc_interactions**: id, user_id, session_id, location, user_message, npc_response, response_time_ms, **is_fallback**, created_at. (every Professor Atlas chat)
- **quiz_attempts**: id, user_id, location, question_key, selected_answer, is_correct, attempt_number, **npc_consulted**, created_at. (one row per question answered)
- **knowledge_tests**: id, user_id, answers_json, score, created_at. (post-test results)
- **location_progress**: id, user_id, location, passed, best_score, attempts_count, unlocked_at.
- **achievements**: id, user_id, achievement_key, earned_at.

Research measures = quiz_attempts, npc_interactions, knowledge_tests, achievements, game_sessions, compared across `users.condition`.

## 6. Routes (controllers)
- **game** (`game.py`):
  - `GET /` → `hub()` — world map; passes stats (gamification_summary), progress map, badges, new achievements (for popup).
  - `GET /location/<key>` → `location()` — branches by `interaction`: `"bookshelf"`→location.html (Library), `"terminal"`→terminal.html (AI Lab), `"constellation"`→observatory.html, else paged lessons.
  - `GET /location/<key>/trial` → `trial()` — renders trial.html (Library/Observatory quiz).
  - `POST /location/<key>/submit` → `submit_quiz()` — grades, logs QuizAttempt per question, updates LocationProgress, grants achievements, renders results.html.
- **auth** (`auth.py`, prefix `/auth`): register, login, logout (used when AUTH_DISABLED off; assigns condition).
- **eval** (`eval_routes.py`, prefix `/eval`): `GET /eval/post-test` (gated until all 3 passed), `POST /eval/post-test/submit` (scores, saves KnowledgeTest, sets post_test_done, grants Atlas Sage).
- **npc** (`npc.py`, prefix `/npc`): `POST /npc/chat` — calls npc_service, returns JSON `{response, is_fallback}`, logs NpcInteraction.

## 7. The three location experiences (bespoke interactive scenes, each themed to its hub-map zone)
- **📚 The Library** (key `library`, theme `archive`, accent amber **#d4a84b**, topic "What is AI"): interactive **bookshelf** of aged leather books; 5 "glowing tomes" hold content among decoys; click → multi-page **book reader** (intro→concept→example→quick-check→reward); **Knowledge Core** charges; **Concept Deck** flashcards; candlelight/dust atmosphere; real book-open sound. Auto-scales to fit one screen (non-scrolling).
- **🔬 The AI Lab** (key `ai_lab`, theme `lab`, accent industrial blue-grey **#8ab4d4**, topic data/history of computing): whole screen is a **CRT monitor** with **power-on sequence**, scanlines; mission briefing → typewriter "sector" cards; 4 **physical toggle switches**; an **interactive data-sorting machine** (drag items into Structured/Semi/Unstructured bins → feeds quiz Q3); **ticker-tape quiz** with console buttons; synthesised Web-Audio sounds; mute toggle. Professor Atlas = a CRT mini-monitor with an ASCII face.
- **🔭 The Observatory** (key `observatory`, theme `cosmos`, accent cyan **#3ab8d8**, topic Machine Learning): a **single constellation built one star at a time** — you see one star, complete its concept + an inline check question, then the next star appears and a line connects to it (constellation forms as you go). Living sky: 3-layer parallax stars, nebulae, shooting stars, cursor stardust; cinematic intro typed on the sky; finale + unlock cinematic when all 5 mapped; mute toggle.

Inline "quick check" / "check" questions in each location are **learning gates only — NOT logged** as quiz attempts. Only the formal 4-question Trials and the 10-question post-test are recorded.

## 8. Frontend JavaScript (`app/static/js/`)
- `bookshelf.js` — Library book reader (pages, typed text, quick-check, Knowledge Core, unlock Trial; calls window.LibFX for sound).
- `library-ambience.js` — Library audio (Web Audio) + auto-scale-to-fit (no scroll); exposes window.LibFX.
- `terminal.js` — AI Lab: power-on, typewriter, screen-roll, sorting machine, ticker-tape quiz, sounds, mute (all audio routed through a master gain).
- `observatory.js` — Observatory: canvas constellation, progressive reveal+connect, discovery sequence, inline check questions, sounds, mute, cinematic intro/unlock.
- `quiz.js` — stepped Trial quiz (one question at a time, instant feedback, floating XP, hints via /npc/chat).
- `npc.js` — Professor Atlas floating chat widget; POSTs to /npc/chat (AJAX), renders replies.
- `achievements.js` — achievement unlock popups (golden particles + Web-Audio chime, queued).
- `hub-onboard.js` — hub: applies pin positions from data-x/data-y, fills XP bar, runs How-to-Play tutorial.
- `lesson.js`, `reveal.js`, `onboarding.js`, `celebration.js` — paged lessons, scroll reveals, onboarding overlays, win celebration.
- `darkdata.js` — unused (old AI Lab concept).

## 9. Professor Atlas (the AI tutor) — `app/services/npc_service.py`
- Icon: a **telescope-and-stars SVG glyph** (`static/images/atlas-glyph.svg`) that recolours to each location's accent (amber Library / blue-grey AI Lab / cyan Observatory) — replaced the original owl emoji.
- `get_response(location, message, ollama_enabled)` returns `(text, is_fallback)`.
- If `ollama_enabled`: `_query_ollama()` does `requests.post("http://localhost:11434/api/chat", {model:"granite3.3:8b", messages:[system,user]})`. **RAG:** the location's course text (`COURSE_KNOWLEDGE`) is injected into a locked-down `SYSTEM_PROMPT` (answer only from that content, never give quiz answers, stay in character, 2–4 sentences). Returns `is_fallback=False`.
- **Fallback** (LLM down/error, or OLLAMA_ENABLED False): rule-based keyword responses (`KEYWORDS`) + Socratic deflections for answer-seeking; generic fallback returns `is_fallback=True`.
- Verified working live: Ollama up with granite3.3:8b; novel question returned `is_fallback:false`.

## 10. Gamification (`app/services/gamification.py`) — computed, not stored
- XP: `XP_PER_CORRECT=25`, `XP_LOCATION_BONUS=100`, `XP_PER_POSTTEST_CORRECT=30`. Level: `XP_PER_LEVEL=200`.
- Ranks: `["Novice Explorer","Apprentice","Scholar","Master Cartographer"]` by locations passed; `"Atlas Sage"` after post-test.
- `gamification_summary(user)` → level, rank, xp, level_pct, passed_count, badges, badges_earned/total.

## 11. Achievements (`app/services/achievements.py`) — persisted to `achievements` table
5 achievements, granted once each (idempotent `grant_new()` returns newly-earned keys; hub pops a celebration):
- `first_steps` (👟) — Library passed.
- `field_researcher` (🛰️) — AI Lab passed.
- `stargazer` (✨) — Observatory passed.
- `flawless` (💎) — any Trial passed **4/4 on first attempt (attempt_number==1) with no hints (npc_consulted all False)**.
- `atlas_sage` (🏆) — post_test_done.
Triggered after `submit_quiz` and `submit_post_test`; defensively re-checked on hub load. Hub shows count `X / 5 ACHIEVEMENTS`, tooltips, "NEW" pulse, and a centre-screen popup (particles + chime) for newly-earned ones (passed via session → hub).

## 12. Content (`app/game_content.py`, `app/eval_content.py`)
- `LOCATION_ORDER = ["library","ai_lab","observatory"]`, `PASS_THRESHOLD = 3` (3/4 to pass a Trial).
- `LOCATIONS` dict: per-location key/name/icon/tagline/topic/accent/theme/interaction/learn_cards/atlas_steps/learning_objectives (+ Library books).
- `QUIZZES`: 4 MCQs per location (keys like lib_q1..q4, lab_q1..q4 with lab_q3 = the sorting question, obs_q1..q4).
- `POST_TEST`: 10 MCQs (the research learning measure).
- Helpers: `grade_quiz()`, `build_library_shelves(items, rows=3, per_row=8)`.

## 13. Known caveats / not-yet-done (be honest in the writeup)
- `AUTH_DISABLED=True` and `UNLOCK_ALL=True` are **testing flags** — must be turned off before running participants (enable real auth + random condition assignment + the unlock chain).
- The **`control` condition** currently shares the gamified UI; the implemented differentiator is the AI tutor being game-only — the exact "control" treatment should be defined.
- **Final Assessment** location is not a bespoke build; planned theme **royal purple #8a5cf0 + gold**.
- Inline check questions are gates, not logged data.
- Study currently has a **post-test only** (no pre-test/baseline) — a design decision to confirm with the supervisor.

## 14. How to run
1. Ensure Ollama is running with the model: `ollama run granite3.3:8b` (or `ollama list` to confirm).
2. `python run.py`
3. Open `http://localhost:5001/`.
