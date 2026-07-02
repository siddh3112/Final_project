from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..prefs import set_prefs

from ..game_content import (
    GAME_INTRO_STEPS,
    LOCATION_ORDER,
    LOCATIONS,
    QUIZZES,
    build_library_shelves,
    get_questions_by_keys,
    grade_quiz,
    select_trial_questions,
)
from ..eval_content import POST_TEST
from ..models import KnowledgeTest, NpcInteraction, QuizAttempt, db
from ..services.achievements import (
    ACH_BY_KEY,
    earned_map,
    grant_new,
)
from ..services.gamification import gamification_summary
from ..services.leaderboard import run_stats, user_runs
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
    # Post-test pin is clickable when unlocked and not yet done — or always,
    # while POSTTEST_REPLAYABLE is on for testing.
    from .eval_routes import POSTTEST_REPLAYABLE
    show_post_test = all_passed(current_user) and (
        not current_user.post_test_done or POSTTEST_REPLAYABLE
    )
    new_keys = session.pop("atlas_new_achievements", [])
    new_achievements = [ACH_BY_KEY[k] for k in new_keys if k in ACH_BY_KEY]

    stats = gamification_summary(current_user)
    badge_detail = _badge_detail(current_user, pmap, stats)

    return render_template(
        "game/hub.html",
        locations=LOCATIONS,
        order=LOCATION_ORDER,
        pmap=pmap,
        show_post_test=show_post_test,
        post_test_done=current_user.post_test_done,
        stats=stats,
        badge_detail=badge_detail,
        game_steps=GAME_INTRO_STEPS,
        new_achievement_keys=new_keys,
        new_achievements=new_achievements,
        runs=user_runs(current_user),
        run_stats=run_stats(current_user),
    )


# Maps each location-completion badge to its location key.
_BADGE_LOCATION = {"first_steps": "library", "field_researcher": "ai_lab", "stargazer": "observatory"}


def _badge_detail(user, pmap, stats):
    """Read-only detail for each EARNED badge, keyed by achievement_key.

    Assembles already-stored data (location_progress, quiz_attempts,
    knowledge_tests, gamification) for the hub's badge cards. Locked badges are
    intentionally omitted. Nothing is written or recomputed here.
    """
    em = earned_map(user)
    detail = {}

    def meta(key):
        a = ACH_BY_KEY.get(key, {})
        return {"name": a.get("name"), "icon": a.get("icon"), "desc": a.get("desc")}

    # Location-completion badges → that Trial's best score + attempts.
    for bkey, lkey in _BADGE_LOCATION.items():
        if bkey in em:
            p = pmap[lkey]
            d = meta(bkey)
            d.update({
                "kind": "location",
                "location": LOCATIONS[lkey]["name"],
                "score": p["best_score"], "max": 4,
                "attempts": p["attempts_count"],
                "perfect": p["best_score"] >= 4,
            })
            detail[bkey] = d

    # Atlas Sage → post-test score + rank reached.
    if "atlas_sage" in em:
        kt = (KnowledgeTest.query.filter_by(user_id=user.id)
              .order_by(KnowledgeTest.id.desc()).first())
        d = meta("atlas_sage")
        d.update({
            "kind": "atlas_sage",
            "score": kt.score if kt else 0, "max": len(POST_TEST),
            "perfect": bool(kt and kt.score >= len(POST_TEST)),
            "rank": stats.get("rank"),
        })
        detail["atlas_sage"] = d

    return detail


@game_bp.route("/prefs", methods=["POST"])
@login_required
def save_prefs():
    """Persist front-of-house presentation prefs to the session (audio /
    accessibility only — never anything that affects scoring or research data)."""
    data = request.get_json(silent=True) or {}
    return jsonify({"ok": True, "prefs": set_prefs(data)})


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
        # The terminal embeds the graded Trial: pick this attempt's questions
        # (pinning the sorting diagnostic) and remember exactly what was shown.
        shown_keys = select_trial_questions(key)
        session[f"shown_{key}"] = shown_keys
        quiz = get_questions_by_keys(key, shown_keys)
        return render_template(
            "game/terminal.html", loc=loc, quiz=quiz, shown_keys=shown_keys
        )

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
    # Draw this attempt's questions at random and remember what was shown so the
    # graded set == the shown set (see submit_quiz).
    shown_keys = select_trial_questions(key)
    session[f"shown_{key}"] = shown_keys
    quiz = get_questions_by_keys(key, shown_keys)
    return render_template("game/trial.html", loc=loc, quiz=quiz, shown_keys=shown_keys)


@game_bp.route("/location/<key>/submit", methods=["POST"])
@login_required
def submit_quiz(key):
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("stub", False):
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))

    # Grade only the questions this attempt actually showed. Prefer the hidden
    # field posted with the form (authoritative for this exact page), then the
    # session record, then fall back to the whole bank.
    bank_keys = [q["key"] for q in QUIZZES.get(key, [])]
    shown_raw = request.form.get("shown_keys", "")
    shown_keys = [k for k in shown_raw.split(",") if k in bank_keys]
    if not shown_keys:
        shown_keys = [k for k in session.get(f"shown_{key}", []) if k in bank_keys]
    if not shown_keys:
        shown_keys = bank_keys

    quiz = get_questions_by_keys(key, shown_keys)
    submitted = {q["key"]: request.form.get(q["key"]) for q in quiz}
    results, score, total, passed = grade_quiz(key, submitted, shown_keys=shown_keys)

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
