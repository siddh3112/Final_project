import random

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Condition machinery retained but DORMANT: all users are currently assigned
# 'game' (see _assign_condition), so Professor Atlas is universal. The two-
# condition split can be restored by uncommenting _assign_condition. This tuple
# is kept for that revert; assignment is always SERVER-controlled, never from
# client input.
CONDITIONS = ("game", "control")


def _assign_condition():
    """Assign EVERY new participant to the 'game' condition, so Professor Atlas is
    available to all users (single-condition study).

    The two-group machinery is deliberately kept intact and simply always
    evaluates to 'game' now: the `condition` field, the template gates
    ({% if current_user.condition == 'game' %}), and the /npc/chat 403 gate all
    still exist — they just never gate anyone out because no one is 'control'.
    Assignment is still SERVER-controlled; no client-supplied value is consulted.

    REVERSIBLE: to restore the randomised, balanced two-group split, delete the
    `return "game"` and un-comment the original allocation below. Nothing
    structural was removed."""
    return "game"
    # ── KEPT INTENTIONALLY, NOT DEAD CODE ──────────────────────────────────────
    # This is the original balanced-random allocation for the two-group study. It
    # is commented out rather than deleted so the split can be restored by hand in
    # one step: delete the `return "game"` above and un-comment the block below.
    # Please do not "tidy" this away; it is the documented revert path, and the
    # CONDITIONS tuple, the `import random`, the template gates and the /npc/chat
    # gate are all retained for the same reason.
    # ───────────────────────────────────────────────────────────────────────────
    # game_n = User.query.filter_by(condition="game").count()
    # control_n = User.query.filter_by(condition="control").count()
    # if game_n < control_n:
    #     return "game"
    # if control_n < game_n:
    #     return "control"
    # return random.choice(CONDITIONS)


def _reset_presentation_session():
    """Drop per-browser session state so a freshly authenticated user starts
    clean: their own one-time map reveals (fog recede / path draw / pin ignite),
    their own reading progress, and their own front-of-house SETTINGS, not the
    previous user's.

    Settings (theme, sound, voice, reduce_motion, large_text, voice_name,
    skip_hooks) live only in session["prefs"] (no browser storage), so popping that
    key makes current_prefs() fall back to DEFAULT_PREFS on the next render. This
    runs ONLY at login/registration, so mid-session setting changes still apply
    until the next login. Never touches progress tables or research data (progress,
    BookRead, run_history, achievements are all in the DB, not the session)."""
    session.pop("seen", None)
    session.pop("read_books", None)
    session.pop("prefs", None)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create a participant account and sign them straight in.

    The study condition is assigned by the SERVER here (see _assign_condition) and
    is never read from the form or the URL, so a participant cannot place
    themselves in a group. Duplicate username or email is rejected before any row
    is created, and the presentation session is reset on success so the new user
    does not inherit the previous one's settings or one-time reveals.
    """
    if current_user.is_authenticated:
        return redirect(url_for("game.hub"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None
        if not username or not email or not password:
            error = "All fields are required."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "That email is already registered."

        if error:
            flash(error, "danger")
            return render_template("auth/register.html")

        # Single-condition configuration — every user is assigned 'game' by the
        # SERVER (the random/balanced split is retained, commented, in
        # _assign_condition for a future between-groups study). Any client-supplied
        # condition (URL param or form field) is IGNORED regardless.
        user = User(username=username, email=email, condition=_assign_condition())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        _reset_presentation_session()
        return redirect(url_for("game.hub"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Sign in with either username or email.

    The same generic "Invalid username or password" message is used whether the
    account is missing or the password is wrong, so the form cannot be used to
    discover which accounts exist. Settings and one-time reveals are reset on
    success, so a shared browser never carries the previous participant's state
    into this session.
    """
    if current_user.is_authenticated:
        return redirect(url_for("game.hub"))

    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()
        if user and user.check_password(password):
            login_user(user)
            _reset_presentation_session()
            return redirect(url_for("game.hub"))
        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
