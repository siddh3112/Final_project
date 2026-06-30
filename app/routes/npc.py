import time

from flask import Blueprint, abort, current_app, jsonify, request
from flask_login import current_user, login_required

from ..models import NpcInteraction, db
from ..services.npc_service import get_response
from ..services.progress import get_or_create_open_session

npc_bp = Blueprint("npc", __name__, url_prefix="/npc")


@npc_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    # Professor Atlas only exists for the game condition.
    if current_user.condition != "game":
        abort(403)

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    location = (data.get("location") or "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400

    start = time.time()
    response, is_fallback = get_response(
        location, message, ollama_enabled=current_app.config.get("OLLAMA_ENABLED", False)
    )
    elapsed_ms = int((time.time() - start) * 1000)

    session = get_or_create_open_session(current_user, location) if location else None
    db.session.add(
        NpcInteraction(
            user_id=current_user.id,
            session_id=session.id if session else None,
            location=location,
            user_message=message,
            npc_response=response,
            response_time_ms=elapsed_ms,
            is_fallback=is_fallback,
        )
    )
    db.session.commit()

    return jsonify({"response": response, "is_fallback": is_fallback})
