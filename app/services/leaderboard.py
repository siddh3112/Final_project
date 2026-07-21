"""
Personal best-runs leaderboard for Atlas Quest.

Each completed post-test records ONE RunHistory row with a combined score. This
is PER-USER history only — it is never ranked across users or by condition.
Additive telemetry: nothing here changes how the post-test is scored or stored.
"""

from ..models import RunHistory, db
from .handles import ensure_handle, handle_for

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
               ai_lab_score, observatory_score, badges_count, time_spent_seconds, xp, rank,
               run_number=1):
    """Insert one RunHistory row for a completed playthrough.

    This is the GAMIFIED score and the only thing a replay writes. It is never the
    research record: the one-shot KnowledgeTest is written on run 1 only, in
    eval_routes.submit_post_test, and a replay never touches it.

    Returns (run, is_personal_best, best_after). A new personal best = strictly
    greater than the user's previous best (ties are NOT a new best), so a worse
    replay can never lower a standing. First run is always a personal best.
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
        run_number=run_number,
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


def best_run_for(user_id, runs):
    """The single best run for one user, re-scored with current weights."""
    return max(runs, key=lambda r: (score_of(r), r.created_at))


def best_runs(limit=25, current_user_id=None):
    """CROSS-PLAYER board: every player once, at their BEST run, ranked high to low.

    Ranking uses score_of() (re-scored with current weights) rather than the stored
    combined_score, so the board stays internally consistent if the formula is
    tuned. Taking the MAX over a player's runs is what makes a worse replay
    harmless: it simply is not the maximum, so a standing can only ever rise.

    PRIVACY: rows carry the anonymised display handle, never the username or email,
    so participants cannot identify each other on a shared board. `is_you` lets the
    viewer find their own row without exposing anyone else.
    """
    from ..models import User  # local import keeps this module free of route deps

    rows = RunHistory.query.all()
    by_user = {}
    for r in rows:
        by_user.setdefault(r.user_id, []).append(r)

    entries = []
    backfilled = False
    for uid, runs in by_user.items():
        best = best_run_for(uid, runs)
        u = db.session.get(User, uid)
        if u is None:
            continue
        # Backfill an anonymised handle for anyone who predates the column (or was
        # created outside the registration flow). Presentation only, idempotent,
        # and it guarantees a real username can never reach the board.
        if not u.display_handle:
            ensure_handle(u, commit=False)
            backfilled = True
        entries.append({
            "user_id": uid,
            "handle": handle_for(u),
            "score": score_of(best),
            "run_number": getattr(best, "run_number", 1) or 1,
            "post_test_score": best.post_test_score or 0,
            "post_test_max": best.post_test_max or 0,
            "time_spent_seconds": best.time_spent_seconds,
            "total_runs": len(runs),
            "is_you": (current_user_id is not None and uid == current_user_id),
        })

    if backfilled:
        db.session.commit()

    entries.sort(key=lambda e: (e["score"], -e["user_id"]), reverse=True)
    for i, e in enumerate(entries, 1):
        e["rank"] = i
    return entries[:limit] if limit else entries


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
