"""
INTEGRATION tests — the game loop through the Flask test client.

The unlock chain enforced by the routes, and the full side effects of a graded
Trial submission: results page, LocationProgress, per-question QuizAttempt logs,
time-on-task session close, and achievement grant. Verifies behaviour — never
relaxes gating, scoring, or logging to pass.
"""

from app.models import (
    LocationProgress, QuizAttempt, GameSession, Achievement, db,
)
from app.game_content import QUIZZES, get_questions_by_keys


def _fresh():
    db.session.expire_all()


def _answers(loc, shown, n_correct):
    qs = get_questions_by_keys(loc, shown)
    out = {}
    for i, q in enumerate(qs):
        if i < n_correct:
            out[q["key"]] = q["correct"]
        else:
            out[q["key"]] = next(l for l in q["options"] if l != q["correct"])
    return out


def _submit(client, loc, n_correct, shown=None, consulted=()):
    """POST a graded Trial attempt exactly as the browser would."""
    shown = shown or [q["key"] for q in QUIZZES[loc]][:4]
    data = _answers(loc, shown, n_correct)
    data["shown_keys"] = ",".join(shown)
    data["consulted"] = ",".join(consulted)
    return client.post(f"/location/{loc}/submit", data=data)


# ── the unlock chain is enforced at the route level ─────────────────────
def test_first_location_unlocked_later_ones_gated(client, user_factory, login):
    u = user_factory()   # nothing passed
    login(u)
    assert client.get("/location/library/trial").status_code == 200, "first location is open"
    # a later location's trial bounces back to the hub
    r = client.get("/location/chronicle/trial")
    assert r.status_code == 302 and "/location/chronicle" not in r.headers["Location"]


def test_passing_a_location_unlocks_the_next(client, user_factory, login):
    u = user_factory()
    login(u)
    assert client.get("/location/chronicle/trial").status_code == 302  # locked first
    _submit(client, "library", 4)                                      # pass the Library
    _fresh()
    assert client.get("/location/chronicle/trial").status_code == 200  # now open


# ── a passing submission: results + progress + logs + session + badge ───
def test_passing_submission_full_side_effects(client, user_factory, login):
    u = user_factory()
    login(u)
    # an open time-on-task session exists and must be closed by the submit
    gs = GameSession(user_id=u.id, location="library")
    db.session.add(gs)
    db.session.commit()

    shown = [q["key"] for q in QUIZZES["library"]][:4]
    r = _submit(client, "library", 4, shown=shown, consulted=[shown[0]])
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "results" in body.lower()

    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="library").first()
    assert lp.passed is True and lp.best_score == 4 and lp.attempts_count == 1

    # one QuizAttempt row per shown question, correctness recorded
    attempts = QuizAttempt.query.filter_by(user_id=u.id, location="library").all()
    assert len(attempts) == len(shown)
    assert all(a.is_correct for a in attempts)
    # the consulted flag is recorded on exactly the consulted question
    consulted_rows = [a for a in attempts if a.npc_consulted]
    assert [a.question_key for a in consulted_rows] == [shown[0]]

    # the open session was closed
    _fresh()
    assert GameSession.query.filter_by(user_id=u.id, location="library").first().ended_at is not None

    # the location badge was granted
    assert Achievement.query.filter_by(user_id=u.id, achievement_key="first_steps").count() == 1


# ── a submission to a LOCKED location records nothing ───────────────────
def test_submit_to_locked_location_is_refused(client, user_factory, login):
    u = user_factory()   # library not passed → chronicle locked
    login(u)
    r = _submit(client, "chronicle", 4)
    assert r.status_code == 302, "a locked submission redirects"
    _fresh()
    assert QuizAttempt.query.filter_by(user_id=u.id, location="chronicle").count() == 0
    assert LocationProgress.query.filter_by(user_id=u.id, location="chronicle").count() == 0


# ── best_score never decreases; a pass is never revoked by a worse retake ──
def test_best_score_is_monotonic(client, user_factory, login):
    u = user_factory()
    login(u)
    _submit(client, "library", 4)   # 4/4 pass
    _submit(client, "library", 2)   # a worse retake
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="library").first()
    assert lp.best_score == 4, "best score must not drop on a worse attempt"
    assert lp.passed is True, "a pass is not revoked"
    assert lp.attempts_count == 2, "both attempts are counted"


# ── the route grades only the shown set, even if extra answers are POSTed ──
def test_route_grades_only_shown_set(client, user_factory, login):
    u = user_factory()
    login(u)
    shown = [q["key"] for q in QUIZZES["library"]][:2]   # only two questions shown
    data = _answers("library", shown, 2)
    # smuggle a (correct) answer for a non-shown question
    extra = [q for q in QUIZZES["library"] if q["key"] not in shown][0]
    data[extra["key"]] = extra["correct"]
    data["shown_keys"] = ",".join(shown)
    r = client.post("/location/library/submit", data=data)
    assert r.status_code == 200
    _fresh()
    attempts = QuizAttempt.query.filter_by(user_id=u.id, location="library").all()
    assert {a.question_key for a in attempts} == set(shown), "only shown questions are graded/logged"


# ── the hub renders for an authenticated user ───────────────────────────
def test_hub_renders(client, user_factory, login):
    login(user_factory(passed=("library",)))
    assert client.get("/").status_code == 200
