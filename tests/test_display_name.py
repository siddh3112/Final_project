"""
Chosen display name: unique (case-insensitively), set at registration, editable
in settings, and shown on the leaderboard instead of the login username.

The privacy rule these tests protect: a login username is never auto-published.
Before a player picks a name, the board falls back to their anonymised handle.
"""

from app.models import LocationProgress, User, db
from app.services.handles import handle_for, name_taken, validate_display_name
from app.game_content import LOCATION_ORDER

ALL = tuple(LOCATION_ORDER)


def _register(client, username, email, display_name, password="pw123456"):
    return client.post(
        "/auth/register",
        data={
            "username": username,
            "email": email,
            "display_name": display_name,
            "password": password,
        },
        follow_redirects=True,
    )


# ──────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────

def test_registration_sets_display_name(client):
    r = _register(client, "alice", "a@t.local", "StarSeeker")
    assert r.status_code == 200
    u = User.query.filter_by(username="alice").first()
    assert u is not None
    assert u.display_name == "StarSeeker"


def test_duplicate_display_name_rejected_at_registration(client):
    _register(client, "alice", "a@t.local", "StarSeeker")
    client.get("/auth/logout")

    r = _register(client, "bob", "b@t.local", "StarSeeker")
    assert r.status_code == 200, "must not crash"
    body = r.get_data(as_text=True)
    assert "already taken" in body, "a clear message is shown"
    assert User.query.filter_by(username="bob").first() is None, "no account created"


def test_duplicate_display_name_is_case_insensitive(client):
    _register(client, "alice", "a@t.local", "StarSeeker")
    client.get("/auth/logout")

    # different case = the SAME name
    r = _register(client, "bob", "b@t.local", "starseeker")
    assert r.status_code == 200
    assert "already taken" in r.get_data(as_text=True)
    assert User.query.filter_by(username="bob").first() is None

    # and a genuinely different name works
    r2 = _register(client, "bob", "b@t.local", "MoonWright")
    assert r2.status_code == 200
    assert User.query.filter_by(username="bob").first() is not None


def test_blank_display_name_rejected(client):
    r = _register(client, "alice", "a@t.local", "   ")
    assert r.status_code == 200
    assert "display name" in r.get_data(as_text=True).lower()
    assert User.query.filter_by(username="alice").first() is None


# ──────────────────────────────────────────────────────────────────
# Settings
# ──────────────────────────────────────────────────────────────────

def test_display_name_editable_in_settings(client, user_factory, login):
    u = user_factory()
    u.display_name = "OldName"
    db.session.commit()
    login(u)

    r = client.post("/display-name", json={"display_name": "NewName"})
    assert r.status_code == 200 and r.get_json()["ok"] is True
    db.session.expire_all()
    assert db.session.get(User, u.id).display_name == "NewName"


def test_duplicate_display_name_rejected_in_settings(client, user_factory, login):
    taken = user_factory()
    taken.display_name = "StarSeeker"
    other = user_factory()
    other.display_name = "MoonWright"
    db.session.commit()

    login(other)
    # exact clash
    r = client.post("/display-name", json={"display_name": "StarSeeker"})
    assert r.status_code == 409, "graceful rejection, never a crash"
    assert "already taken" in r.get_json()["error"]
    # different case is still a clash
    r2 = client.post("/display-name", json={"display_name": "STARSEEKER"})
    assert r2.status_code == 409
    db.session.expire_all()
    assert db.session.get(User, other.id).display_name == "MoonWright", "unchanged"


def test_keeping_your_own_name_is_not_a_duplicate(client, user_factory, login):
    u = user_factory()
    u.display_name = "StarSeeker"
    db.session.commit()
    login(u)
    r = client.post("/display-name", json={"display_name": "StarSeeker"})
    assert r.status_code == 200, "your own name must not count as taken"


# ──────────────────────────────────────────────────────────────────
# Leaderboard display + the privacy fallback
# ──────────────────────────────────────────────────────────────────

def test_board_shows_display_name_not_username(client, user_factory, login):
    u = user_factory(username="secretlogin")
    u.display_name = "StarSeeker"
    db.session.commit()
    assert handle_for(u) == "StarSeeker"
    assert "secretlogin" not in handle_for(u)


def test_without_a_chosen_name_the_board_falls_back_to_the_handle(user_factory):
    """Option B: the default must never be the login username."""
    u = user_factory(username="secretlogin")
    u.display_name = None
    u.display_handle = "Star Reader 4F2A"
    db.session.commit()
    shown = handle_for(u)
    assert shown == "Star Reader 4F2A"
    assert "secretlogin" not in shown


def test_validator_rules(app):   # `app` gives the context the uniqueness query needs
    assert validate_display_name("")[1] is not None
    assert validate_display_name("x")[1] is not None          # too short
    assert validate_display_name("y" * 41)[1] is not None     # too long
    assert validate_display_name("  Fine Name  ") == ("Fine Name", None)  # trimmed


def test_name_taken_helper_is_case_insensitive(user_factory):
    u = user_factory()
    u.display_name = "StarSeeker"
    db.session.commit()
    assert name_taken("starseeker") is True
    assert name_taken("STARSEEKER") is True
    assert name_taken("StarSeeker", exclude_user_id=u.id) is False
    assert name_taken("Nobody") is False
