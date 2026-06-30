import os

from flask import Flask, request
from flask_login import LoginManager, current_user, login_user

from .models import User, db

login_manager = LoginManager()

# ── Login is disabled for now so we can jump straight into the game while
# rebuilding the GUI. Set this back to False to restore real login/register. ──
AUTH_DISABLED = True


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

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

    return app
