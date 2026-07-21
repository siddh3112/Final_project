"""
Anonymised display handles for the cross-player leaderboard.

Participants must not be identifiable to each other on a shared board, so the
leaderboard never shows the login username. Each user gets an in-world alias
("Wandering Cartographer 4F2A") assigned once at registration.

The suffix is random, NOT derived from the user id, username or email, so a
handle cannot be reversed back to a person or ordered by signup time. Handles are
stable once assigned, so a learner can still recognise their own row.
"""

import secrets

from ..models import User, db

# In-world aliases. Kept deliberately generic: none of them encodes anything
# about the participant.
_TITLES = (
    "Wandering Cartographer", "Star Reader", "Archive Keeper", "Lantern Bearer",
    "Compass Wright", "Chart Binder", "Dust Walker", "Sky Surveyor",
    "Margin Scribe", "Atlas Wayfarer", "Ledger Warden", "Orbit Plotter",
)


def _candidate():
    """One alias plus a short random suffix, e.g. 'Star Reader 4F2A'."""
    return f"{secrets.choice(_TITLES)} {secrets.token_hex(2).upper()}"


def ensure_handle(user, commit=True):
    """Give `user` an anonymised handle if they do not have one yet.

    Safe to call repeatedly: an existing handle is never changed, so a learner's
    identity on the board stays stable. Retries on the (unlikely) collision with
    the unique index, and falls back to a longer suffix rather than failing the
    request, since a handle is presentation only and must never block signup.
    """
    if getattr(user, "display_handle", None):
        return user.display_handle

    for _ in range(8):
        h = _candidate()
        if User.query.filter_by(display_handle=h).first() is None:
            user.display_handle = h
            break
    else:
        # Extremely unlikely; widen the suffix so it cannot keep colliding.
        user.display_handle = f"{secrets.choice(_TITLES)} {secrets.token_hex(4).upper()}"

    if commit:
        db.session.commit()
    return user.display_handle


def handle_for(user):
    """The name to SHOW for this user on the leaderboard.

    Order: the player's CHOSEN display name, else their auto-assigned anonymous
    handle, else a neutral placeholder. It never falls back to `username`, so a
    login identity is never published by default. A player who wants their
    username shown can simply type it as their display name.
    """
    return (
        getattr(user, "display_name", None)
        or getattr(user, "display_handle", None)
        or "Unknown Explorer"
    )


# ── Chosen display name: validation + case-insensitive uniqueness ──
DISPLAY_NAME_MIN = 2
DISPLAY_NAME_MAX = 40


def name_taken(name, exclude_user_id=None):
    """Is this display name already in use, ignoring case?

    Compares on lower() so "StarSeeker" and "starseeker" are the same name. Pass
    exclude_user_id when editing, so a player keeping their own name is not told
    it is taken.
    """
    from sqlalchemy import func

    if not name:
        return False
    q = User.query.filter(func.lower(User.display_name) == name.strip().lower())
    if exclude_user_id is not None:
        q = q.filter(User.id != exclude_user_id)
    return q.first() is not None


def validate_display_name(name, exclude_user_id=None):
    """Return (cleaned_name, error). error is None when the name is usable.

    Used by BOTH registration and settings so the rules and the wording cannot
    drift apart. Messages are plain and tell the player what to do next.
    """
    cleaned = (name or "").strip()
    if not cleaned:
        return cleaned, "Please choose a display name."
    if len(cleaned) < DISPLAY_NAME_MIN:
        return cleaned, f"Display name must be at least {DISPLAY_NAME_MIN} characters."
    if len(cleaned) > DISPLAY_NAME_MAX:
        return cleaned, f"Display name must be {DISPLAY_NAME_MAX} characters or fewer."
    if name_taken(cleaned, exclude_user_id=exclude_user_id):
        return cleaned, "That display name is already taken, please choose another."
    return cleaned, None
