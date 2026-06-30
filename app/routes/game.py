from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..game_content import (
    GAME_INTRO_STEPS,
    LOCATION_ORDER,
    LOCATIONS,
    QUIZZES,
    build_library_shelves,
    grade_quiz,
)
from ..models import NpcInteraction, QuizAttempt, db
from ..services.achievements import ACH_BY_KEY, grant_new
from ..services.gamification import gamification_summary
from ..services.progress import (
    all_passed,
    get_or_create_open_session,
    get_or_create_progress,
    is_unlocked,
    progress_map,
)

game_bp = Blueprint("game", __name__)


@game_bp.route("/")
@login_required
def hub():
    grant_new(current_user)  # keep the achievements table consistent
    pmap = progress_map(current_user)
    show_post_test = all_passed(current_user) and not current_user.post_test_done
    new_keys = session.pop("atlas_new_achievements", [])
    new_achievements = [ACH_BY_KEY[k] for k in new_keys if k in ACH_BY_KEY]
    return render_template(
        "game/hub.html",
        locations=LOCATIONS,
        order=LOCATION_ORDER,
        pmap=pmap,
        show_post_test=show_post_test,
        post_test_done=current_user.post_test_done,
        stats=gamification_summary(current_user),
        game_steps=GAME_INTRO_STEPS,
        new_achievement_keys=new_keys,
        new_achievements=new_achievements,
    )


@game_bp.route("/location/<key>")
@login_required
def location(key):
    loc = LOCATIONS.get(key)
    if loc is None:
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))
    if loc.get("stub", False):
        return render_template("game/coming_soon.html", loc=loc)

    # Ensure a progress row + an open game session exist for logging.
    get_or_create_progress(current_user, key)
    get_or_create_open_session(current_user, key)

    quiz = QUIZZES.get(key, [])
    interaction = loc.get("interaction")

    if interaction == "terminal":
        return render_template("game/terminal.html", loc=loc, quiz=quiz)

    if interaction == "constellation":
        return render_template("game/observatory.html", loc=loc, quiz=quiz)

    shelves = None
    books = None
    if interaction == "bookshelf":
        books = loc.get("books", [])
        shelves = build_library_shelves(books)
    return render_template(
        "game/location.html", loc=loc, quiz=quiz, shelves=shelves, books=books
    )


@game_bp.route("/location/<key>/trial")
@login_required
def trial(key):
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("stub", False):
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))
    quiz = QUIZZES.get(key, [])
    return render_template("game/trial.html", loc=loc, quiz=quiz)


@game_bp.route("/location/<key>/submit", methods=["POST"])
@login_required
def submit_quiz(key):
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("stub", False):
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))

    quiz = QUIZZES.get(key, [])
    submitted = {q["key"]: request.form.get(q["key"]) for q in quiz}
    results, score, total, passed = grade_quiz(key, submitted)

    lp = get_or_create_progress(current_user, key)
    attempt_number = lp.attempts_count + 1

    # Which questions the user took a Professor Atlas hint on (per-question).
    consulted_raw = request.form.get("consulted", "")
    consulted = {c for c in consulted_raw.split(",") if c}

    # One quiz_attempts row per question.
    for q in quiz:
        selected = submitted.get(q["key"])
        db.session.add(
            QuizAttempt(
                user_id=current_user.id,
                location=key,
                question_key=q["key"],
                selected_answer=selected,
                is_correct=(selected == q["correct"]),
                attempt_number=attempt_number,
                npc_consulted=(q["key"] in consulted),
            )
        )

    # Update progress.
    lp.attempts_count = attempt_number
    if score > lp.best_score:
        lp.best_score = score
    if passed:
        lp.passed = True
    db.session.commit()

    # Grant any newly-earned achievements; the hub celebrates them on return.
    session["atlas_new_achievements"] = grant_new(current_user)

    return render_template(
        "game/results.html",
        loc=loc,
        results=results,
        score=score,
        total=total,
        passed=passed,
    )
