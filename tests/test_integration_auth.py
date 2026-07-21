"""
INTEGRATION tests — authentication through the Flask test client.

Register / login / logout, duplicate rejection, password hashing, SERVER-assigned
study condition, and login-required protection. Runs on the in-memory DB (conftest).
"""

from flask import g

from app.models import User, db


def _fresh():
    db.session.expire_all()


def _register_anon(client, i, condition_hint="game"):
    """Register one fresh, anonymous participant through the route. Clears the
    session + Flask-Login's cached user first (the test app-context is long-lived,
    so otherwise the previous registrant stays 'logged in' and gets redirected)."""
    with client.session_transaction() as s:
        s.clear()
    g.pop("_login_user", None)
    return client.post("/auth/register", data={
        "username": f"p{i}", "email": f"p{i}@ex.com", "password": "pw",
        "display_name": f"Explorer {i}",   # required since display names were added
        "condition": condition_hint,   # supplied on purpose — must be IGNORED
    })


# ── register creates a hashed user, logs them in; condition is SERVER-assigned ──
def test_register_creates_hashed_user_and_logs_in(client):
    r = client.post(
        "/auth/register?condition=control",   # supplied condition must be IGNORED
        data={"username": "newbie", "email": "New@Example.com", "password": "s3cret",
              "display_name": "Newbie Explorer", "condition": "control"},
    )
    assert r.status_code == 302 and "/auth" not in r.headers["Location"]  # → hub, not back to auth
    _fresh()
    u = User.query.filter_by(username="newbie").first()
    assert u is not None
    assert u.condition == "game", "single-condition study: the server always assigns 'game'"
    assert u.email == "new@example.com", "email is normalised to lowercase"
    # password is stored HASHED, never in plaintext, and verifies correctly
    assert "s3cret" not in (u.password_hash or "")
    assert u.check_password("s3cret") and not u.check_password("wrong")


# ── condition is server-assigned; a client-supplied value is ignored ──
def test_register_ignores_supplied_condition(client):
    """Single-condition study: the server ALWAYS assigns 'game' and never consults
    a client-supplied condition (URL param or form field)."""
    with client.session_transaction() as s:
        s.clear()
    g.pop("_login_user", None)
    client.post(
        "/auth/register?condition=control",   # supplied condition must be IGNORED
        data={"username": "z", "email": "z@ex.com", "password": "pw",
              "display_name": "Zed Explorer", "condition": "control"},
    )
    _fresh()
    u = User.query.filter_by(username="z").first()
    assert u.condition == "game", "server ignores the supplied condition and assigns 'game'"


# ── every new registration is assigned 'game' (Atlas is universal) ──
def test_register_all_new_users_are_game(client):
    """Single-condition study: every new user is assigned 'game' (so Professor
    Atlas is available to everyone). The two-group machinery is retained but always
    evaluates to 'game' — control is no longer allocated at registration. (A control
    user can still be set manually; test_control_user_cannot_use_atlas proves the
    gate machinery is intact and reversible.)"""
    N = 20
    for i in range(N):
        # even when the client keeps supplying 'control', the server assigns 'game'
        assert _register_anon(client, i, condition_hint="control").status_code == 302
    _fresh()
    game = User.query.filter_by(condition="game").count()
    control = User.query.filter_by(condition="control").count()
    assert game == N and control == 0, f"all new users must be 'game', got game={game} control={control}"


# ── no request can change a user's condition once assigned ──
def test_no_route_can_change_condition(client, user_factory, login):
    u = user_factory(condition="game")
    original = u.condition
    login(u)
    # the settings/prefs save must not touch condition…
    client.post("/prefs", data={"condition": "control", "sound": "false"})
    # …and re-posting to register while authenticated is redirected, changing nothing.
    client.post("/auth/register", data={
        "username": "x", "email": "x@x.com", "password": "pw", "condition": "control",
    })
    _fresh()
    assert db.session.get(User, u.id).condition == original, "no request may change a user's condition"


def test_register_rejects_duplicate_username(client, user_factory):
    user_factory(username="taken")
    r = client.post(
        "/auth/register",
        data={"username": "taken", "email": "other@x.com", "password": "pw"},
    )
    assert r.status_code == 200  # re-renders the form with an error (no redirect)
    _fresh()
    assert User.query.filter_by(username="taken").count() == 1, "must not create a duplicate"


def test_register_rejects_duplicate_email(client, user_factory):
    user_factory(username="a", password="pw")
    existing = User.query.filter_by(username="a").first()
    r = client.post(
        "/auth/register",
        data={"username": "b", "email": existing.email, "password": "pw"},
    )
    assert r.status_code == 200
    _fresh()
    assert User.query.filter_by(email=existing.email).count() == 1


def test_login_valid_and_invalid(client, user_factory):
    user_factory(username="alice", password="correct-horse")
    ok = client.post("/auth/login", data={"username": "alice", "password": "correct-horse"})
    assert ok.status_code == 302 and "/auth" not in ok.headers["Location"]  # → hub

    client.get("/auth/logout")
    bad = client.post("/auth/login", data={"username": "alice", "password": "nope"})
    assert bad.status_code == 200, "a bad password re-renders the login form"
    assert b"Invalid" in bad.data


def test_logout_then_protected_route_redirects_to_login(client, user_factory, login):
    u = user_factory()
    login(u)
    assert client.get("/").status_code == 200      # authenticated → hub renders
    client.get("/auth/logout")
    r = client.get("/")                             # anonymous → bounced to login
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_authenticated_user_cannot_reach_register(client, user_factory, login):
    login(user_factory())
    r = client.get("/auth/register")
    assert r.status_code == 302 and "/auth/register" not in r.headers["Location"]
