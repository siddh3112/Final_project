"""
Front-of-house user preferences for Atlas Quest.

These are PRESENTATION-only settings (audio, accessibility) stored in the Flask
session. They never touch scoring, progress, unlocking, achievements, condition,
or any research data — they only change how the app looks/sounds for this browser.
"""

from flask import session

# The only keys we accept, with their defaults. Booleans unless listed in
# STRING_PREFS below.
DEFAULT_PREFS = {
    "sound": True,          # master Web-Audio SFX on/off
    "voice": True,          # Professor Atlas read-aloud (AtlasVoice) on/off
    "reduce_motion": False, # calm animations / particles / parallax
    "large_text": False,    # bump base font size for readability
    "skip_hooks": False,    # skip the guess-first hook prompts, straight to lessons
    "voice_name": "",       # chosen read-aloud voice by name; "" = automatic/best
    "theme": "midnight",    # shared-frame colour theme (reskins chrome only)
}

# Keys whose value is a free string (not a boolean). Kept short and presentation
# only — never touches scoring, progress, or research data.
STRING_PREFS = {"voice_name", "theme"}
_MAX_STRING_LEN = 120

# The only theme names we accept (used as a CSS class, so it is whitelisted).
ALLOWED_THEMES = {"midnight", "parchment", "ocean"}


def _coerce_string(key, value):
    """Coerce a string pref; whitelist the theme name to a known-safe value."""
    s = ("" if value is None else str(value))[:_MAX_STRING_LEN]
    if key == "theme" and s not in ALLOWED_THEMES:
        return DEFAULT_PREFS["theme"]
    return s


def current_prefs():
    """Session prefs merged over defaults (always a full, coerced dict)."""
    saved = session.get("prefs") or {}
    prefs = dict(DEFAULT_PREFS)
    for key in DEFAULT_PREFS:
        if key in saved:
            if key in STRING_PREFS:
                prefs[key] = _coerce_string(key, saved[key])
            else:
                prefs[key] = bool(saved[key])
    return prefs


def set_prefs(updates):
    """Merge validated updates into the session. Unknown keys are ignored."""
    saved = dict(session.get("prefs") or {})
    for key, value in (updates or {}).items():
        if key in STRING_PREFS:
            saved[key] = _coerce_string(key, value)
        elif key in DEFAULT_PREFS:
            saved[key] = bool(value)
    session["prefs"] = saved
    session.permanent = True
    return current_prefs()


# ── One-time presentation reveals ("seen" flags) ──
# Tracks which hub moments have already played (opening cinematic, fog-recede
# reveals, path draws, final-pin ignite) so each plays exactly once. Stored in
# the session like prefs — presentation only, never in research tables.
SEEN_FLAGS = {
    "intro",              # opening cinematic viewed
    "unlock_ai_lab",      # fog-recede reveal played
    "unlock_observatory",
    "path_library",       # golden path draw played (from this pin onward)
    "path_ai_lab",
    "path_observatory",
    "ignite_final",       # Final Ascent pin ignition played
    "epilogue",           # closing cinematic viewed (post-test complete)
}


def seen_flags():
    """{flag: True} for every whitelisted reveal this session has played."""
    saved = session.get("seen") or {}
    return {k: True for k in SEEN_FLAGS if saved.get(k)}


def mark_seen(flags):
    """Mark whitelisted flags as seen. Unknown flags are ignored."""
    saved = dict(session.get("seen") or {})
    for f in flags or []:
        if f in SEEN_FLAGS:
            saved[f] = True
    session["seen"] = saved
    session.permanent = True
    return seen_flags()
