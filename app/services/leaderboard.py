"""
Personal best-runs leaderboard for Atlas Quest.

Each completed post-test records ONE RunHistory row with a combined score. This
is PER-USER history only — it is never ranked across users or by condition.
Additive telemetry: nothing here changes how the post-test is scored or stored.
"""

from ..models import RunHistory, db

# ── Combined-score weights (tune here) ──
# The score rewards the whole journey: all FOUR location Trials matter (8 each),
# knowledge stays dominant, badges reward achievement, and a small capped speed
# bonus breaks ties. Max possible = 100 + 128 + 60 + 20 = 308.
WEIGHTS = {
    "post_test": 10,   # knowledge — dominant: score 0..10 → 0..100
    "location": 8,     # Trial mastery: each location 0..4 → 0..128 across the 4
    "badge": 12,       # achievement: badges_count 0..5 → 0..60
}
SPEED_BONUS_CAP = 20        # light tiebreaker only
SPEED_BASELINE_SECONDS = 600
SPEED_DIVISOR = 30

# Highest attainable combined score (for reference / display headroom):
#   4 location Trials × 4 best_score = 16 location points; 5 badges.
MAX_COMBINED = (10 * WEIGHTS["post_test"]) + (16 * WEIGHTS["location"]) + (5 * WEIGHTS["badge"]) + SPEED_BONUS_CAP  # = 308


def speed_bonus(time_spent_seconds):
    """Small, capped speed bonus. 0 if time is unknown."""
    if time_spent_seconds is None:
        return 0
    return min(SPEED_BONUS_CAP, max(0, (SPEED_BASELINE_SECONDS - int(time_spent_seconds)) // SPEED_DIVISOR))


def combined_score(post_test_score, location_scores, badges_count, time_spent_seconds):
    """Compute the combined score. Knowledge dominates; the three Trials matter;
    speed is a light bonus."""
    total = post_test_score * WEIGHTS["post_test"]
    total += sum(location_scores) * WEIGHTS["location"]
    total += badges_count * WEIGHTS["badge"]
    total += speed_bonus(time_spent_seconds)
    return int(round(total))


def score_of(run):
    """Re-score a stored run with the CURRENT weights, from its own inputs.

    Used for ranking / display / personal-best comparisons so the board stays
    internally consistent even after the formula is tuned — WITHOUT ever
    overwriting the historical `combined_score` stored on the row (additive)."""
    return combined_score(
        run.post_test_score or 0,
        [run.library_score or 0, run.chronicle_score or 0, run.ai_lab_score or 0, run.observatory_score or 0],
        run.badges_count or 0,
        run.time_spent_seconds,
    )


def record_run(user, *, post_test_score, post_test_max, library_score, chronicle_score,
               ai_lab_score, observatory_score, badges_count, time_spent_seconds, xp, rank):
    """Insert one RunHistory row for a completed post-test.

    Returns (run, is_personal_best, best_after). A new personal best = strictly
    greater than the user's previous best combined_score (ties are NOT a new
    best). First run is always a personal best.
    """
    cs = combined_score(
        post_test_score,
        [library_score, chronicle_score, ai_lab_score, observatory_score],
        badges_count,
        time_spent_seconds,
    )

    # Compare against prior runs RE-SCORED with the current weights, so the
    # personal best is a like-for-like whole-journey comparison.
    prev = [score_of(r) for r in RunHistory.query.filter_by(user_id=user.id).all()]
    prev_best = max(prev) if prev else None
    is_personal_best = prev_best is None or cs > prev_best

    run = RunHistory(
        user_id=user.id,
        combined_score=cs,
        post_test_score=post_test_score,
        post_test_max=post_test_max,
        library_score=library_score,
        chronicle_score=chronicle_score,
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
    """This user's runs ONLY, best-to-worst then most recent. Never joins users.

    Each run is re-scored with the current weights (attached as `display_score`,
    a non-persisted attribute) and sorted by that, so the whole-journey best sits
    at #1 regardless of when it was recorded."""
    runs = RunHistory.query.filter_by(user_id=user.id).all()
    for r in runs:
        r.display_score = score_of(r)  # non-mapped attr — never written back to the DB
    runs.sort(key=lambda r: (r.display_score, r.created_at), reverse=True)
    return runs


def run_stats(user):
    """Small summary strip for the board (best score / best post-test / fastest / total)."""
    runs = RunHistory.query.filter_by(user_id=user.id).all()
    if not runs:
        return {"best_score": None, "best_post_test": None, "fastest": None, "total": 0}
    times = [r.time_spent_seconds for r in runs if r.time_spent_seconds is not None]
    return {
        "best_score": max(score_of(r) for r in runs),
        "best_post_test": max(r.post_test_score for r in runs),
        "fastest": min(times) if times else None,
        "total": len(runs),
    }
