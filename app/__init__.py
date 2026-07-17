import os
import random

from flask import Flask, request
from flask_login import LoginManager, current_user, login_user

from .models import User, db

login_manager = LoginManager()


def shuffle_options(q):
    """Return a question's (letter, text) options in a randomised DISPLAY order.

    Grading compares the option's LETTER (each option keeps its original letter as
    its submitted value), so only the on-screen position changes — never which
    answer is correct. Questions that are intentionally ordered, or that contain an
    'all/none of the above' style option, are returned UNSHUFFLED.
    """
    items = list((q.get("options") or {}).items())
    if q.get("ordered") or q.get("no_shuffle"):
        return items
    if any("above" in (text or "").lower() for _, text in items):
        return items
    items = items[:]  # copy — never mutate the source content
    for i in range(len(items) - 1, 0, -1):  # Fisher–Yates
        j = random.randint(0, i)
        items[i], items[j] = items[j], items[i]
    return items


def shuffle_events(q):
    """Return an ordering item's `events` in a randomised DISPLAY order.

    The learner reassembles the true sequence, so the events are presented
    scrambled; the CORRECT order lives only in game_content (never in the DOM).
    Copies the list (never mutates source) and re-rolls up to a few times so the
    already-solved order is not shown by fluke.
    """
    events = list((q.get("events") if isinstance(q, dict) else q) or [])
    if len(events) < 2:
        return events
    correct = [e["id"] for e in events]
    shuffled = events[:]
    for _ in range(8):
        random.shuffle(shuffled)
        if [e["id"] for e in shuffled] != correct:
            break
    return shuffled


def shuffle_board(items):
    """Return a shuffled COPY of a list — used to present the AI Lab's sorting-board
    objects in a random intake order (their draw order never hints the bins)."""
    lst = list(items or [])
    random.shuffle(lst)
    return lst

# ── Real login/register is ON. Flip to True to bypass auth with a shared
# "guest" auto-login while rebuilding the GUI. ──
AUTH_DISABLED = False


def create_app(config=None):
    """Application factory.

    `config` is an optional dict of Flask config overrides applied LAST — so
    tests can run against a throwaway DB with Ollama off, e.g.
    create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "OLLAMA_ENABLED": False}). With no argument the defaults below are
    used unchanged (identical to the original behaviour).
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.jinja_env.filters["shuffle_options"] = shuffle_options
    app.jinja_env.filters["shuffle_events"] = shuffle_events
    app.jinja_env.filters["shuffle_board"] = shuffle_board

    # Overridable via environment for any non-local deployment (default unchanged).
    app.config["SECRET_KEY"] = os.environ.get("ATLAS_SECRET_KEY", "atlas-quest-dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "ATLAS_DB_URI", "sqlite:///atlas_quest.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Professor Atlas LLM (Granite via Ollama). Flip OLLAMA_ENABLED to True once
    # Ollama is installed and the model is pulled (`ollama pull granite3.3:8b`).
    # When off (or if Ollama is unreachable) the NPC falls back to rule-based replies.
    app.config["OLLAMA_ENABLED"] = True
    app.config["OLLAMA_BASE_URL"] = "http://localhost:11434"
    app.config["OLLAMA_MODEL"] = "granite3.3:8b"
    app.config["OLLAMA_TIMEOUT"] = 30

    # Test / deployment overrides win over every default above.
    if config:
        app.config.update(config)

    # SQLite lives in the instance folder: instance/atlas_quest.db
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue your quest."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Front-of-house preferences (audio/accessibility) available to every
    # template, plus the guest-mode flag the Settings panel needs.
    from .prefs import current_prefs

    @app.context_processor
    def _inject_prefs():
        return {"prefs": current_prefs(), "auth_disabled": AUTH_DISABLED}

    # Blueprints
    from .routes.auth import auth_bp
    from .routes.eval_routes import eval_bp
    from .routes.game import game_bp
    from .routes.npc import npc_bp

    app.register_blueprint(game_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(npc_bp)
    app.register_blueprint(eval_bp)

    # Lightweight CSRF mitigation: browsers label cross-site requests with
    # Sec-Fetch-Site — reject state-changing requests that arrive cross-site.
    # Same-origin fetches/forms and non-browser clients (no header) pass.
    @app.before_request
    def _reject_cross_site_writes():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            sfs = request.headers.get("Sec-Fetch-Site")
            if sfs and sfs not in ("same-origin", "same-site", "none"):
                from flask import abort
                abort(403)

    # While AUTH_DISABLED, transparently sign in a single shared "guest" user so
    # all the per-user logic (progress, sessions, quiz attempts) keeps working
    # without any login screen.
    @app.before_request
    def _auto_guest_login():
        if not AUTH_DISABLED or request.endpoint == "static":
            return
        if not current_user.is_authenticated:
            guest = User.query.filter_by(username="guest").first()
            if guest is None:
                guest = User(
                    username="guest",
                    email="guest@atlasquest.local",
                    condition="game",
                )
                guest.set_password("guest")
                db.session.add(guest)
                db.session.commit()
            login_user(guest)

    with app.app_context():
        db.create_all()
        _ensure_sqlite_columns()

    return app


def _ensure_sqlite_columns():
    """Lightweight guarded migrations for SQLite (create_all won't ALTER existing
    tables). Adds missing nullable columns and integrity indexes without
    touching existing data. Never blocks boot."""
    from sqlalchemy import text

    wanted = {
        "knowledge_tests": [("time_spent_seconds", "INTEGER")],
        "users": [("seen_intro", "INTEGER")],
        # The Chronicle (4th location) joined the leaderboard; add its Trial score
        # to existing run_history rows as 0 (pre-Chronicle runs had no Chronicle).
        "run_history": [("chronicle_score", "INTEGER NOT NULL DEFAULT 0")],
    }
    conn = db.session.connection()

    # Reconcile a STALE `trial_attempts` table left by an earlier, reverted
    # design (different columns; create_all never ALTERs an existing table). It
    # holds NO research data — that's quiz_attempts; a trial_attempts row is
    # transient server-authoritative grading-flow state — so if the current
    # TrialAttempt columns (e.g. `token`) are absent, drop the empty stale table
    # and let create_all rebuild it to match the model. Guarded; no-op once correct.
    ta_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(trial_attempts)"))}
    if ta_cols and "token" not in ta_cols:
        conn.execute(text("DROP TABLE trial_attempts"))
        db.session.commit()
        db.create_all()  # recreate trial_attempts with the current schema

    for table, cols in wanted.items():
        existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
        for name, coltype in cols:
            if name not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {coltype}"))
    db.session.commit()

    # Uniqueness for research-data integrity. SQLite can't ALTER ADD CONSTRAINT,
    # but a unique INDEX enforces the same guarantee on existing tables. Any
    # pre-existing duplicates are merged first (keep the strongest/earliest row).
    hardening = [
        # location_progress: keep passed > best_score > earliest per (user, location)
        """DELETE FROM location_progress WHERE id NOT IN (
             SELECT id FROM (
               SELECT id, ROW_NUMBER() OVER (
                 PARTITION BY user_id, location
                 ORDER BY passed DESC, best_score DESC, id ASC) AS rn
               FROM location_progress)
             WHERE rn = 1)""",
        # achievements: keep the earliest earned per (user, key)
        """DELETE FROM achievements WHERE id NOT IN (
             SELECT MIN(id) FROM achievements GROUP BY user_id, achievement_key)""",
        # knowledge_tests: the graded assessment is single-attempt — one row per
        # user. Keep the EARLIEST (first == authoritative) attempt if any pre-fix
        # duplicates exist, then enforce it going forward with a unique index.
        """DELETE FROM knowledge_tests WHERE id NOT IN (
             SELECT MIN(id) FROM knowledge_tests GROUP BY user_id)""",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_progress_user_location"
        " ON location_progress(user_id, location)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_achievement_user_key"
        " ON achievements(user_id, achievement_key)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_knowledge_test_user"
        " ON knowledge_tests(user_id)",
    ]
    for sql in hardening:
        try:
            conn = db.session.connection()
            conn.execute(text(sql))
            db.session.commit()
        except Exception:
            db.session.rollback()  # hardening must never block boot
