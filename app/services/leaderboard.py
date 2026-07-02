"""
Personal best-runs leaderboard for Atlas Quest.

Each completed post-test records ONE RunHistory row with a combined score. This
is PER-USER history only — it is never ranked across users or by condition.
Additive telemetry: nothing here changes how the post-test is scored or stored.
"""

from sqlalchemy import func

from ..models import RunHistory, db

# ── Combined-score weights (tune here) ──
WEIGHTS = {
    "post_test": 10,   # knowledge, weighted highest: 0..100 (score 0..10)
    "location": 5,     # mastery: each location 0..4 → 0..60 across the 3
    "badge": 15,       # achievement: badges_count * 15
}
SPEED_BONUS_CAP = 20        # light tiebreaker only
SPEED_BASELINE_SECONDS = 600
SPEED_DIVISOR = 30


def speed_bonus(time_spent_seconds):
    """Small, capped speed bonus. 0 if time is unknown."""
    if time_spent_seconds is None:
        return 0
    return min(SPEED_BONUS_CAP, max(0, (SPEED_BASELINE_SECONDS - int(time_spent_seconds)) // SPEED_DIVISOR))


def combined_score(post_test_score, location_scores, badges_count, time_spent_seconds):
    """Compute the combined score. Knowledge dominates; speed is a light bonus."""
    total = post_test_score * WEIGHTS["post_test"]
    total += sum(location_scores) * WEIGHTS["location"]
    total += badges_count * WEIGHTS["badge"]
    total += speed_bonus(time_spent_seconds)
    return int(round(total))


def record_run(user, *, post_test_score, post_test_max, library_score, ai_lab_score,
               observatory_score, badges_count, time_spent_seconds, xp, rank):
    """Insert one RunHistory row for a completed post-test.

    Returns (run, is_personal_best). A new personal best = strictly greater than
    the user's previous best combined_score (ties are NOT a new best). First run
    is always a personal best.
    """
    cs = combined_score(
        post_test_score,
        [library_score, ai_lab_score, observatory_score],
        badges_count,
        time_spent_seconds,
    )

    prev_best = (
        db.session.query(func.max(RunHistory.combined_score))
        .filter(RunHistory.user_id == user.id)
        .scalar()
    )
    is_personal_best = prev_best is None or cs > prev_best

    run = RunHistory(
        user_id=user.id,
        combined_score=cs,
        post_test_score=post_test_score,
        post_test_max=post_test_max,
        library_score=library_score,
        ai_lab_score=ai_lab_score,
        observatory_score=observatory_score,
        badges_count=badges_count,
        time_spent_seconds=time_spent_seconds,
        xp=xp,
        rank=rank,
    )
    db.session.add(run)
    db.session.commit()

    best_after = cs if is_personal_best else prev_best
    return run, is_personal_best, best_after


def user_runs(user):
    """This user's runs ONLY, best-to-worst then most recent. Never joins users."""
    return (
        RunHistory.query.filter_by(user_id=user.id)
        .order_by(RunHistory.combined_score.desc(), RunHistory.created_at.desc())
        .all()
    )


def run_stats(user):
    """Small summary strip for the board (best score / best post-test / fastest / total)."""
    runs = RunHistory.query.filter_by(user_id=user.id).all()
    if not runs:
        return {"best_score": None, "best_post_test": None, "fastest": None, "total": 0}
    times = [r.time_spent_seconds for r in runs if r.time_spent_seconds is not None]
    return {
        "best_score": max(r.combined_score for r in runs),
        "best_post_test": max(r.post_test_score for r in runs),
        "fastest": min(times) if times else None,
        "total": len(runs),
    }
