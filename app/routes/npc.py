import time

from flask import Blueprint, abort, current_app, jsonify, request
from flask_login import current_user, login_required

from ..game_content import LOCATION_ORDER, QUIZZES
from ..models import NpcInteraction, QuizAttempt, db
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
    # Only real locations may be logged against (protects game_sessions /
    # npc_interactions research data from junk location strings).
    if location not in LOCATION_ORDER:
        return jsonify({"error": "invalid location"}), 400

    # ── Adaptive context: recent mistakes (STEMS ONLY) + recent dialogue ──
    recent_mistakes = _recent_mistake_stems(current_user.id, location)
    history = _recent_history(current_user.id, location)

    start = time.time()
    response, is_fallback = get_response(
        location,
        message,
        ollama_enabled=current_app.config.get("OLLAMA_ENABLED", False),
        recent_mistakes=recent_mistakes,
        history=history,
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


def _recent_mistake_stems(user_id, location):
    """Up to 5 recent question STEMS the learner got wrong here (options/answers
    stripped), de-duplicated by question, most-recent first."""
    if not location:
        return []
    stems_by_key = {q["key"]: q["question"] for q in QUIZZES.get(location, [])}
    rows = (
        QuizAttempt.query.filter_by(user_id=user_id, location=location, is_correct=False)
        .order_by(QuizAttempt.created_at.desc())
        .limit(20)
        .all()
    )
    stems, seen = [], set()
    for r in rows:
        if r.question_key in seen:
            continue
        seen.add(r.question_key)
        stem = stems_by_key.get(r.question_key)
        if stem:
            stems.append(stem)  # STEM ONLY — no options, no correct answer, no selection
        if len(stems) >= 5:
            break
    return stems


def _recent_history(user_id, location):
    """The last 3 Atlas turns in this location, chronological order."""
    if not location:
        return []
    rows = (
        NpcInteraction.query.filter_by(user_id=user_id, location=location)
        .order_by(NpcInteraction.created_at.desc())
        .limit(3)
        .all()
    )
    return [
        {"user_message": r.user_message, "npc_response": r.npc_response}
        for r in reversed(rows)
    ]
