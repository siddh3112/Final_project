"""
INTEGRATION tests — the game loop through the Flask test client.

The unlock chain, the full side effects of a graded Trial submission, and —
since Trial grading is now SERVER-AUTHORITATIVE — its tamper resistance: the
server picks + stores the question set under an attempt id, and forged/duplicate
keys, mismatched ids, and replays are all rejected. Verifies behaviour; never
relaxes gating, scoring, or logging to pass.
"""

from app.models import (
    LocationProgress, QuizAttempt, GameSession, Achievement, db,
)
from app.game_content import LOCATIONS, QUIZZES, TRIAL_COUNT, get_questions_by_keys


def _fresh():
    db.session.expire_all()


def _start(client, loc):
    """GET the Trial so the SERVER creates + stores this attempt; return
    (attempt_id, stored_keys, question dicts). The browser never chooses the set."""
    if LOCATIONS[loc]["interaction"] == "terminal":
        client.get(f"/location/{loc}")
    else:
        client.get(f"/location/{loc}/trial")
    with client.session_transaction() as s:
        att = s.get(f"trial_{loc}")
    assert att, f"server did not create a trial attempt for {loc}"
    return att["aid"], att["keys"], get_questions_by_keys(loc, att["keys"])


def _answer_data(qs, n_correct):
    """Answers keyed by the SERVER's questions: first n_correct right, rest wrong."""
    data = {}
    for i, q in enumerate(qs):
        data[q["key"]] = q["correct"] if i < n_correct else next(l for l in q["options"] if l != q["correct"])
    return data


def _submit(client, loc, n_correct):
    aid, keys, qs = _start(client, loc)
    data = {"attempt_id": aid, "consulted": ""}
    data.update(_answer_data(qs, n_correct))
    return client.post(f"/location/{loc}/submit", data=data)


# ── the unlock chain is enforced at the route level ─────────────────────
def test_first_location_unlocked_later_ones_gated(client, user_factory, login):
    u = user_factory()
    login(u)
    assert client.get("/location/library/trial").status_code == 200, "first location is open"
    r = client.get("/location/chronicle/trial")
    assert r.status_code == 302 and "/location/chronicle" not in r.headers["Location"]


def test_passing_a_location_unlocks_the_next(client, user_factory, login):
    u = user_factory()
    login(u)
    assert client.get("/location/chronicle/trial").status_code == 302  # locked first
    _submit(client, "library", 4)
    _fresh()
    assert client.get("/location/chronicle/trial").status_code == 200  # now open


# ── a passing submission: results + progress + logs + session + badge ───
def test_passing_submission_full_side_effects(client, user_factory, login):
    u = user_factory()
    login(u)
    gs = GameSession(user_id=u.id, location="library")
    db.session.add(gs)
    db.session.commit()

    aid, keys, qs = _start(client, "library")
    data = {"attempt_id": aid, "consulted": keys[0]}   # consulted the FIRST served question
    data.update(_answer_data(qs, 4))
    r = client.post("/location/library/submit", data=data)
    assert r.status_code == 200 and "results" in r.get_data(as_text=True).lower()

    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="library").first()
    assert lp.passed is True and lp.best_score == 4 and lp.attempts_count == 1

    attempts = QuizAttempt.query.filter_by(user_id=u.id, location="library").all()
    assert len(attempts) == TRIAL_COUNT
    assert {a.question_key for a in attempts} == set(keys), "graded the SERVER's stored set"
    assert all(a.is_correct for a in attempts)
    consulted_rows = [a for a in attempts if a.npc_consulted]
    assert [a.question_key for a in consulted_rows] == [keys[0]]

    _fresh()
    assert GameSession.query.filter_by(user_id=u.id, location="library").first().ended_at is not None
    assert Achievement.query.filter_by(user_id=u.id, achievement_key="first_steps").count() == 1


# ── a submission to a LOCKED location records nothing ───────────────────
def test_submit_to_locked_location_is_refused(client, user_factory, login):
    u = user_factory()   # library not passed → chronicle locked
    login(u)
    r = client.post("/location/chronicle/submit", data={"attempt_id": "anything"})
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


# ══════════════ SERVER-AUTHORITATIVE grading — tamper resistance ═════════════

def test_forged_duplicate_keys_cannot_pass(client, user_factory, login):
    """The classic exploit: claim the Trial was one known question ×4. The server
    ignores the browser key list entirely and grades its OWN four keys, so one
    known answer scores at most 1/4 — never a pass."""
    u = user_factory()
    login(u)
    aid, keys, qs = _start(client, "library")
    k0 = keys[0]
    c0 = get_questions_by_keys("library", [k0])[0]["correct"]
    forged = {"attempt_id": aid, "shown_keys": ",".join([k0] * 4), k0: c0}
    r = client.post("/location/library/submit", data=forged)
    assert r.status_code == 200
    _fresh()
    attempts = QuizAttempt.query.filter_by(user_id=u.id, location="library").all()
    assert len(attempts) == TRIAL_COUNT
    assert {a.question_key for a in attempts} == set(keys), "graded the server's set, not the forged list"
    assert sum(1 for a in attempts if a.is_correct) == 1, "one known answer scores 1, not 4"
    lp = LocationProgress.query.filter_by(user_id=u.id, location="library").first()
    assert lp.passed is False, "a forged one-answer submission must NOT pass"


def test_fewer_than_full_set_still_grades_full_set(client, user_factory, login):
    """Submitting answers for only 1 of the 4 served questions doesn't shrink the
    graded set — the missing three are graded as wrong against the stored set."""
    u = user_factory()
    login(u)
    aid, keys, qs = _start(client, "library")
    c0 = get_questions_by_keys("library", [keys[0]])[0]["correct"]
    r = client.post("/location/library/submit", data={"attempt_id": aid, keys[0]: c0})
    assert r.status_code == 200
    _fresh()
    attempts = QuizAttempt.query.filter_by(user_id=u.id, location="library").all()
    assert len(attempts) == TRIAL_COUNT and sum(1 for a in attempts if a.is_correct) == 1


def test_mismatched_attempt_id_is_rejected(client, user_factory, login):
    u = user_factory()
    login(u)
    _start(client, "library")   # a real attempt exists…
    r = client.post("/location/library/submit", data={"attempt_id": "forged-nonsense"})
    assert r.status_code == 302, "an unknown attempt id is rejected"
    _fresh()
    assert QuizAttempt.query.filter_by(user_id=u.id, location="library").count() == 0


def test_attempt_can_only_be_graded_once(client, user_factory, login):
    u = user_factory()
    login(u)
    aid, keys, qs = _start(client, "library")
    data = {"attempt_id": aid}
    data.update(_answer_data(qs, 4))
    r1 = client.post("/location/library/submit", data=data)
    r2 = client.post("/location/library/submit", data=data)   # replay
    assert r1.status_code == 200 and r2.status_code == 302
    _fresh()
    assert QuizAttempt.query.filter_by(user_id=u.id, location="library").count() == TRIAL_COUNT, \
        "a replayed attempt must not double-log"


def test_answer_key_not_in_trial_dom(client, user_factory, login):
    u = user_factory()
    login(u)
    html = client.get("/location/library/trial").get_data(as_text=True)
    assert "data-correct" not in html, "the correct answer must not be embedded in the page"
    assert 'name="shown_keys"' not in html, "no browser-trusted shown-keys list"
    assert 'name="attempt_id"' in html


def test_commit_endpoint_locks_first_answer(client, user_factory, login):
    """The /answer commit endpoint records the FIRST committed letter; a later
    call returns that same locked answer (so it can't be used to fish the key),
    and submit grades the locked answer."""
    u = user_factory()
    login(u)
    aid, keys, qs = _start(client, "library")
    k0 = keys[0]
    q0 = get_questions_by_keys("library", [k0])[0]
    c0 = q0["correct"]
    w0 = next(l for l in q0["options"] if l != c0)
    first = client.post("/location/library/answer",
                        json={"attempt_id": aid, "qkey": k0, "letter": w0}).get_json()
    retry = client.post("/location/library/answer",
                        json={"attempt_id": aid, "qkey": k0, "letter": c0}).get_json()
    assert first["is_correct"] is False
    assert retry["committed"] == w0, "first commit is locked; retry cannot switch it"
    client.post("/location/library/submit", data={"attempt_id": aid})
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="library", question_key=k0).first()
    assert row.selected_answer == w0 and row.is_correct is False


def test_commit_endpoint_rejects_unknown_question(client, user_factory, login):
    u = user_factory()
    login(u)
    aid, keys, qs = _start(client, "library")
    # a question key that isn't part of THIS attempt's stored set
    other = next(q["key"] for q in QUIZZES["library"] if q["key"] not in keys)
    r = client.post("/location/library/answer", json={"attempt_id": aid, "qkey": other, "letter": "A"})
    assert r.status_code == 400, "an off-attempt question is rejected"


# ── the hub renders for an authenticated user ───────────────────────────
def test_hub_renders(client, user_factory, login):
    login(user_factory(passed=("library",)))
    assert client.get("/").status_code == 200
