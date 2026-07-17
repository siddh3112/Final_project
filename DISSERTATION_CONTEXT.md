# Atlas Quest — Dissertation Technical Inventory

**Purpose.** A factual, verbatim-where-asked inventory of what the Atlas Quest
code *actually does right now* (working tree at the time of writing), for use as
raw material in an MSc dissertation. This is not prose for the report. Where a
value could not be determined it is marked **UNKNOWN**. Where a comment or a
project note contradicts the code, both are reported and the authoritative one is
named. File references use `path:line`.

> Method note: facts were read from the source in the working tree; installed
> package versions were read from the running Python environment. The commit
> state is the `main` branch with the uncommitted working-tree changes listed in
> the repo status.

---

## 1. Ground truth on open questions

### 1.1 Is there a pre-test?
**No stored, graded pre-test / baseline measure exists.** The only graded
knowledge test persisted to the database is the single post-test. This is stated
in the code: *"This is the ONLY knowledge test in the study."*
([app/eval_content.py:1-6](app/eval_content.py#L1-L6)). No route, template, or
table implements a pre-test (searched: no `pre-test`/`pretest`/`baseline` route,
template, or model).

**However — and this corrects a naïve "no" — there ARE questions posed to the
learner before the lesson content and before the Trial.** They are *not* a
research pre-test; none is stored, scored, or gating:

- **Guess-first "hooks"** — a curiosity question shown *before* each lesson
  chunk ("Before you begin — a quick guess"). The client code states plainly:
  *"NOTHING here is logged, graded, or gating — tapping through is fine"*
  ([app/static/js/hooks.js:7-8](app/static/js/hooks.js#L7-L8)) and, at the guess
  handler, `guessed = true; // records NOTHING — priming only`
  ([app/static/js/hooks.js:77](app/static/js/hooks.js#L77)). Server-side the
  `HOOKS` data is described as *"Presentation/qualitative-data layer only. Hooks
  are NEVER logged, graded, or gating"*
  ([app/game_content.py:935-951](app/game_content.py#L935-L951)). They are passed
  to templates for rendering ([app/routes/game.py:248](app/routes/game.py#L248))
  but **no route accepts a hook answer back** — there is no endpoint that stores
  a guess. Counts: 25 hooks total — library 5, chronicle 6, ai_lab 4,
  observatory 10 ([app/game_content.py:951-1035](app/game_content.py#L951-L1035)).
- **Inline "quick-checks"** during learning — one per Library book (5), one per
  Chronicle timeline beat (6), one per Observatory constellation star (10).
  These gate progress *within* a location on the client (they reveal the "Enter
  the Trial" affordance) but are **not logged**: *"Inline 'quick check' … are
  learning gates only — NOT logged"* (project note,
  [PROJECT_CONTEXT.md:103](PROJECT_CONTEXT.md#L103); consistent with the code —
  no route records them).

**Bottom line:** there is *priming* and *formative* questioning before the graded
Trial, but no summative pre-test instrument. If the dissertation needs a
pre/post gain score, the current build provides only the post measure.

### 1.2 Single-condition or two-condition? What does `control` receive?
**Single-condition in practice, right now.** Registration always assigns
`condition = "game"`: `_assign_condition()` is literally `return "game"`
([app/routes/auth.py:31](app/routes/auth.py#L31)), with the original balanced
random allocation preserved as commented code
([app/routes/auth.py:32-39](app/routes/auth.py#L32-L39)). The `condition` column
defaults to `"game"` ([app/models/__init__.py:25](app/models/__init__.py#L25)).

The **only implemented behavioural difference** between `game` and `control` is
Professor Atlas: `/npc/chat` aborts `403` unless `condition == "game"`
([app/routes/npc.py:17-19](app/routes/npc.py#L17-L19)). So a `control` user would
receive an identical gamified UI but **no AI tutor**. The two-condition machinery
(the `CONDITIONS` tuple, the column, template gates, the 403) is intact and
described as *"retained but DORMANT"* and *"REVERSIBLE"*
([app/routes/auth.py:10-31](app/routes/auth.py#L10-L31)).

**Is the control path reachable?** The *gate* is reachable and enforced (a user
whose `condition` is manually set to `"control"` is refused Atlas, proven by a
test, [tests/test_eval.py:303-307](tests/test_eval.py#L303-L307)). But **no
control user is ever created** through the app — registration only ever assigns
`"game"`, and no route can change a condition
([tests/test_integration_auth.py:82-93](tests/test_integration_auth.py#L82-L93)).
So the two-group study cannot actually be *run* without a code change.

### 1.3 Exactly how many locations, in `LOCATION_ORDER`?
**Four**, in this order ([app/game_content.py:13](app/game_content.py#L13)):
`["library", "chronicle", "ai_lab", "observatory"]` — display names **The
Library**, **The Chronicle**, **The AI Lab**, **The Observatory**. The Final
Assessment is **not** a location: it is a pseudo-location key `"assessment"`
deliberately absent from `LOCATION_ORDER`
([app/routes/eval_routes.py:28-32](app/routes/eval_routes.py#L28-L32)).

### 1.4 Which Granite model tag is configured, and where?
`granite3.3:8b`, set at [app/__init__.py:61](app/__init__.py#L61)
(`app.config["OLLAMA_MODEL"] = "granite3.3:8b"`). The same tag is the hard-coded
fallback default inside the query function
([app/services/npc_service.py:435](app/services/npc_service.py#L435)).

### 1.5 Current state of every testing/config flag
| Flag | Value today | Location |
|---|---|---|
| `AUTH_DISABLED` | **False** | [app/__init__.py:33](app/__init__.py#L33) |
| `OLLAMA_ENABLED` | **True** (default config; tests override to False) | [app/__init__.py:59](app/__init__.py#L59) |
| `UNLOCK_ALL` | **False** | [app/services/progress.py:18](app/services/progress.py#L18) |
| `POSTTEST_REPLAYABLE` | **Does not exist** | — |
| `OLLAMA_BASE_URL` | `"http://localhost:11434"` | [app/__init__.py:60](app/__init__.py#L60) |
| `OLLAMA_MODEL` | `"granite3.3:8b"` | [app/__init__.py:61](app/__init__.py#L61) |
| `OLLAMA_TIMEOUT` | `30` (seconds) | [app/__init__.py:62](app/__init__.py#L62) |

`POSTTEST_REPLAYABLE` is **not present anywhere in the codebase** (grep returns
nothing in `app/`). It is referenced only in the stale
[PROJECT_CONTEXT.md:69](PROJECT_CONTEXT.md#L69). The current build enforces a
genuine single-attempt post-test (see §6) instead of a replay flag —
authoritative source is the code.

### 1.6 How many database tables exist? (resolving 10 vs 11)
**Eleven.** The model module's own docstring says *"11 tables"*
([app/models/__init__.py:2](app/models/__init__.py#L2)), and there are exactly 11
`db.Model` subclasses: `users`, `game_sessions`, `npc_interactions`,
`quiz_attempts`, `trial_attempts`, `knowledge_tests`, `location_progress`,
`achievements`, `book_reads`, `reflections`, `run_history`. The "10 tables"
(actually an 8-row list) in [PROJECT_CONTEXT.md:74-82](PROJECT_CONTEXT.md#L74-L82)
is **stale** — it predates `trial_attempts`, `book_reads`, and `reflections`.
**Authoritative: 11 (the code).**

---

## 2. Tech stack, exactly

`requirements.txt` pins only **minimum** versions; the exact versions below are
those **installed in the environment used for this inventory** (read via
`importlib.metadata`). Report both if the dissertation needs a fixed manifest.

**Runtime:** Python **3.14.6** (project note claims 3.12–3.14,
[PROJECT_CONTEXT.md:12](PROJECT_CONTEXT.md#L12)).

### Back-end
| Package | requirements.txt | Installed | Role in this system |
|---|---|---|---|
| Flask | `>=3.0` | 3.1.3 | Web framework; application-factory + 4 blueprints |
| Flask-SQLAlchemy | `>=3.1` | 3.1.1 | ORM over SQLite; the 11 models |
| Flask-Login | `>=0.6` | 0.6.3 | Session auth; `@login_required`, `current_user` |
| Werkzeug | `>=3.0` | 3.1.8 | Password hashing (`generate/check_password_hash`); WSGI |
| requests | `>=2.31` | 2.34.2 | HTTP client to the Ollama `/api/chat` endpoint |
| reportlab | `>=4.0` | 5.0.0 | Generates the PDF completion certificate (lazy-imported) |

> Note: the installed `reportlab 5.0.0` / `werkzeug 3.1.8` / `requests 2.34.2` /
> `sqlalchemy 2.0.51` strings are what the environment reported; they are newer
> than public releases known at authoring time. Report the installed values or
> the `requirements.txt` minima per your needs. SQLAlchemy 2.0.51 is present
> transitively via Flask-SQLAlchemy.

### Data
| Component | Detail |
|---|---|
| Database | **SQLite**, file `instance/atlas_quest.db` (gitignored; auto-created). URI `sqlite:///atlas_quest.db`, overridable via `ATLAS_DB_URI` ([app/__init__.py:51-53](app/__init__.py#L51-L53)) |
| Migrations | No Alembic. A hand-rolled guarded migration `_ensure_sqlite_columns()` adds missing nullable columns + unique indexes via `PRAGMA`/`ALTER` at boot ([app/__init__.py:137-205](app/__init__.py#L137-L205)) |

### AI
| Component | Detail |
|---|---|
| Model | IBM **Granite 3.3 8B** (`granite3.3:8b`) |
| Serving | **Ollama** local HTTP API, `http://localhost:11434`, `POST /api/chat`, `stream:false` ([app/services/npc_service.py:466-471](app/services/npc_service.py#L466-L471)) |
| Technique | Lightweight **RAG** (per-location course text injected into a locked system prompt) + **rule-based keyword fallback** + Socratic deflection guardrail |

### Front-end
No `package.json`; assets are vendored or loaded from CDNs in
[app/templates/base.html](app/templates/base.html):
- **Bootstrap 5.3.3** CSS + JS bundle (CDN, jsDelivr) — [base.html:9,42](app/templates/base.html#L9)
- **Bootstrap Icons 1.11.3** (CDN) — [base.html:11](app/templates/base.html#L11)
- **Google Fonts** — Rye, Inter, Source Serif 4 (CDN) — [base.html:13](app/templates/base.html#L13)
- **Vanilla JavaScript** (no framework), 28 modules — canvas scenes, audio, chat, etc.
- **HTML5 Canvas 2D** (Observatory constellation, Chronicle/ascent skies, certificate-style flourishes)
- **Web Audio API** (synthesised SFX) + one `book-open.mp3`
- **Web Speech API** (optional read-aloud, `tts.js`)
- **CSS3** with custom properties, one stylesheet (`style.css`)
- **Jinja2** server-side templates; custom `shuffle_options` filter randomises answer display order without changing the correct letter ([app/__init__.py:12-29](app/__init__.py#L12-L29))

### Tooling / testing
| Package | requirements-dev.txt | Installed | Role |
|---|---|---|---|
| pytest | `>=7.0` | 9.1.1 | The 109-test suite |
| Playwright | commented out | 1.61.0 | Installed but **not** part of the committed test suite; used only for exploratory browser inspection |

### Imported but unused / dead
- `import random` in [app/routes/auth.py:1](app/routes/auth.py#L1) — **unused** (`random.choice` appears only in commented-out code).
- Template `game/darkdata.html` and its script `js/darkdata.js` — **no route renders `darkdata.html`** (dead; also flagged in project notes).
- Template `game/coming_soon.html` — rendered only when a location has `stub=True` ([app/routes/game.py:238-239](app/routes/game.py#L238-L239)); **no location currently sets `stub=True`**, so it is effectively unreachable.

---

## 3. Architecture

### 3.1 App factory and blueprints
`create_app(config=None)` ([app/__init__.py:36-134](app/__init__.py#L36-L134))
builds the Flask app, applies defaults then optional overrides, initialises
`db` + `login_manager`, registers four blueprints, installs two `before_request`
hooks and one context processor, then runs `db.create_all()` +
`_ensure_sqlite_columns()`.

| Blueprint | Object | URL prefix | File |
|---|---|---|---|
| game | `game_bp` | (none, root) | [app/routes/game.py:51](app/routes/game.py#L51) |
| auth | `auth_bp` | `/auth` | [app/routes/auth.py:8](app/routes/auth.py#L8) |
| npc | `npc_bp` | `/npc` | [app/routes/npc.py:11](app/routes/npc.py#L11) |
| eval | `eval_bp` | `/eval` | [app/routes/eval_routes.py:26](app/routes/eval_routes.py#L26) |

**`before_request` hooks:** `_reject_cross_site_writes` — CSRF mitigation that
`abort(403)`s state-changing methods whose `Sec-Fetch-Site` header is
cross-site ([app/__init__.py:102-108](app/__init__.py#L102-L108)); and
`_auto_guest_login` — active only when `AUTH_DISABLED` (currently off)
([app/__init__.py:113-128](app/__init__.py#L113-L128)). **Context processor:**
`_inject_prefs` exposes `prefs` + `auth_disabled` to all templates.

### 3.2 Every route
Auth column: **LR** = `@login_required`; **AN** = anonymous-allowed.

| Method | Path | Auth | Endpoint | Purpose |
|---|---|---|---|---|
| GET | `/` | LR | `game.hub` | World-map hub: progress, stats, badges, runs, intro flags |
| POST | `/prefs` | LR | `game.save_prefs` | Persist audio/accessibility prefs to session |
| POST | `/seen` | LR | `game.save_seen` | Mark one-time hub reveals as played (session) |
| GET | `/location/<key>` | LR | `game.location` | Render a location scene; unlock-gated; starts Trial attempt for terminal |
| POST | `/location/<key>/read` | LR | `game.mark_read` | Record a Library book as read (presentation) |
| POST | `/location/<key>/progress` | LR | `game.mark_progress` | Record an explored sector/star (presentation) |
| POST | `/location/<key>/answer` | LR | `game.commit_answer` | Commit one Trial answer, return correctness+feedback (no key in DOM) |
| GET | `/location/<key>/trial` | LR | `game.trial` | Render the stepped Trial (non-terminal locations) |
| POST | `/location/<key>/submit` | LR | `game.submit_quiz` | Server-authoritative Trial grading + logging |
| POST | `/location/<key>/reflect` | LR | `game.reflect` | Save/skip a post-Trial reflection (qualitative) |
| GET/POST | `/auth/register` | AN | `auth.register` | Create account; assigns `condition="game"` |
| GET/POST | `/auth/login` | AN | `auth.login` | Log in by username or email |
| GET | `/auth/logout` | LR | `auth.logout` | Log out |
| POST | `/npc/chat` | LR + game-only | `npc.chat` | Professor Atlas exchange (JSON) |
| GET | `/eval/post-test` | LR | `eval.post_test` | The Final Assessment (gated; single-attempt) |
| POST | `/eval/post-test/submit` | LR | `eval.submit_post_test` | Grade + record the single post-test attempt |
| GET | `/eval/review` | LR | `eval.review` | Read-only per-question review of the attempt |
| GET | `/eval/epilogue` | LR | `eval.epilogue` | Replay the closing cinematic |
| GET | `/eval/certificate` | LR | `eval.certificate` | Stream the PDF completion certificate |

**Total: 19 routes** (game 10, auth 3, eval 5, npc 1).

### 3.3 Full database schema
Type = SQLAlchemy column type. Classification key: **R** = research measure,
**P** = presentation/progress state, **T** = additive telemetry, **M** =
transient mechanism state, **I** = identity/account.

**`users`** (I; `condition`/`post_test_done` are R) — [models:18-31](app/models/__init__.py#L18-L31)
| Column | Type | Null | Notes |
|---|---|---|---|
| id | Integer | no | PK |
| username | String(80) | no | unique |
| email | String(160) | no | unique |
| password_hash | String(255) | no | Werkzeug hash |
| condition | String(20) | no | default `"game"` — `game`\|`control` |
| post_test_done | Boolean | no | default False (passed the post-test) |
| seen_intro | Boolean | no | default False (presentation) |
| created_at | DateTime | yes | default utcnow |

**`game_sessions`** (R — time-on-task; also used for assessment timing) — [models:40-47](app/models/__init__.py#L40-L47)
`id`, `user_id`(FK), `location`(String40), `started_at`(DateTime), `ended_at`(DateTime, null).

**`npc_interactions`** (R — every tutor turn) — [models:50-61](app/models/__init__.py#L50-L61)
`id`, `user_id`(FK), `session_id`(FK, null), `location`, `user_message`(Text), `npc_response`(Text), `response_time_ms`(Integer, null), `is_fallback`(Boolean, default False), `created_at`.

**`quiz_attempts`** (R — one row per graded Trial question) — [models:64-75](app/models/__init__.py#L64-L75)
`id`, `user_id`(FK), `location`, `question_key`(String20), `selected_answer`(String4, null), `is_correct`(Boolean, default False), `attempt_number`(Integer, default 1), `npc_consulted`(Boolean, default False), `created_at`.

**`trial_attempts`** (M — server-authoritative grading-flow state, *not* research data per its docstring) — [models:78-101](app/models/__init__.py#L78-L101)
`id`, `token`(String64, unique, indexed), `user_id`(FK, indexed), `location`, `question_keys`(Text JSON), `answers_json`(Text JSON, default `"{}"`), `status`(String16, default `"open"` — open\|submitted\|expired), `score`(Integer, null), `passed`(Boolean, null), `started_at`, `submitted_at`(null).

**`knowledge_tests`** (R — the post-test outcome) — [models:104-121](app/models/__init__.py#L104-L121)
`id`, `user_id`(FK), `answers_json`(Text), `score`(Integer), `time_spent_seconds`(Integer, null — server-measured), `created_at`. **Constraint:** `UniqueConstraint(user_id)` named `ux_knowledge_test_user` — enforces one attempt per user.

**`location_progress`** (R/P — progression) — [models:124-136](app/models/__init__.py#L124-L136)
`id`, `user_id`(FK), `location`, `passed`(Boolean, default False), `best_score`(Integer, default 0), `attempts_count`(Integer, default 0), `unlocked_at`(DateTime, null). **Constraint:** `UniqueConstraint(user_id, location)` = `ux_progress_user_location`.

**`achievements`** (R — engagement) — [models:139-150](app/models/__init__.py#L139-L150)
`id`, `user_id`(FK), `achievement_key`(String40), `earned_at`. **Constraint:** `UniqueConstraint(user_id, achievement_key)` = `ux_achievement_user_key`.

**`book_reads`** (P — reading progress, explicitly *never a research measure*) — [models:153-170](app/models/__init__.py#L153-L170)
`id`, `user_id`(FK), `location`, `book_id`(String60), `created_at`. **Constraint:** `UniqueConstraint(user_id, location, book_id)` = `ux_book_read`.

**`reflections`** (R — additive qualitative) — [models:173-190](app/models/__init__.py#L173-L190)
`id`, `user_id`(FK), `location`, `prompt_key`(String60), `prompt_text`(Text), `response_text`(Text, null), `skipped`(Boolean, default False), `created_at`.

**`run_history`** (T — personal best-runs; never cross-user/by-condition) — [models:193-215](app/models/__init__.py#L193-L215)
`id`, `user_id`(FK), `combined_score`, `post_test_score`, `post_test_max`, `library_score`(default 0), `chronicle_score`(default 0), `ai_lab_score`(default 0), `observatory_score`(default 0), `badges_count`(default 0), `time_spent_seconds`(null), `xp`(default 0), `rank`(String40, null), `created_at`.

Additional unique indexes are also created at boot by
`_ensure_sqlite_columns()` ([app/__init__.py:174-197](app/__init__.py#L174-L197)),
matching the three `UniqueConstraint`s above (belt-and-braces for pre-existing
SQLite files).

### 3.4 Request lifecycles
**Loading a location** (`GET /location/<key>`, [game.py:230-282](app/routes/game.py#L230-L282)):
`@login_required` → `LOCATIONS.get(key)` else `404` → `is_unlocked(user,key)` else
redirect to hub → `stub` check → `get_or_create_progress` +
`get_or_create_open_session` (opens a `game_sessions` row) → branch on
`interaction`: `terminal` starts a `TrialAttempt` and embeds the Trial;
`constellation`/`timeline`/`bookshelf` render their scene. Hooks are attached for
rendering.

**Submitting a Trial** (`POST /location/<key>/submit`, [game.py:451-561](app/routes/game.py#L451-L561)):
unlock check → `_load_trial_attempt(key, form["attempt_id"])` validates ownership,
`status=="open"`, TTL (7200 s), and that the stored key-set is exactly 4 unique
known keys → build `submitted` from server-recorded first-commit answers (falling
back to a validated form letter only where never committed) → `grade_quiz` over
the **stored** keys → flip attempt to `submitted`, stamp `score`/`passed` (one
grading) → write one `quiz_attempts` row per question → update
`location_progress` (`best_score` monotonic, set `passed`) → close open
`game_sessions` → `grant_new` achievements → offer a reflection on pass →
render `results.html`.

**Submitting the post-test** (`POST /eval/post-test/submit`, [eval_routes.py:164-304](app/routes/eval_routes.py#L164-L304)):
`all_passed` gate → `_assessment_completed` single-attempt gate (if an attempt
exists, re-show results) → score by question key → server-authoritative duration
via `_server_assessment_seconds` (closes the `assessment` `game_sessions` row) →
insert `KnowledgeTest` (unique index rejects a racing double-submit →
`IntegrityError` rollback → show existing results) → set `post_test_done` if
`score >= 8` → `grant_new` (Atlas Sage) → `record_run` (one `run_history` row) →
render the cinematic results.

**One tutor exchange** (`POST /npc/chat`, [npc.py:14-64](app/routes/npc.py#L14-L64)):
`@login_required` → `condition=="game"` else `403` → non-empty message; `location`
must be in `LOCATION_ORDER` else `400` → `is_unlocked` else `403` → gather up to 5
recent wrong-answer **stems** + last-3 dialogue turns → `get_response(...,
ollama_enabled=config)` → (guardrail → optional LLM → keyword fallback) → log one
`npc_interactions` row with `response_time_ms` and `is_fallback` → return JSON
`{response, is_fallback}`.

---

## 4. Content and the four locations

`PASS_THRESHOLD = 3` ([game_content.py:10](app/game_content.py#L10)),
`TRIAL_COUNT = 4` ([game_content.py:805](app/game_content.py#L805)),
`PINNED_QUESTIONS = {"ai_lab": ["lab_q3"]}` ([game_content.py:809-811](app/game_content.py#L809-L811)).
`select_trial_questions(key)` includes the pinned key(s) first, then
`random.sample`s the remaining bank up to `TRIAL_COUNT`; the chosen keys are
stored per-attempt so the graded set equals the shown set
([game_content.py:814-827](app/game_content.py#L814-L827)).

IBM course = **SkillsBuild "Introduction to Artificial Intelligence"**, Course ID
**4058918**, 6 modules + final assessment
([CourseFidelityCheck.md:116](%20Atlas%20Quest%20—%20CourseFidelityCheck.md)).
The module→location mapping below reflects the **current** 4-location build (the
Chronicle was added since that fidelity doc, which described a 3-location plan).

### 4.1 The Library
- **key** `library`; **name** The Library; **theme** `archive`; **interaction** `bookshelf`; **accent** `#d4a84b` ([game_content.py:206-255](app/game_content.py#L206-L255)).
- **IBM module:** Module 1 (What is AI?).
- **Learning objectives** ([game_content.py:248-254](app/game_content.py#L248-L254)): define AI; differentiate AI vs augmented intelligence; describe AI's two core actions; identify real-world predictions; describe the three levels of AI.
- **Content items:** 5 books (`LIBRARY_BOOKS`: `ai`, `augmented`, `does`, `predict`, `levels`), each with 3 pages + a quick-check quiz + a flashcard; 5 `learn_cards`; 5 hooks.
- **Trial bank (5):** `lib_s1`, `lib_s2`, `lib_s3`, `lib_s4`, `lib_s5`.

### 4.2 The Chronicle
- **key** `chronicle`; **name** The Chronicle; **theme** `timeline`; **interaction** `timeline`; **accent** `#c1824a` ([game_content.py:257-354](app/game_content.py#L257-L354)).
- **IBM module:** Module 2 (Three Eras of Computing + the AI Winters).
- **Learning objectives** ([game_content.py:347-353](app/game_content.py#L347-L353)): name the three eras in order; explain Dartmouth 1956; identify the two causes of the First Winter; explain the expert-systems boom/bust; recall the thaw milestones (Deep Blue, Watson).
- **Content items:** 6 timeline beats (each with an inline check); 6 hooks; no `learn_cards` (uses beats).
- **Trial bank (6):** `ch_s1`…`ch_s6`.

### 4.3 The AI Lab
- **key** `ai_lab`; **name** The AI Lab; **theme** `lab`; **interaction** `terminal`; **accent** `#3fd0e0` ([game_content.py:356-393](app/game_content.py#L356-L393)).
- **IBM module:** Module 3 (data types); its `learn_cards` also recap Module 2 history (tabulation/programming/AI eras) — an overlap with the Chronicle (see §9).
- **Learning objectives** ([game_content.py:387-393](app/game_content.py#L387-L393)): describe the three eras of computing; explain why programmable computers can't solve dark data; identify AI history milestones; differentiate structured/unstructured/semi-structured data; explain why unstructured data needs AI.
- **Content items:** 4 `learn_cards` (terminal "sectors"); 4 hooks; the interactive data-sorting machine feeds the pinned question `lab_q3`.
- **Trial bank (6):** `lab_q3` (pinned, `no_shuffle`, the sorting diagnostic), `lab_s1`…`lab_s5`.

### 4.4 The Observatory
- **key** `observatory`; **name** The Observatory; **theme** `cosmos`; **interaction** `constellation`; **accent** `#3ab8d8` ([game_content.py:396-434](app/game_content.py#L396-L434)).
- **IBM modules:** 4 + 5 (how ML works: deterministic vs probabilistic; the three ML methods), **plus a "Modern-AI" extension** beyond the base course (overfitting, bias, NLP, LLMs, hallucination, few-shot) — labelled "Path A" in `TAUGHT_CONCEPTS` ([game_content.py:35-43](app/game_content.py#L35-L43)).
- **Learning objectives** ([game_content.py:427-433](app/game_content.py#L427-L433)): define ML vs traditional programming; deterministic vs probabilistic; supervised/unsupervised/reinforcement with examples; how ML solves unstructured data; what General AI is and when expected.
- **Content items:** 10 constellation stars (`observatory.js` `CONCEPTS`, each with an inline check), authored 1:1 with 10 hooks; 4 `learn_cards`. Star count is derived from content (10) and enforced consistent by a test.
- **Trial bank (6):** `obs_s1`…`obs_s6`.

### 4.5 `TAUGHT_CONCEPTS` (reproduced exactly, [game_content.py:23-44](app/game_content.py#L23-L44))
```python
TAUGHT_CONCEPTS = {
    # Library — Module 1 (foundations)
    "what_is_ai": "library",
    "augmented_intelligence": "library",
    "analysis_prediction": "library",
    "three_levels": "library",
    # Chronicle — Module 2 (history)
    "eras_and_winters": "chronicle",
    "ai_milestones": "chronicle",
    # AI Lab — Module 3 (data)
    "data_types": "ai_lab",
    "unstructured_data": "ai_lab",
    # Observatory — Modules 4–5 (machine learning) + Modern-AI extension
    "ml_methods": "observatory",
    "deterministic_probabilistic": "observatory",
    "overfitting": "observatory",
    "bias": "observatory",
    "nlp": "observatory",
    "llm": "observatory",
    "hallucination": "observatory",
    "few_shot_prompting": "observatory",
}
```

### 4.6 Post-test blueprint (question → concept → location → chapter)
Source: [app/eval_content.py:36-157](app/eval_content.py#L36-L157) (question/concept/chapter/correct) joined to `TAUGHT_CONCEPTS` for the teaching location. `POST_TEST_PASS = 8`, 10 items.

| Key | Chapter | Concept | Teaching location | Correct |
|---|---|---|---|---|
| p1 | 1 Foundations | what_is_ai | library | B |
| p2 | 1 Foundations | three_levels | library | C |
| p3 | 1 Foundations | augmented_intelligence | library | B |
| p4 | 1 Foundations | eras_and_winters | chronicle | B |
| p5 | 1 Foundations | ai_milestones | chronicle | C |
| p6 | 2 The Data Deep | data_types | ai_lab | C |
| p7 | 2 The Data Deep | unstructured_data | ai_lab | B |
| p8 | 3 The Learning Machines | ml_methods | observatory | A |
| p9 | 3 The Learning Machines | overfitting | observatory | B |
| p10 | 4 Final Synthesis | hallucination | observatory | A |

`CHAPTER_TITLES = {1:"Foundations", 2:"The Data Deep", 3:"The Learning Machines",
4:"Final Synthesis"}` — chapters are presentation only; scoring reads by key
([eval_content.py:16-21](app/eval_content.py#L16-L21),
[eval_routes.py:65-76](app/routes/eval_routes.py#L65-L76)). A content-validity
test asserts every tested concept is in `TAUGHT_CONCEPTS`
([tests/test_unit_content.py:85-92](tests/test_unit_content.py#L85-L92)).

---

## 5. Professor Atlas — verbatim

### 5.1 The complete `SYSTEM_PROMPT` (exact, [app/services/npc_service.py:406-421](app/services/npc_service.py#L406-L421))
```
You are Professor Atlas, a tutor inside the Atlas Quest educational game.

Your knowledge is strictly and exclusively limited to the IBM Introduction to Artificial Intelligence course content provided to you below. You have no other knowledge. You do not know anything that is not in the course content.

STRICT RULES:
1. Only answer using information from the COURSE CONTENT section below
2. If a question cannot be answered from that content, respond with exactly: That is beyond what we have covered in this course. Try asking me about the topics in the lesson above.
3. Never give direct quiz answers. If a student asks for an answer, respond with a Socratic question that helps them think it through
4. Stay in character as Professor Atlas at all times
5. Keep answers concise — 2 to 4 sentences maximum
6. When the learner answers correctly or seems close, occasionally ask them to explain WHY the other options are wrong, to deepen understanding

COURSE CONTENT:
{relevant_content}

Remember: you can ONLY draw from the course content above. Nothing else.
```

### 5.2 Other prompt fragments that reach the model
The only additional fragment injected into the prompt is the **adaptive
scaffolding block**, appended to the system message when the learner has recent
wrong answers ([npc_service.py:443-451](app/services/npc_service.py#L443-L451)):
```
\n\nLEARNER CONTEXT — This learner recently struggled with the following questions. Gently steer them toward understanding these concepts using hints and questions. You must NEVER state or hint at the correct option for any quiz question.\n
```
followed by one `- {stem}\n` line per recent-mistake **stem** (question text only;
options and correct answers are never included). The `SOCRATIC_DEFLECTIONS`,
`FALLBACK`, and `KEYWORDS` strings are the *rule-based* replies and never enter a
model prompt.

### 5.3 What the prompt manager assembles per exchange, in order
[npc_service.py:438-464](app/services/npc_service.py#L438-L464):
1. `relevant_content` = `COURSE_KNOWLEDGE[location]` (or `"No content available for this location."`).
2. `system` = `SYSTEM_PROMPT.format(relevant_content=...)`.
3. If `recent_mistakes`: append the LEARNER CONTEXT block + one line per stem.
4. `messages = [{"role":"system", "content": system}]`.
5. Append the **last 3** prior turns as alternating `user`/`assistant` messages.
6. Append the new `{"role":"user","content": message}`.
7. `POST {base_url}/api/chat` with `{model, messages, stream:false}`.

### 5.4 RAG grounding
`COURSE_KNOWLEDGE` ([npc_service.py:321-404](app/services/npc_service.py#L321-L404))
is a dict of four verbatim course-text blocks keyed by location
(`library`, `chronicle`, `ai_lab`, `observatory`). Selection is by exact location
key; the block is injected into `{relevant_content}`. There is **no vector store
or similarity search** — the whole location block is included (a static,
location-scoped RAG). The Observatory block additionally covers the Modern-AI
concepts (overfitting, bias, NLP, LLMs, hallucination, few-shot), verified by a
test ([tests/test_unit_services.py:51-61](tests/test_unit_services.py#L51-L61)).

### 5.5 The guardrail chain
`_looks_like_answer_request(message)` ([npc_service.py:278-280](app/services/npc_service.py#L278-L280))
tests the lower-cased message against 9 regexes
([npc_service.py:246-256](app/services/npc_service.py#L246-L256)):
`what('?s| is) the (correct )?answer`, `which (option|one|answer|choice)`,
`\bis it [abcd]\b`, `tell me the answer`, `give me the answer`, `just tell me`,
`what should i (pick|choose|select|answer)`, `the (right|correct) (option|choice|one)`,
`answer to (q|question)`.

**Where it runs:** *first*, at the top of `get_response`, **before any LLM call**
([npc_service.py:291-298](app/services/npc_service.py#L291-L298)). On a match it
returns `random.choice(SOCRATIC_DEFLECTIONS)` with `is_fallback=False` and the
model is never queried — proven by a monkeypatched test that the model is not
reached for answer-seeking messages
([tests/test_unit_services.py:64-81](tests/test_unit_services.py#L64-L81)).
There are 5 Socratic deflections
([npc_service.py:258-269](app/services/npc_service.py#L258-L269)).

### 5.6 The fallback path
Order in `get_response` ([npc_service.py:283-316](app/services/npc_service.py#L283-L316)):
1. Answer-request guard (above).
2. If `ollama_enabled`: call `_query_ollama`; if it returns text, return it
   (`is_fallback=False`).
3. Otherwise (LLM disabled, or returned `None`): scan `KEYWORDS[location]` for a
   substring keyword match; on a hit return the authored explanation
   (`is_fallback=False`).
4. Nothing matched → return `FALLBACK` with **`is_fallback=True`**.

`is_fallback` is recorded on every exchange in `npc_interactions.is_fallback`
([npc.py:51-60](app/routes/npc.py#L51-L60)) — a research signal for "the tutor had
nothing grounded to say."

### 5.7 Timeouts, retries, latency
- **Timeout:** effective **30 s** — `_query_ollama` reads
  `current_app.config.get("OLLAMA_TIMEOUT", 10)`
  ([npc_service.py:436](app/services/npc_service.py#L436)); the app config sets it
  to **30** ([app/__init__.py:62](app/__init__.py#L62)), so config wins. The `10`
  is only a fallback default if the key were absent.
- **Retries:** **none.** A single `requests.post`; any exception (incl.
  connection error, timeout, non-2xx via `raise_for_status`) is caught and returns
  `None` → the rule-based fallback ([npc_service.py:466-476](app/services/npc_service.py#L466-L476)).
- **Latency budget / measurement:** `response_time_ms` is measured around
  `get_response` in the route ([npc.py:40-48](app/routes/npc.py#L40-L48)) and
  stored. No streaming (`stream:false`). No other latency cap.

---

## 6. Assessment and tamper resistance

**How a Trial is served, committed, graded**
([game.py:343-362, 389-430, 451-535](app/routes/game.py#L343-L362)):
- **Serve:** `_start_trial_attempt` picks `TRIAL_COUNT` unique keys server-side,
  stores them in a `trial_attempts` row (`status="open"`) under a fresh opaque
  `token = secrets.token_urlsafe(16)`. The page receives **only the token**.
- **Commit:** `POST /answer` records the **first** letter committed per question
  and locks it — later calls return the same recorded letter, so it can't be used
  as an answer oracle ([game.py:389-430](app/routes/game.py#L389-L430)).
- **Grade:** `POST /submit` loads the attempt by token, validates it, grades the
  **server-stored** keys from the recorded answers, flips the attempt to
  `submitted` (one grading only), and writes the per-question research log.

**What the browser is trusted with:** the opaque `token`; optionally per-question
form letters that are used **only** if that question was never committed and
**only** if the value is one of that question's option letters
([game.py:481-488](app/routes/game.py#L481-L488)); the self-reported `consulted`
list (which questions got a hint). **What it is NOT trusted with:** which
questions to grade, the shown-keys list, or the correct answers — the page ships
no `data-correct` and no `shown_keys`, verified by a test
([tests/test_integration_game.py:191-197](tests/test_integration_game.py#L191-L197)).

**`_load_trial_attempt` validation** ([game.py:365-386](app/routes/game.py#L365-L386)):
rejects a missing token; an attempt not owned by the current user or wrong
location; `status != "open"` (so a **replay** of a submitted attempt is refused);
an attempt older than the **TTL of 7200 s** (`TRIAL_TTL_SECONDS = 2*60*60`,
[game.py:326](app/routes/game.py#L326)); and any stored key-set that isn't exactly
`TRIAL_COUNT` unique keys drawn from the real bank (guards forged/duplicated
keys). Tamper cases are covered by tests
([tests/test_integration_game.py:132-317](tests/test_integration_game.py#L132-L317)).

**Post-test single-attempt enforcement** (two layers):
- App layer: `_assessment_completed` blocks any second GET/POST once one
  `KnowledgeTest` exists ([eval_routes.py:54-62, 144-174](app/routes/eval_routes.py#L54-L62)).
- DB layer: `UniqueConstraint(user_id)` on `knowledge_tests`; a racing
  double-submit hits `IntegrityError`, is rolled back, and the first attempt is
  shown — so a race can create only one row
  ([eval_routes.py:226-236](app/routes/eval_routes.py#L226-L236),
  [tests/test_eval.py:156-170](tests/test_eval.py#L156-L170)).

**Server-authoritative timing:** the recorded/scoring duration is measured from a
server-stamped start (`GameSession` for the `assessment` pseudo-location, created
on GET) to the server's submit time via `_server_assessment_seconds`
([eval_routes.py:35-51, 185-189](app/routes/eval_routes.py#L35-L51)). A forged
browser time is ignored for both scoring and the recorded value.

**Still client-supplied (non-authoritative):** the browser's
`time_spent_seconds` and `per_question_seconds` are stored only under reserved
keys (`_client_time_spent_seconds`, `_per_question_seconds`) that scoring never
reads ([eval_routes.py:193-209](app/routes/eval_routes.py#L193-L209)); the
`consulted` hint list on a Trial; and hook guesses (not stored at all). Answer
display order is shuffled server-side by the Jinja filter, so shuffling is not
a client trust surface.

---

## 7. Testing

- **Framework/config:** pytest, configured by [pytest.ini](pytest.ini)
  (`testpaths = tests`, `python_files = test_*.py`, `addopts = -q`). Fixtures in
  [tests/conftest.py](tests/conftest.py): function-scoped in-memory SQLite
  (`StaticPool`), `OLLAMA_ENABLED=False`, `WTF_CSRF_ENABLED=False`, plus
  `user_factory` / `login` / `as_correct` helpers.
- **Per-module counts (109 total):**

| Module | Tests | Covers |
|---|---:|---|
| `tests/test_unit_content.py` | 17 | Content/authoring integrity; Observatory star-count + gate invariants |
| `tests/test_unit_grading.py` | 21 | `grade_quiz` / `select_trial_questions` / `get_questions_by_keys` across all locations |
| `tests/test_unit_services.py` | 16 | Atlas guardrails, RAG coverage, XP, leaderboard, achievements |
| `tests/test_integration_auth.py` | 9 | Register/login/logout; server-assigned condition |
| `tests/test_integration_game.py` | 22 | Unlock chain; Trial side effects; server-authoritative grading + tamper resistance |
| `tests/test_eval.py` | 24 | Post-test scoring/gating/single-attempt/timing; Chronicle in leaderboard |

- **How to run:** `python3 -m pytest` (from repo root).
- **Current result:** **109 passed**, 0 failed, in ~**4 s** (366 non-fatal
  `datetime.utcnow()` deprecation warnings).
- **Environment:** Python 3.14.6, pytest 9.1.1, Flask 3.1.3, SQLAlchemy 2.0.51.
- A prose write-up of the testing already exists at [docs/TESTING.md](docs/TESTING.md).

---

## 8. Design decisions and alternatives (recorded reasoning only)

Sources searched: code comments/docstrings, `PROJECT_CONTEXT.md`,
`CourseFidelityCheck.md`, `Assessment_Blueprint.md`, `LIBRARY_CONTEXT.md`, and
`git log`. The git history is 15 commits with terse messages ("fixes", "bug
fix", "new changes", "checkpoint before effective condition removal") and carries
**no design rationale**.

| Decision | Recorded rationale? |
|---|---|
| **Flask (app-factory + blueprints)** | The pattern is documented ([PROJECT_CONTEXT.md:13](PROJECT_CONTEXT.md#L13)) but **no recorded rationale** for choosing Flask over alternatives, and no alternative considered is recorded. |
| **SQLite** | Named as the datastore ([PROJECT_CONTEXT.md:14](PROJECT_CONTEXT.md#L14)); **no recorded rationale** and no recorded alternative. |
| **Vanilla JS (no framework)** | Recorded only as the parenthetical choice *"vanilla JavaScript (no frameworks)"* ([PROJECT_CONTEXT.md:18](PROJECT_CONTEXT.md#L18)). **No explicit reasoning** beyond that it was deliberate. |
| **Granite 3.3 8B specifically** | The model tag is documented; **no recorded rationale** for Granite over other models, nor for the 8B size specifically. |
| **Local Ollama over a cloud API** | The local endpoint is documented ([PROJECT_CONTEXT.md:16](PROJECT_CONTEXT.md#L16)); **no recorded rationale** stating *why* local was chosen over a cloud API. (Do not infer privacy/offline reasons — not stated.) |
| **Prompt-level guardrails over fine-tuning** | The guardrail *design* is heavily documented (system-prompt rules; `_looks_like_answer_request` running before the LLM — [npc_service.py:291-298](app/services/npc_service.py#L291-L298)). But there is **no recorded comparison to fine-tuning** and no statement that fine-tuning was considered and rejected. |
| **Gated unlock chain** | Documented mechanism + intent: *"the first location is always unlocked; each later location unlocks only when the previous one is passed"* ([app/services/progress.py:1-7](app/services/progress.py#L1-L7)); reinforced in the in-game tutorial ([game_content.py:201-203](app/game_content.py#L201-L203)). The *mechanism* is a recorded design; no explicit trade-off discussion. |
| **Scenario banks over fixed question sets** | Documented design: banks are sampled per attempt and stored so *"the graded set == the shown set"* ([game_content.py:437-442](app/game_content.py#L437-L442), [game_content.py:803-827](app/game_content.py#L803-L827); [PROJECT_CONTEXT.md:108-113](PROJECT_CONTEXT.md#L108-L113)). Rationale is the anti-cheat/variety property, stated as the mechanism's purpose. |
| **Single-condition decision** | The **richest recorded rationale.** `_assign_condition` docstring: single-condition study so *"Professor Atlas is available to all users"*, machinery *"deliberately kept intact"*, and *"REVERSIBLE: to restore the randomised, balanced two-group split…"* ([app/routes/auth.py:18-39](app/routes/auth.py#L18-L39)). Note `PROJECT_CONTEXT.md` still describes a two-condition study — stale (see §9). |

---

## 9. Known gaps, defects and rough edges

**Stale documentation that contradicts the code:**
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) is substantially out of date. It states
  3 locations ([:106](PROJECT_CONTEXT.md#L106)), the testing flags all ON
  ([:66-69](PROJECT_CONTEXT.md#L66-L69)), `POSTTEST_REPLAYABLE` exists
  ([:69](PROJECT_CONTEXT.md#L69)), "10 tables"/7 models
  ([:34,:74](PROJECT_CONTEXT.md#L74)), 4 badges ([:144-149](PROJECT_CONTEXT.md#L144)),
  a two-condition study ([:9](PROJECT_CONTEXT.md#L9)), session-based Trial storage
  ([:91-92](PROJECT_CONTEXT.md#L91)), and a leaderboard formula of
  `location*5 + badges*15`, max ≈ 240 ([:153](PROJECT_CONTEXT.md#L153)). The code
  contradicts every one of these (see §10 and below). **Authoritative = code.**
- `npc_service.py` module docstring says the tutor is *"Rule-based keyword
  responses for now, with a clear slot for an Ollama/Granite LLM … (Step 10)"*
  ([npc_service.py:1-14](app/services/npc_service.py#L1-L14)) — but the LLM path
  is fully implemented (`_query_ollama`). **Stale docstring.**

**Stale/again-wrong data in the code itself:**
- The per-location `order` fields are inconsistent: library `order=1`, chronicle
  `order=2`, **ai_lab `order=2`** (duplicate), observatory `order=3`
  ([game_content.py:214,264,363,403](app/game_content.py#L214)). The real order is
  `LOCATION_ORDER`; the `order` field appears vestigial/unused for ordering.
- The AI Lab's `topic` and `description` still frame it around "The Three Eras of
  Computing and Data" ([game_content.py:361-362](app/game_content.py#L361-L362)),
  overlapping the Chronicle; its `learn_cards` recap the eras. Whether this
  overlap is intended (spaced reinforcement) or leftover is **not recorded** —
  the fidelity doc recommended moving history into its own location, which became
  the Chronicle, but the AI Lab framing was not fully updated.

**Dead / unused:**
- `import random` unused in [auth.py:1](app/routes/auth.py#L1).
- `game/darkdata.html` + `js/darkdata.js` — not rendered by any route (dead).
- `game/coming_soon.html` — reachable only if a location sets `stub=True`; none does.

**Behavioural rough edges:**
- **Friction that is deliberate:** the gated unlock chain; the 3/4 Trial pass
  bar; the single-attempt, no-retake post-test (a fail is final,
  [tests/test_eval.py:188-198](tests/test_eval.py#L188-L198)); the 2-hour Trial
  attempt TTL; guess-first hooks before content.
- **Friction that is likely accidental / irritating:** a very slow learner can
  have a Trial attempt **expire** (TTL 7200 s) and be bounced to a fresh draw
  ([game.py:378-381](app/routes/game.py#L378-L381)); the guess-first hook
  auto-advances after ~1.6 s which can feel rushed
  ([hooks.js:87-89](app/static/js/hooks.js#L87-L89)); the AI Lab's pinned
  `lab_q3` (a drag-sort) is also surfaced as a multiple-choice item in the
  review, which has previously read as a "phantom question" (a known UX
  confusion, no data defect).
- **Study-blocking:** because registration only ever assigns `"game"`, the
  two-condition experiment **cannot be run** without a code change (§1.2).
- **Ollama dependency:** with `OLLAMA_ENABLED=True` and no Ollama running, each
  chat falls back to rule-based replies; a *reachable but slow* Ollama could add
  up to the 30 s timeout per chat before falling back.
- **Deprecation debt:** 366 `datetime.utcnow()` deprecation warnings (non-fatal)
  across the app/tests.

**Open audit items:** none tracked in the repo as open. Prior audit findings
referenced in tests (H1 Observatory star persistence, M2 timing, M3–M5 tutor,
M6 unique constraint) are all **fixed and regression-tested**.

---

## 10. Metrics (exact)

**Lines of code** (excluding `__pycache__`; `wc -l`):
| Language | LOC | Files |
|---|---:|---:|
| Python — app | 3,982 | 16 |
| Python — tests | 1,603 | 7 |
| JavaScript | 5,792 | 28 |
| CSS (single file `style.css`) | 5,945 | 1 |
| HTML templates | 2,183 | 18 |

**Structure:**
- **Routes:** 19 (game 10, auth 3, eval 5, npc 1).
- **Database tables / models:** 11.
- **Service modules:** 5 (`achievements`, `gamification`, `leaderboard`, `npc_service`, `progress`).
- **Templates:** 18. **JS modules:** 28.
- **Blueprints:** 4.

**Questions and prompts:**
- **Graded Trial banks:** 23 total — library 5, chronicle 6, ai_lab 6, observatory 6. Each Trial shows/grades 4.
- **Post-test:** 10 (pass ≥ 8).
- **Non-logged questioning:** 25 guess-first hooks (library 5, chronicle 6, ai_lab 4, observatory 10); inline quick-checks — 5 Library book quizzes + 6 Chronicle beat checks + 10 Observatory star checks = 21; 4 post-Trial reflection prompts (stored to `reflections`, ungraded).

**Gamification/achievements:**
- **Achievements:** 5 (`first_steps`, `chronicler`, `field_researcher`, `stargazer`, `atlas_sage`) — [app/services/achievements.py:15-31](app/services/achievements.py#L15-L31).
- **Ranks:** 5 rungs + sage — `["Novice Explorer","Apprentice","Scholar","Cartographer","Master Cartographer"]` then `"Atlas Sage"` ([gamification.py:26-27](app/services/gamification.py#L26-L27)).
- **XP:** 25/correct, +100/location passed, +30/post-test correct; 200 XP per level ([gamification.py:17-21](app/services/gamification.py#L17-L21)).
- **Leaderboard combined score:** `post_test*10 + Σ(4 location scores)*8 + badges*12 + speed_bonus(≤20)`, **max 308** ([leaderboard.py:15-26](app/services/leaderboard.py#L15-L26)).

**Tests:** 109.

---

## 11. Things here that contradict your written notes (to correct in the report)

1. **Locations:** your notes/PROJECT_CONTEXT say **3** (`library, ai_lab, observatory`); the code has **4** — the **Chronicle** was added between `library` and `ai_lab`.
2. **Testing flags:** notes say `AUTH_DISABLED`, `UNLOCK_ALL`, `POSTTEST_REPLAYABLE` are **True/on**; today all are **off**, and **`POSTTEST_REPLAYABLE` does not exist** — the post-test is a real single-attempt measure.
3. **Study design:** notes describe a **two-condition** between-subjects study; the code is **single-condition** (everyone `game`; control never allocated).
4. **Tables:** notes say **10** (and elsewhere "7 models"); the code has **11**.
5. **Trial storage:** notes describe a **session + hidden `shown_keys` field**; the code uses a **durable `trial_attempts` DB row + opaque token** (server-authoritative).
6. **Badges:** notes say **4**; the code has **5** (adds **Chronicler**).
7. **Leaderboard formula:** notes say `location*5 + badges*15`, max ≈ **240**; the code is `location*8 + badges*12` + speed, max **308**.
8. **Ranks:** notes list 4 rungs (no "Cartographer"); the code has **5** rungs before Atlas Sage.
9. **Post-test gate:** notes say "after all **3** locations"; the code requires all **4**.
10. **Pre-test:** if your notes imply a baseline test, note that pre-lesson *questions exist* (guess-first hooks + inline checks) but **none is stored or graded** — there is no pre-test instrument, only the single post-test.
11. **Tutor status:** the `npc_service` docstring calling the LLM a future "Step 10" is stale — the **Granite/Ollama path is implemented and live** by default.
