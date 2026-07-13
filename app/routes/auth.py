import random

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# The two study conditions. Assignment is SERVER-controlled (see _assign_condition)
# — never taken from client input — so the between-groups design stays valid.
CONDITIONS = ("game", "control")


def _assign_condition():
    """Randomly assign a study condition with BALANCED allocation: hand the next
    participant to whichever group currently has FEWER users (so the two groups
    never differ by more than one), breaking ties with a coin flip. Computed on
    the SERVER from live group counts — a participant can never choose their own
    group, and no client-supplied value is ever consulted."""
    game_n = User.query.filter_by(condition="game").count()
    control_n = User.query.filter_by(condition="control").count()
    if game_n < control_n:
        return "game"
    if control_n < game_n:
        return "control"
    return random.choice(CONDITIONS)


def _reset_presentation_session():
    """Drop per-browser session state so a freshly authenticated user starts
    clean: their own one-time map reveals (fog recede / path draw / pin ignite)
    and their own reading progress, not the previous user's. Never touches
    progress tables or research data."""
    session.pop("seen", None)
    session.pop("read_books", None)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
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

        # Study condition is assigned by the SERVER — random, balanced, and fixed
        # for the life of the account. Any client-supplied condition (URL param or
        # form field) is IGNORED so participants can't choose their own group.
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
