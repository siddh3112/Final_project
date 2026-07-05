"""
Shared pytest fixtures for Atlas Quest.

Everything here runs against a THROWAWAY in-memory SQLite database with Ollama
stubbed OFF — it never touches instance/atlas_quest.db and never needs the model
running. A fresh database is built for every test (function-scoped `app`), so
tests are fully isolated.

Fixtures (conventionally named so other test files can reuse them):
  - app          : a configured Flask app on an in-memory DB, inside an app context
  - client       : app.test_client()
  - db_session   : the SQLAlchemy session (db.session)
  - user_factory : create a user in any state (fresh / mid / passed / done) in one call
  - login        : authenticate the test client as a given user (no password round-trip)
  - as_correct   : build post-test form answers with exactly N correct
"""

import json

import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.models import BookRead, KnowledgeTest, LocationProgress, User, db
from app.eval_content import POST_TEST
from app.game_content import LOCATION_ORDER

# ── The learning locations, in unlock order ──
# Sourced from the app so the post-test gate ("all locations passed") stays in
# sync as locations are added/removed (e.g. the Chronicle).
ALL_LOCATIONS = tuple(LOCATION_ORDER)


@pytest.fixture
def app():
    """A fresh Flask app on a private in-memory DB (Ollama off). Function-scoped,
    so each test starts with an empty, isolated database."""
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            # StaticPool keeps ONE shared connection, so the in-memory DB created
            # by the fixture is the same one the test client's requests see.
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
            "OLLAMA_ENABLED": False,          # never call the model in tests
            "WTF_CSRF_ENABLED": False,
        }
    )
    # Hard guard: a bug in config handling must never point tests at the real DB.
    assert ":memory:" in application.config["SQLALCHEMY_DATABASE_URI"], (
        "tests must run on an in-memory DB, not atlas_quest.db"
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    return db.session


@pytest.fixture
def user_factory(app):
    """Create a user in any state in one call.

    make(condition="game"|"control",
         passed=(<location keys>),          # LocationProgress rows, passed=True
         post_test_done=False,
         sectors=(0,1,...),                 # BookRead 'sector-N' rows for ai_lab
         knowledge_tests=[{"score": 8, "answers": {...}, "time": 120}, ...],
         password="pw")
    Returns the committed User.
    """
    seq = {"n": 0}

    def make(
        *,
        condition="game",
        passed=(),
        post_test_done=False,
        sectors=(),
        knowledge_tests=None,
        seen_intro=True,
        password="pw",
        username=None,
    ):
        seq["n"] += 1
        uname = username or f"user{seq['n']}"
        u = User(
            username=uname,
            email=f"{uname}@test.local",
            condition=condition,
            post_test_done=post_test_done,
            seen_intro=seen_intro,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.flush()  # assign u.id

        for loc in passed:
            db.session.add(
                LocationProgress(
                    user_id=u.id, location=loc, passed=True,
                    best_score=4, attempts_count=1,
                )
            )
        for s in sectors:
            db.session.add(
                BookRead(user_id=u.id, location="ai_lab", book_id=f"sector-{s}")
            )
        for kt in (knowledge_tests or []):
            db.session.add(
                KnowledgeTest(
                    user_id=u.id,
                    answers_json=json.dumps(kt.get("answers", {})),
                    score=kt["score"],
                    time_spent_seconds=kt.get("time"),
                )
            )
        db.session.commit()
        return u

    return make


@pytest.fixture
def login(client):
    """Authenticate the test client as `user` via the Flask-Login session key —
    no password round-trip, no dependency on the login form."""
    def _login(user):
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True
    return _login


@pytest.fixture
def as_correct():
    """Build POST_TEST form data with exactly `n` correct answers (the rest a
    deliberately wrong option). Also carries a timing field the route stores."""
    def _make(n, time_spent_seconds=120):
        data = {"time_spent_seconds": str(time_spent_seconds)}
        for i, q in enumerate(POST_TEST):
            if i < n:
                data[q["key"]] = q["correct"]
            else:
                wrong = next(letter for letter in q["options"] if letter != q["correct"])
                data[q["key"]] = wrong
        return data
    return _make
