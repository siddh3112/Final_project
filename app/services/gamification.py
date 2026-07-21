"""
Lightweight gamification layer for Atlas Quest.

XP, rank, level progress and badges are all COMPUTED on the fly from data that
already exists (LocationProgress + the user's post_test_done flag). Nothing new
is stored — so it can never drift out of sync, and it's fully reversible.

Scoring (transparent + round numbers):
  - 25 XP per correct answer in your best attempt at a location  (best_score * 25)
  - +100 XP completion bonus per location passed
  - +30 XP per correct answer on the final assessment (if submitted)
"""

from ..game_content import LOCATION_ORDER
from ..models import KnowledgeTest, LocationProgress

XP_PER_CORRECT = 25
XP_LOCATION_BONUS = 100
XP_PER_POSTTEST_CORRECT = 30

XP_PER_LEVEL = 200  # XP needed to advance one level

# Rank title by how many locations have been passed (0..4), plus the sage rank.
# One rung per state so passing every location — including the 4th — moves the
# rank (RANKS[min(passed_count, len(RANKS) - 1)]).
RANKS = ["Novice Explorer", "Apprentice", "Scholar", "Cartographer", "Master Cartographer"]
SAGE_RANK = "Atlas Sage"


def _location_progress(user):
    """All of this user's progress rows, keyed by location.

    Fetched once and passed around so a single hub render does not re-query per
    location.
    """
    rows = LocationProgress.query.filter_by(user_id=user.id).all()
    return {r.location: r for r in rows}


def compute_xp(user, progress=None):
    """Total XP: best score per location, a bonus per location passed, plus the
    Final Assessment.

    XP is derived from stored progress every time rather than accumulated in a
    column, so it can never drift out of step with the real scores and there is no
    running total to corrupt. It is presentation only: XP, levels, and ranks never
    feed back into grading or unlocking.

    Scoring off `best_score` (not the latest attempt) means a weaker retry cannot
    take XP away, which matches the rule that best_score only ever rises.
    """
    progress = progress if progress is not None else _location_progress(user)
    xp = 0
    for key in LOCATION_ORDER:
        lp = progress.get(key)
        if lp:
            xp += (lp.best_score or 0) * XP_PER_CORRECT
            if lp.passed:
                xp += XP_LOCATION_BONUS
    if user.post_test_done:
        # The FIRST attempt is authoritative (single-attempt); read it with the
        # same id.asc() ordering as results/certificate so all consumers agree.
        attempt = (
            KnowledgeTest.query.filter_by(user_id=user.id)
            .order_by(KnowledgeTest.id.asc())
            .first()
        )
        if attempt:
            xp += (attempt.score or 0) * XP_PER_POSTTEST_CORRECT
    return xp


def get_badges(user, progress=None):
    """Return the full badge set with earned flags, read from the persisted
    achievements table (the single source of truth)."""
    from .achievements import ACHIEVEMENTS, earned_map

    em = earned_map(user)
    return [
        {
            "key": a["key"], "name": a["name"], "icon": a["icon"],
            "desc": a["desc"], "how": a["how"],
            "earned": a["key"] in em,
            "earned_at": em.get(a["key"]),
        }
        for a in ACHIEVEMENTS
    ]


def gamification_summary(user):
    """Everything the hub HUD needs in one call."""
    progress = _location_progress(user)

    passed_count = sum(1 for k in LOCATION_ORDER if progress.get(k) and progress[k].passed)
    total = len(LOCATION_ORDER)
    xp = compute_xp(user, progress)

    badges = get_badges(user, progress)
    badges_earned = sum(1 for b in badges if b["earned"])

    # Rank: sage if finished everything, else by locations passed.
    if user.post_test_done:
        rank = SAGE_RANK
    else:
        rank = RANKS[min(passed_count, len(RANKS) - 1)]

    level = xp // XP_PER_LEVEL + 1
    xp_into_level = xp % XP_PER_LEVEL
    level_pct = round(xp_into_level / XP_PER_LEVEL * 100)

    # Journey counts every location PLUS the final assessment as one extra
    # milestone (total is len(LOCATION_ORDER), so this can't drift).
    journey_total = total + 1
    journey_done = passed_count + (1 if user.post_test_done else 0)
    # Everything done: all locations passed AND the final assessment complete.
    # At that point there is no more content, so the HUD shows a "complete"
    # state instead of a misleading "X/200 to next level" teaser.
    journey_complete = journey_done >= journey_total

    return {
        "xp": xp,
        "level": level,
        "level_pct": 100 if journey_complete else level_pct,
        "xp_into_level": xp_into_level,
        "xp_per_level": XP_PER_LEVEL,
        "rank": rank,
        "passed_count": passed_count,
        "total": total,
        "journey_done": journey_done,
        "journey_total": journey_total,
        "journey_complete": journey_complete,
        "journey_pct": round(passed_count / total * 100) if total else 0,
        "badges": badges,
        "badges_earned": badges_earned,
        "badges_total": len(badges),
    }
