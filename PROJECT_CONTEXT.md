# Atlas Quest — Project Context

> Paste this whole file into a new Claude session to give it full, current context about the project.
> Last updated to reflect: scenario question banks, the "Final Ascent" post-test, Settings/prefs, the personal leaderboard, and the HUD-completion logic.

## 1. What it is
**Atlas Quest** is a **gamified, web-based learning environment for AI literacy**, built as an **MSc dissertation artefact + research study**. It turns an IBM "Introduction to Artificial Intelligence" curriculum into an explorable fantasy world: a world-map hub with three themed locations, each teaching one strand of AI, each ending in a 4-question quiz ("Trial"), culminating in a cinematic 10-question post-test ("The Final Ascent").

**Research aim:** a between-subjects experiment comparing a **`game` condition** (gamified UI + an AI tutor, "Professor Atlas") vs a **`control` condition**, studying whether game-based learning with an AI tutor improves AI-concept knowledge/engagement. Every user has a `condition` field; content is held constant, delivery is the independent variable. The most visible differentiator currently implemented is that **Professor Atlas (the AI tutor) appears only in the `game` condition** (`/npc/chat` returns 403 for control).

## 2. Tech stack
- **Language:** Python 3 (works on 3.12–3.14).
- **Web framework:** Flask (application-factory + blueprints pattern).
- **DB/ORM:** Flask-SQLAlchemy over **SQLite** (`instance/atlas_quest.db`).
- **Auth/session:** Flask-Login; Werkzeug password hashing; Flask server-side session for per-attempt state and prefs.
- **AI tutor:** **IBM Granite 3.3 8B** run locally via **Ollama** (HTTP API at `http://localhost:11434`), with lightweight RAG + a rule-based fallback.
- **Templating:** Jinja2 (server-side rendered HTML); a custom `shuffle_options` Jinja filter randomises answer positions.
- **Frontend:** **vanilla JavaScript** (no frameworks), **HTML5 Canvas 2D**, **Web Audio API** (synth SFX + one mp3), **Web Speech API** (optional read-aloud), **CSS3** with CSS custom properties, Bootstrap 5 + Bootstrap Icons, Google Fonts.
- **Run:** `python run.py` → dev server on **`localhost:5001`** (5000 is taken by macOS AirPlay), Flask debug auto-reload. `requirements.txt`: flask, flask-sqlalchemy, flask-login, werkzeug, requests.

## 3. Repository structure (key files)
```
run.py                      # entry point: create_app(), app.run(debug=True, port=5001)
PROJECT_CONTEXT.md          # this file
app/
  __init__.py               # app factory: config, db, login, blueprints, create_all + guarded migration,
                            #   AUTH_DISABLED guest auto-login, shuffle_options filter, prefs context processor
  game_content.py           # LOCATIONS, LIBRARY_BOOKS, QUIZZES (scenario banks), GAME_INTRO_STEPS,
                            #   LOCATION_ORDER, PASS_THRESHOLD, TRIAL_COUNT, PINNED_QUESTIONS,
                            #   select_trial_questions(), get_questions_by_keys(), grade_quiz(),
                            #   build_library_shelves()
  eval_content.py           # POST_TEST (10 Qs, each with chapter + explanation), CHAPTER_TITLES
  prefs.py                  # session-based front-of-house prefs (sound/voice/reduce_motion/large_text)
  models/__init__.py        # SQLAlchemy db + 7 model classes (tables)
  routes/
    game.py                 # game_bp: hub, location, trial, submit_quiz, /prefs
    auth.py                 # auth_bp (/auth): register, login, logout
    eval_routes.py          # eval_bp (/eval): post_test, submit_post_test (+ POSTTEST_REPLAYABLE)
    npc.py                  # npc_bp (/npc): /npc/chat (Professor Atlas JSON endpoint, game-only)
  services/
    progress.py             # unlock chain + progress (UNLOCK_ALL flag)
    gamification.py         # computed XP/level/rank/badges + journey_complete
    achievements.py         # persisted achievements (grant_new, earned_map, 4 rules)
    leaderboard.py          # personal best-runs: combined_score, record_run, user_runs, run_stats
    npc_service.py          # Professor Atlas brain: Ollama/Granite + RAG + fallback + ZPD scaffolding
  templates/
    base.html
    game/hub.html           # world map landing page: map, HUD, badges, settings panel, leaderboard panel
    game/location.html      # Library (bookshelf) + generic paged layout
    game/terminal.html      # AI Lab (CRT terminal), embeds the Trial
    game/observatory.html   # Observatory (constellation)
    game/trial.html         # stepped Trial quiz (Library/Observatory)
    game/results.html       # quiz results + celebration + elaborative feedback
    game/coming_soon.html, game/darkdata.html   # unused
    eval/post_test.html     # "The Final Ascent" (instructions → chapters → Back/Forward questions)
    eval/post_test_done.html# cinematic results reveal + per-question review + personal-best banner
    auth/login.html, auth/register.html
  static/
    css/style.css           # ~3400+ lines, all theming/animation; canonical palette vars in :root
    js/                     # see section 9
    images/ (images.jpeg map, atlas-glyph.svg), sounds/book-open.mp3
instance/atlas_quest.db     # the SQLite database (auto-created; gitignored)
final quiz/                 # design reference screenshots (not code)
```

## 4. Configuration & TESTING FLAGS (important — flip these for the real study)
- `app/__init__.py`: **`AUTH_DISABLED = True`** → a `@before_request` **auto-logs-in a single shared "guest" user** (condition="game") so you can test without registering. **Set False for real participants** (real auth + condition assignment).
- `app/services/progress.py`: **`UNLOCK_ALL = True`** → opens every location regardless of progress. **Set False** to restore the "pass the previous location to unlock the next" chain.
- `app/routes/eval_routes.py`: **`POSTTEST_REPLAYABLE = True`** → lets the post-test be re-taken repeatedly (so the results page can be exercised). **Set False** for the real single-attempt research measure.
- Ollama config (in `create_app`): `OLLAMA_ENABLED = True`, `OLLAMA_BASE_URL = "http://localhost:11434"`, `OLLAMA_MODEL = "granite3.3:8b"`, `OLLAMA_TIMEOUT = 30`.
- `SQLALCHEMY_DATABASE_URI = "sqlite:///atlas_quest.db"`, dev `SECRET_KEY`.
- On startup, `create_app()` runs `db.create_all()` then `_ensure_sqlite_columns()` — a **guarded migration** (PRAGMA table_info + ALTER TABLE) that adds missing nullable columns, because `create_all` never ALTERs existing tables. Currently it ensures `knowledge_tests.time_spent_seconds`.

## 5. Database (10 tables, `app/models/__init__.py`)
- **users**: id, username, email, password_hash, **condition** ("game"|"control"), post_test_done, created_at.
- **game_sessions**: id, user_id, location, started_at, ended_at. (time-on-task)
- **npc_interactions**: id, user_id, session_id, location, user_message, npc_response, response_time_ms, **is_fallback**, created_at. (every Professor Atlas chat)
- **quiz_attempts**: id, user_id, location, question_key, selected_answer, is_correct, attempt_number, **npc_consulted**, created_at. (one row per graded Trial question answered)
- **knowledge_tests**: id, user_id, answers_json, score, **time_spent_seconds** (nullable, silent telemetry), created_at. (post-test results)
- **location_progress**: id, user_id, location, passed, best_score, attempts_count, unlocked_at.
- **achievements**: id, user_id, achievement_key, earned_at.
- **run_history**: id, user_id, combined_score, post_test_score, post_test_max, library_score, ai_lab_score, observatory_score, badges_count, time_spent_seconds (nullable), xp, rank, created_at. (one row per completed post-test — the **personal** best-runs leaderboard; never cross-user or by-condition.)

Research measures = quiz_attempts, npc_interactions, knowledge_tests, achievements, game_sessions, compared across `users.condition`. run_history and time_spent_seconds are **additive telemetry** and never affect scoring.

## 6. Routes (controllers)
- **game** (`game.py`):
  - `GET /` → `hub()` — world map. Computes `stats=gamification_summary`, `badge_detail` (read-only detail for earned badges), `pmap=progress_map`, `runs=user_runs`, `run_stats`; shows post-test pin when unlocked (and, while `POSTTEST_REPLAYABLE`, even after completion); pops any newly-earned achievements from the session for the celebration popup.
  - `POST /prefs` → `save_prefs()` — persists front-of-house prefs to the session (audio/accessibility only; never scoring/research).
  - `GET /location/<key>` → `location()` — branches by `interaction`: `"bookshelf"`→location.html (Library), `"terminal"`→terminal.html (AI Lab; also selects + embeds that attempt's Trial questions), `"constellation"`→observatory.html, else paged lessons.
  - `GET /location/<key>/trial` → `trial()` — **draws this attempt's questions at random** via `select_trial_questions`, stores them in `session["shown_<key>"]`, renders trial.html with a hidden `shown_keys` field.
  - `POST /location/<key>/submit` → `submit_quiz()` — grades ONLY the shown subset (hidden field is authoritative, then session, then whole bank), logs one QuizAttempt per shown question (with `npc_consulted` per-question), updates LocationProgress (best_score/passed/attempts), grants achievements, renders results.html.
- **auth** (`auth.py`, prefix `/auth`): register, login, logout (used when AUTH_DISABLED off; assigns condition).
- **eval** (`eval_routes.py`, prefix `/eval`): `GET /eval/post-test` (gated until all 3 passed; single-attempt unless POSTTEST_REPLAYABLE), `POST /eval/post-test/submit` (scores by question key, saves KnowledgeTest + time, sets post_test_done, grants Atlas Sage, records a RunHistory row, builds the per-question review).
- **npc** (`npc.py`, prefix `/npc`): `POST /npc/chat` — **403 unless condition=="game"**; calls npc_service with recent-mistake stems + last-3-turns history, returns JSON `{response, is_fallback}`, logs NpcInteraction.

## 7. The three location experiences (bespoke interactive scenes, each themed to its hub-map zone)
> **Colour rule (do NOT change without explicit instruction):** each location's interior must match its hub-map zone accent. Library **#d4a84b** (amber), AI Lab **#3fd0e0** (cyan), Observatory **#3ab8d8** (cyan-blue). The Final Assessment zone is royal purple **#8a5cf0** + gold **#f0c96b**.
- **📚 The Library** (`library`, theme `archive`, "What is AI"): interactive **bookshelf** of aged books; 5 "glowing tomes" (`LIBRARY_BOOKS`) hold multi-page lessons (intro→concept→example→quick-check→flashcard reward) among decoys; **Knowledge Core** charges as you read; **Concept Deck** flashcards; candlelight/dust; real book-open sound; auto-scales to one non-scrolling screen.
- **🔬 The AI Lab** (`ai_lab`, theme `lab`, "Three Eras of Computing & Data"): the whole screen is a **CRT monitor** with power-on sequence + scanlines; typewriter "sector" cards; toggle switches; an **interactive data-sorting machine** (drag items into Structured/Semi/Unstructured bins) that feeds the pinned quiz question `lab_q3`; ticker-tape Trial with console buttons; synthesised Web-Audio SFX; mute toggle.
- **🔭 The Observatory** (`observatory`, theme `cosmos`, "Machine Learning"): a **single constellation built one star at a time** — reveal a star, complete its concept + inline check, the next star appears and a line connects them; parallax star layers, nebulae, shooting stars, cursor stardust; cinematic intro + unlock finale; mute toggle.

Inline "quick check"/"check" questions inside locations are **learning gates only — NOT logged** as quiz attempts. Only the formal 4-question Trials and the 10-question post-test are recorded.

## 8. Content model & the scenario question banks (`app/game_content.py`)
- `LOCATION_ORDER = ["library","ai_lab","observatory"]`; `PASS_THRESHOLD = 3` (3/4 to pass a Trial); `TRIAL_COUNT = 4`.
- `LOCATIONS` dict: per-location key/name/icon/tagline/topic/description/accent/theme/interaction/learn_cards/learning_objectives (+ Library `books`).
- **`QUIZZES` are scenario BANKS, not fixed 4-question sets:**
  - `library`: `lib_s1`–`lib_s5` (5 application scenarios).
  - `ai_lab`: `lab_q3` (the data-sorting diagnostic, **pinned + `no_shuffle`**) plus `lab_s1`–`lab_s5`.
  - `observatory`: `obs_s1`–`obs_s6`.
  - Every question has `options` (dict A–D), `correct` (a letter), `feedback_correct`, `feedback_wrong`, `explanation`, `hint`.
- **Per-attempt selection**: `select_trial_questions(key)` includes any `PINNED_QUESTIONS[key]` first (AI Lab pins `lab_q3`), then randomly samples the rest up to `TRIAL_COUNT=4`. The exact keys are stored in the session (and a hidden form field) so **the graded set == the shown set**. `grade_quiz(key, submitted, shown_keys)` grades only that subset and attaches the right elaborative `feedback`.
- `POST_TEST` (`eval_content.py`): 10 MCQs (`p1`–`p10`), each tagged with a `chapter` (1–4) and an `explanation`. `CHAPTER_TITLES = {1:"Foundations", 2:"The Data Deep", 3:"The Learning Machines", 4:"Final Synthesis"}`. Chapter tags/order are **presentation only** — scoring reads answers by question key.
- **Answer-position shuffling**: the `shuffle_options` Jinja filter (in `app/__init__.py`) randomises display order per render while keeping each option's original letter as its submit value, so grading is unaffected. It intentionally does **not** shuffle questions marked `ordered`/`no_shuffle` or any with an "…of the above" option.

## 9. Frontend JavaScript (`app/static/js/`)
- `bookshelf.js` / `library-ambience.js` — Library book reader + audio/auto-scale (`window.LibFX`).
- `terminal.js` — AI Lab: power-on, typewriter, sorting machine, ticker-tape Trial, SFX, mute.
- `observatory.js` — Observatory: canvas constellation, progressive reveal+connect, inline checks, cinematic intro/unlock, mute.
- `quiz.js` — stepped Trial quiz (one question at a time, instant feedback, floating XP, hints via `/npc/chat`).
- `ascent.js` — **The Final Ascent**: (A) the flow — instructions → Back/Forward questions (no auto-advance, answers editable), forward-only chapter cards, silent per-question + total timing written to hidden fields on submit; (B) the results reveal — frame-based score/XP count-up (~0.7s), Atlas Sage unlock, seal, particles, personal-best banner, per-question review. **Intentionally silent; no Professor Atlas.**
- `npc.js` — Professor Atlas floating chat widget (AJAX to `/npc/chat`).
- `settings.js` + `prefs.js` — Settings slide-in panel; `AtlasPrefs` posts to `/prefs` (session-persisted, no localStorage).
- `leaderboard.js` — personal best-runs slide-in panel (mirrors settings.js).
- `achievements.js` — achievement unlock popups (particles + chime, queued).
- `hub-onboard.js` — hub pin positions, XP bar, How-to-Play tutorial.
- `tts.js` — optional Web-Speech read-aloud (`AtlasVoice`), gated by the `voice` pref.
- `lesson.js`, `reveal.js`, `onboarding.js`, `celebration.js` — paged lessons, scroll reveals, overlays, win celebration. `darkdata.js` — unused.

## 10. Professor Atlas (the AI tutor) — `app/services/npc_service.py`
- Icon: a telescope-and-stars SVG glyph (`static/images/atlas-glyph.svg`) recoloured per location accent.
- `get_response(location, message, ollama_enabled, recent_mistakes, history)` → `(text, is_fallback)`.
- If `ollama_enabled`: `_query_ollama()` POSTs to `…/api/chat` with `granite3.3:8b`. **RAG:** the location's `COURSE_KNOWLEDGE` is injected into a locked-down `SYSTEM_PROMPT` (answer ONLY from that content; if out of scope say the exact fallback line; never give quiz answers; stay in character; 2–4 sentences). Returns `is_fallback=False`.
- **Adaptive tutoring (ZPD):** the route passes up to 5 recent **question STEMS the learner got wrong** (options/answers stripped — never leaks the answer) plus the **last 3 dialogue turns**; these are appended to the system prompt / message list to scaffold.
- **Fallback** (LLM down/error, or OLLAMA_ENABLED False): rule-based keyword explanations + Socratic deflections for answer-seeking; a generic miss returns `is_fallback=True` (useful research signal).

## 11. Gamification (`app/services/gamification.py`) — computed on the fly, not stored
- XP: `XP_PER_CORRECT=25` (best attempt), `XP_LOCATION_BONUS=100` per passed location, `XP_PER_POSTTEST_CORRECT=30`. Level: `XP_PER_LEVEL=200`.
- Ranks by locations passed: `["Novice Explorer","Apprentice","Scholar","Master Cartographer"]`; `"Atlas Sage"` after the post-test.
- `gamification_summary(user)` returns xp, level, level_pct, xp_into_level, rank, passed_count, badges, badges_earned/total, and the **journey** fields.
- **Journey / HUD-completion logic:** `journey_total = 3 locations + 1 (post-test) = 4`; `journey_done = passed_count + (1 if post_test_done)`. When `journey_complete` (everything done), the summary forces `level_pct=100` and the HUD shows **MAX / "✓ All levels mastered" / full gold bar** instead of a misleading "X/200 to next level". While in progress it shows the normal level + "X/200 to next level".

## 12. Achievements (`app/services/achievements.py`) — persisted to `achievements` table (4 badges)
Granted once each; `grant_new()` is idempotent and returns newly-earned keys (hub pops a celebration). **Flawless was removed** — achievements are now **4/4**:
- `first_steps` (👟) — Library passed.
- `field_researcher` (🛰️) — AI Lab passed.
- `stargazer` (✨) — Observatory passed.
- `atlas_sage` (🏆) — post_test_done.
Triggered after `submit_quiz`/`submit_post_test`, and defensively re-checked on hub load. Hub shows `X / 4 ACHIEVEMENTS`, per-badge detail cards (best score, attempts, rank), a "NEW" pulse, and a centre-screen popup for newly-earned ones.

## 13. Personal leaderboard (`app/services/leaderboard.py`) — PER-USER only
- `combined_score = post_test*10 + sum(location best scores)*5 + badges*15 + speed_bonus` (speed bonus capped at 20; a light tiebreaker; 0 if time unknown). Max ≈ 240.
- `record_run(...)` inserts one `run_history` row per completed post-test and reports `is_personal_best` (strictly greater than previous best; first run always counts).
- `user_runs(user)` returns that user's runs best→worst then recent; `run_stats(user)` gives best score / best post-test / fastest / total. **Never joins users, never ranks across users or by condition.** The trophy button on the hub opens the board; results page shows a personal-best celebration.

## 14. Settings & preferences (`app/prefs.py`, `/prefs` route)
Front-of-house presentation prefs stored in the **Flask session** (not localStorage): `sound`, `voice`, `reduce_motion`, `large_text` (all booleans). A context processor injects `prefs` (and `auth_disabled`) into every template. These **never** touch scoring, progress, unlocking, achievements, condition, or research data. `prefers-reduced-motion` is also respected throughout the JS.

## 15. Known caveats / not-yet-done (be honest in any writeup)
- `AUTH_DISABLED`, `UNLOCK_ALL`, `POSTTEST_REPLAYABLE` are **testing flags** — must be turned off before running participants (real auth + random condition assignment + unlock chain + single-attempt post-test).
- The **`control` condition** currently shares the gamified UI; the implemented differentiator is that the AI tutor is game-only — the exact "control" treatment should be finalised with the supervisor.
- The **Final Assessment** is the "Final Ascent" flow (purple + gold) but is not a bespoke explorable scene like the three locations.
- Inline check questions are gates, not logged data.
- Study currently has a **post-test only** (no pre-test/baseline) — a design decision to confirm with the supervisor.

## 16. How to run
1. Ensure Ollama is running with the model: `ollama list` (pull with `ollama pull granite3.3:8b` if missing). The app still works without it — Professor Atlas falls back to rule-based replies.
2. `python run.py`
3. Open `http://localhost:5001/`. With `AUTH_DISABLED=True` you land straight in as the shared "guest" user.
