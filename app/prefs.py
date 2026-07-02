"""
Front-of-house user preferences for Atlas Quest.

These are PRESENTATION-only settings (audio, accessibility) stored in the Flask
session. They never touch scoring, progress, unlocking, achievements, condition,
or any research data — they only change how the app looks/sounds for this browser.
"""

from flask import session

# The only keys we accept, with their defaults. All booleans.
DEFAULT_PREFS = {
    "sound": True,          # master Web-Audio SFX on/off
    "voice": True,          # Professor Atlas read-aloud (AtlasVoice) on/off
    "reduce_motion": False, # calm animations / particles / parallax
    "large_text": False,    # bump base font size for readability
}


def current_prefs():
    """Session prefs merged over defaults (always a full, coerced dict)."""
    saved = session.get("prefs") or {}
    prefs = dict(DEFAULT_PREFS)
    for key in DEFAULT_PREFS:
        if key in saved:
            prefs[key] = bool(saved[key])
    return prefs


def set_prefs(updates):
    """Merge validated updates into the session. Unknown keys are ignored."""
    saved = dict(session.get("prefs") or {})
    for key, value in (updates or {}).items():
        if key in DEFAULT_PREFS:
            saved[key] = bool(value)
    session["prefs"] = saved
    session.permanent = True
    return current_prefs()
