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
        "condition": condition_hint,   # supplied on purpose — must be IGNORED
    })


# ── register creates a hashed user, logs them in; condition is SERVER-assigned ──
def test_register_creates_hashed_user_and_logs_in(client):
    r = client.post(
        "/auth/register?condition=control",   # supplied condition must be IGNORED
        data={"username": "newbie", "email": "New@Example.com", "password": "s3cret",
              "condition": "control"},
    )
    assert r.status_code == 302 and "/auth" not in r.headers["Location"]  # → hub, not back to auth
    _fresh()
    u = User.query.filter_by(username="newbie").first()
    assert u is not None
    assert u.condition in ("game", "control"), "condition is server-assigned to a valid group"
    assert u.email == "new@example.com", "email is normalised to lowercase"
    # password is stored HASHED, never in plaintext, and verifies correctly
    assert "s3cret" not in (u.password_hash or "")
    assert u.check_password("s3cret") and not u.check_password("wrong")


# ── condition is server-assigned; a client-supplied value is ignored ──
def test_register_ignores_supplied_condition(client, user_factory):
    """Seed one game user so the balanced server MUST assign 'control' next; then
    register supplying condition=game everywhere — the server ignores it."""
    user_factory(condition="game")   # groups: game=1, control=0
    with client.session_transaction() as s:
        s.clear()
    g.pop("_login_user", None)
    client.post(
        "/auth/register?condition=game",
        data={"username": "z", "email": "z@ex.com", "password": "pw", "condition": "game"},
    )
    _fresh()
    u = User.query.filter_by(username="z").first()
    assert u.condition == "control", "server assigns the minority (control); supplied 'game' is ignored"


# ── over N registrations, allocation is random but BALANCED ──
def test_register_allocation_is_balanced(client):
    N = 20
    for i in range(N):
        assert _register_anon(client, i, condition_hint="game").status_code == 302
    _fresh()
    game = User.query.filter_by(condition="game").count()
    control = User.query.filter_by(condition="control").count()
    assert game + control == N
    # all N supplied "game"; if it were honoured we'd see 20/0. Balanced instead:
    assert abs(game - control) <= 1, f"allocation must stay balanced, got game={game} control={control}"
    assert game > 0 and control > 0, "both study groups must be represented"


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
