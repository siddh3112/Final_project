"""
Progress + unlock logic for Atlas Quest.

Unlock chain (LOCATION_ORDER): the first location is always unlocked; each
later location unlocks only when the previous one is passed (score >= 3/4).
The post-test unlocks only when all three locations are passed.
"""

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from ..game_content import LOCATION_ORDER
from ..models import GameSession, LocationProgress, db

# Normal gated progression: each location unlocks only when the previous one is
# passed. Set True to open every location regardless of progress (testing).
UNLOCK_ALL = False


def get_or_create_progress(user, location):
    lp = LocationProgress.query.filter_by(user_id=user.id, location=location).first()
    if lp is None:
        unlocked = is_unlocked(user, location)
        lp = LocationProgress(
            user_id=user.id,
            location=location,
            passed=False,
            best_score=0,
            attempts_count=0,
            unlocked_at=datetime.utcnow() if unlocked else None,
        )
        db.session.add(lp)
        try:
            db.session.commit()
        except IntegrityError:
            # A concurrent request created the row first (unique index) —
            # roll back and use the existing one.
            db.session.rollback()
            lp = LocationProgress.query.filter_by(user_id=user.id, location=location).first()
    return lp


def is_unlocked(user, location):
    """A location is unlocked if it's first in the chain, or the previous one passed."""
    if location not in LOCATION_ORDER:
        return False
    if UNLOCK_ALL:
        return True
    idx = LOCATION_ORDER.index(location)
    if idx == 0:
        return True
    prev = LOCATION_ORDER[idx - 1]
    prev_lp = LocationProgress.query.filter_by(user_id=user.id, location=prev).first()
    return bool(prev_lp and prev_lp.passed)


def all_passed(user):
    for loc in LOCATION_ORDER:
        lp = LocationProgress.query.filter_by(user_id=user.id, location=loc).first()
        if not (lp and lp.passed):
            return False
    return True


def progress_map(user):
    """Return {location_key: {passed, best_score, attempts_count, unlocked}} for the hub."""
    result = {}
    for loc in LOCATION_ORDER:
        lp = LocationProgress.query.filter_by(user_id=user.id, location=loc).first()
        result[loc] = {
            "passed": bool(lp and lp.passed),
            "best_score": lp.best_score if lp else 0,
            "attempts_count": lp.attempts_count if lp else 0,
            "unlocked": is_unlocked(user, loc),
        }
    return result


def get_or_create_open_session(user, location):
    """Return the current open game_session for this user+location, or create one."""
    s = (
        GameSession.query.filter_by(user_id=user.id, location=location, ended_at=None)
        .order_by(GameSession.id.desc())
        .first()
    )
    if s is None:
        s = GameSession(user_id=user.id, location=location)
        db.session.add(s)
        db.session.commit()
    return s
