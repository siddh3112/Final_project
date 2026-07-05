"""
INTEGRATION tests — authentication through the Flask test client.

Register / login / logout, duplicate rejection, password hashing, condition
capture, and login-required protection. Runs on the in-memory DB (conftest).
"""

from app.models import User, db


def _fresh():
    db.session.expire_all()


# ── register creates a hashed user, logs them in, and honours condition ──
def test_register_creates_hashed_user_and_logs_in(client):
    r = client.post(
        "/auth/register?condition=control",
        data={"username": "newbie", "email": "New@Example.com", "password": "s3cret"},
    )
    assert r.status_code == 302 and "/auth" not in r.headers["Location"]  # → hub, not back to auth
    _fresh()
    u = User.query.filter_by(username="newbie").first()
    assert u is not None
    assert u.condition == "control", "condition must be captured from the query"
    assert u.email == "new@example.com", "email is normalised to lowercase"
    # password is stored HASHED, never in plaintext, and verifies correctly
    assert "s3cret" not in (u.password_hash or "")
    assert u.check_password("s3cret") and not u.check_password("wrong")


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
