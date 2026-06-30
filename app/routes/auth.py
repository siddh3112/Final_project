from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

VALID_CONDITIONS = {"game", "control"}


def _clean_condition(value):
    return value if value in VALID_CONDITIONS else "game"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("game.hub"))

    # Condition comes from the URL: /auth/register?condition=game|control
    condition = _clean_condition(request.args.get("condition", "game"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        condition = _clean_condition(request.form.get("condition", condition))

        error = None
        if not username or not email or not password:
            error = "All fields are required."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "That email is already registered."

        if error:
            flash(error, "danger")
            return render_template("auth/register.html", condition=condition)

        user = User(username=username, email=email, condition=condition)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("game.hub"))

    return render_template("auth/register.html", condition=condition)


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
            return redirect(url_for("game.hub"))
        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
