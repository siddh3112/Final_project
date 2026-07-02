import json
from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..eval_content import CHAPTER_TITLES, POST_TEST
from ..models import KnowledgeTest, db
from ..services.achievements import grant_new
from ..services.gamification import XP_PER_POSTTEST_CORRECT, gamification_summary
from ..services.leaderboard import record_run
from ..services.progress import all_passed, progress_map

eval_bp = Blueprint("eval", __name__, url_prefix="/eval")

# TESTING: allow the post-test to be re-opened/re-taken even after completion,
# so the results page can be exercised repeatedly.
# Set back to False for the real study (single-attempt research measure).
POSTTEST_REPLAYABLE = True


def _chapters():
    """Group POST_TEST into ordered chapters for the cinematic flow.

    Display order only — scoring reads answers by question key, so grouping and
    ordering here never affect what is scored.
    """
    chapters = []
    for num in sorted(CHAPTER_TITLES):
        qs = [q for q in POST_TEST if q.get("chapter") == num]
        if qs:
            chapters.append({"num": num, "title": CHAPTER_TITLES[num], "questions": qs})
    return chapters


@eval_bp.route("/post-test")
@login_required
def post_test():
    # Gated: only after all three locations are passed, and (in the study) only once.
    if not all_passed(current_user):
        return redirect(url_for("game.hub"))
    if current_user.post_test_done and not POSTTEST_REPLAYABLE:
        return redirect(url_for("game.hub"))
    return render_template(
        "eval/post_test.html",
        chapters=_chapters(),
        total=len(POST_TEST),
    )


@eval_bp.route("/post-test/submit", methods=["POST"])
@login_required
def submit_post_test():
    if not all_passed(current_user):
        return redirect(url_for("game.hub"))
    if current_user.post_test_done and not POSTTEST_REPLAYABLE:
        return redirect(url_for("game.hub"))

    # ── Scoring (UNCHANGED) ──
    answers = {}
    score = 0
    for q in POST_TEST:
        selected = request.form.get(q["key"])
        answers[q["key"]] = selected
        if selected == q["correct"]:
            score += 1

    # ── Silent timing telemetry (display-only data; never affects the score) ──
    total_time = None
    try:
        raw = request.form.get("time_spent_seconds")
        if raw not in (None, ""):
            total_time = max(0, int(float(raw)))
    except (TypeError, ValueError):
        total_time = None

    # Optional per-question seconds → stored under a reserved key that scoring
    # never reads (scoring only checks the p1..p10 question keys).
    answers_out = dict(answers)
    try:
        pq = json.loads(request.form.get("per_question_seconds") or "{}")
        if isinstance(pq, dict) and pq:
            answers_out["_per_question_seconds"] = {
                k: int(v) for k, v in pq.items() if str(k).startswith("p")
            }
    except (TypeError, ValueError):
        pass

    db.session.add(
        KnowledgeTest(
            user_id=current_user.id,
            answers_json=json.dumps(answers_out),
            score=score,
            time_spent_seconds=total_time,
        )
    )
    current_user.post_test_done = True
    db.session.commit()

    # Grant the Atlas Sage (and any pending) achievement; hub celebrates it.
    session["atlas_new_achievements"] = grant_new(current_user)

    # ── Presentation context for the cinematic reveal + post-test review ──
    # (does not affect scoring or storage above)
    review = []
    for q in POST_TEST:
        selected = answers.get(q["key"])
        review.append(
            {
                "chapter": q.get("chapter"),
                "question": q["question"],
                "options": q["options"],
                "selected": selected,
                "correct": q["correct"],
                "is_correct": selected == q["correct"],
                "explanation": q.get("explanation", ""),
            }
        )

    stats = gamification_summary(current_user)

    # ── Record this run in the PERSONAL best-runs history (additive) ──
    # Snapshot of already-stored data; never changes scoring/storage above.
    pmap = progress_map(current_user)
    run, is_personal_best, personal_best = record_run(
        current_user,
        post_test_score=score,
        post_test_max=len(POST_TEST),
        library_score=pmap["library"]["best_score"],
        ai_lab_score=pmap["ai_lab"]["best_score"],
        observatory_score=pmap["observatory"]["best_score"],
        badges_count=stats["badges_earned"],
        time_spent_seconds=total_time,
        xp=stats["xp"],
        rank=stats["rank"],
    )

    return render_template(
        "eval/post_test_done.html",
        score=score,
        total=len(POST_TEST),
        xp_per_correct=XP_PER_POSTTEST_CORRECT,
        xp_gained=score * XP_PER_POSTTEST_CORRECT,
        stats=stats,
        review=review,
        seal_date=datetime.utcnow().strftime("%d %B %Y"),
        combined_score=run.combined_score,
        is_personal_best=is_personal_best,
        personal_best=personal_best,
    )
