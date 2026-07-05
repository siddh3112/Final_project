"""
Achievements — real, persisted unlockables (also engagement research data).

Each achievement is granted at most once per user and stored in the
`achievements` table with a timestamp. `grant_new()` is idempotent: it inserts
any newly-qualifying achievements and returns the keys that were just earned
(so the hub can celebrate them with a popup).
"""

from sqlalchemy.exc import IntegrityError

from ..models import Achievement, LocationProgress, db

# Display order + popup/tooltip copy. (Single source of truth for badges.)
ACHIEVEMENTS = [
    {"key": "first_steps", "name": "First Steps", "icon": "👟",
     "desc": "You completed your first location. The journey begins.",
     "how": "Complete the Library"},
    {"key": "chronicler", "name": "Chronicler", "icon": "⏳",
     "desc": "You walked the timeline of thinking machines — from tabulation to the thaw.",
     "how": "Complete the Chronicle"},
    {"key": "field_researcher", "name": "Field Researcher", "icon": "🛰️",
     "desc": "You mastered the AI Lab. The eras of computing are yours.",
     "how": "Complete the AI Lab"},
    {"key": "stargazer", "name": "Stargazer", "icon": "✨",
     "desc": "You traced the constellation of machine learning.",
     "how": "Complete the Observatory"},
    {"key": "atlas_sage", "name": "Atlas Sage", "icon": "🏆",
     "desc": "You completed the entire Atlas. You are a master cartographer of AI.",
     "how": "Complete the Final Assessment"},
]
ACH_BY_KEY = {a["key"]: a for a in ACHIEVEMENTS}

_LOCATION_BADGE = {"library": "first_steps", "chronicle": "chronicler", "ai_lab": "field_researcher", "observatory": "stargazer"}


def _qualifying(user):
    """The set of achievement keys the user currently qualifies for (from data)."""
    keys = set()
    progress = {lp.location: lp for lp in LocationProgress.query.filter_by(user_id=user.id).all()}

    for loc, badge in _LOCATION_BADGE.items():
        lp = progress.get(loc)
        if lp and lp.passed:
            keys.add(badge)

    if getattr(user, "post_test_done", False):
        keys.add("atlas_sage")

    return keys


def grant_new(user):
    """Grant any newly-qualifying achievements. Returns the list of newly-earned
    keys (in display order). Safe to call repeatedly — never double-grants."""
    have = {a.achievement_key for a in Achievement.query.filter_by(user_id=user.id).all()}
    qualifying = _qualifying(user)
    new = []
    for a in ACHIEVEMENTS:
        k = a["key"]
        if k in qualifying and k not in have:
            db.session.add(Achievement(user_id=user.id, achievement_key=k))
            new.append(k)
    if new:
        try:
            db.session.commit()
        except IntegrityError:
            # A concurrent request granted the same key first (unique index).
            # Roll back; that other request reports/celebrates the new keys.
            db.session.rollback()
            new = []
    return new


def earned_map(user):
    """{achievement_key: earned_at} for everything this user has earned."""
    return {a.achievement_key: a.earned_at for a in Achievement.query.filter_by(user_id=user.id).all()}
