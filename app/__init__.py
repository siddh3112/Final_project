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

# ── Login is disabled for now so we can jump straight into the game while
# rebuilding the GUI. Set this back to False to restore real login/register. ──
AUTH_DISABLED = True


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.jinja_env.filters["shuffle_options"] = shuffle_options

    app.config["SECRET_KEY"] = "atlas-quest-dev-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///atlas_quest.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Professor Atlas LLM (Granite via Ollama). Flip OLLAMA_ENABLED to True once
    # Ollama is installed and the model is pulled (`ollama pull granite3.3:8b`).
    # When off (or if Ollama is unreachable) the NPC falls back to rule-based replies.
    app.config["OLLAMA_ENABLED"] = True
    app.config["OLLAMA_BASE_URL"] = "http://localhost:11434"
    app.config["OLLAMA_MODEL"] = "granite3.3:8b"
    app.config["OLLAMA_TIMEOUT"] = 30

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
    tables). Adds any missing nullable columns without touching existing data."""
    from sqlalchemy import text

    wanted = {
        "knowledge_tests": [("time_spent_seconds", "INTEGER")],
    }
    conn = db.session.connection()
    for table, cols in wanted.items():
        existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
        for name, coltype in cols:
            if name not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {coltype}"))
    db.session.commit()
