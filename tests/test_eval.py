"""
Research-critical invariant tests for Atlas Quest.

These VERIFY the app's grading / gating / condition / persistence behaviour
against the real code. They must never drive the app to change those rules — if
one fails, it's either a test mismatch (fix the test) or a real app bug (report
it). Nothing here weakens grading, thresholds, scoring, or logging.
"""

import json

import pytest

from app.models import KnowledgeTest, RunHistory, LocationProgress, BookRead, db
from app.game_content import (
    PASS_THRESHOLD,
    QUIZZES,
    grade_quiz,
    get_questions_by_keys,
)
from app.eval_content import POST_TEST, POST_TEST_PASS
from app.game_content import LOCATION_ORDER

# The learning locations, in unlock order. Imported from the app so the post-test
# gate ("all locations passed") stays in sync as locations are added/removed.
ALL_LOCATIONS = tuple(LOCATION_ORDER)

SUBMIT = "/eval/post-test/submit"
POST_TEST_GET = "/eval/post-test"


def _fresh():
    """Drop cached identity-map state so post-request reads hit the DB."""
    db.session.expire_all()


# ────────────────────────────────────────────────────────────────────
#  Trial grading — passes at >= PASS_THRESHOLD (3 of 4); score = # correct
# ────────────────────────────────────────────────────────────────────
def _library_trial(n_correct):
    """Build a 4-question library trial submission with exactly n correct."""
    shown = [q["key"] for q in QUIZZES["library"]][:4]
    qs = get_questions_by_keys("library", shown)
    submitted = {}
    for i, q in enumerate(qs):
        if i < n_correct:
            submitted[q["key"]] = q["correct"]
        else:
            submitted[q["key"]] = next(l for l in q["options"] if l != q["correct"])
    return submitted, shown


def test_trial_score_is_count_of_correct():
    for n in range(5):
        submitted, shown = _library_trial(n)
        _results, score, total, _passed = grade_quiz("library", submitted, shown_keys=shown)
        assert score == n, f"trial score should equal #correct ({n}), got {score}"
        assert total == 4


def test_trial_passes_at_threshold_3_of_4():
    assert PASS_THRESHOLD == 3  # the graded threshold, unchanged
    # 2/4 fails, 3/4 passes, 4/4 passes
    for n, expect_pass in [(2, False), (3, True), (4, True)]:
        submitted, shown = _library_trial(n)
        _r, score, _t, passed = grade_quiz("library", submitted, shown_keys=shown)
        assert score == n
        assert passed is expect_pass, f"{n}/4 passed should be {expect_pass}"


# ────────────────────────────────────────────────────────────────────
#  Post-test — score = count of correct answers
# ────────────────────────────────────────────────────────────────────
def test_posttest_score_is_count_of_correct(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    for n in (0, 6, len(POST_TEST)):
        r = client.post(SUBMIT, data=as_correct(n))
        assert r.status_code == 200
        _fresh()
        kt = (
            KnowledgeTest.query.filter_by(user_id=u.id)
            .order_by(KnowledgeTest.id.desc())
            .first()
        )
        assert kt.score == n, f"post-test score should be #correct ({n}), got {kt.score}"


def test_posttest_pass_mark_is_8_of_10():
    # Confirm the pass gate actually exists in the code (not invented by the test).
    assert POST_TEST_PASS == 8
    assert len(POST_TEST) == 10


# ────────────────────────────────────────────────────────────────────
#  knowledge_tests records EVERY attempt (answers + score + time), pass or fail
# ────────────────────────────────────────────────────────────────────
def test_knowledge_tests_records_every_attempt(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(8, time_spent_seconds=111))   # pass
    client.post(SUBMIT, data=as_correct(3, time_spent_seconds=222))   # fail
    _fresh()
    rows = (
        KnowledgeTest.query.filter_by(user_id=u.id)
        .order_by(KnowledgeTest.id.asc())
        .all()
    )
    assert len(rows) == 2, "both pass and fail attempts must be recorded"
    assert [r.score for r in rows] == [8, 3]
    assert [r.time_spent_seconds for r in rows] == [111, 222]
    # answers persisted (the p1..p10 keys are present in the stored JSON)
    stored = json.loads(rows[0].answers_json)
    assert all(q["key"] in stored for q in POST_TEST)


# ────────────────────────────────────────────────────────────────────
#  run_history is ADDITIVE — a retake ADDS a row; old rows never change
# ────────────────────────────────────────────────────────────────────
def test_run_history_is_additive(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(8))
    _fresh()
    first = RunHistory.query.filter_by(user_id=u.id).order_by(RunHistory.id.asc()).all()
    assert len(first) == 1
    snapshot = (first[0].id, first[0].combined_score, first[0].post_test_score)

    # explicit retake
    client.post(SUBMIT, data=as_correct(10))
    _fresh()
    rows = RunHistory.query.filter_by(user_id=u.id).order_by(RunHistory.id.asc()).all()
    assert len(rows) == 2, "a retake must ADD a run_history row"
    # the original row is untouched (id, combined_score, post_test_score unchanged)
    assert (rows[0].id, rows[0].combined_score, rows[0].post_test_score) == snapshot
    assert rows[1].post_test_score == 10


# ────────────────────────────────────────────────────────────────────
#  post_test_done: flips only on a pass, and PERSISTS (re-entry = results)
# ────────────────────────────────────────────────────────────────────
def test_post_test_done_only_on_pass(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(7))   # below the 8/10 mark → fail
    _fresh()
    assert db.session.get(type(u), u.id).post_test_done is False

    client.post(SUBMIT, data=as_correct(8))   # meets the mark → pass
    _fresh()
    assert db.session.get(type(u), u.id).post_test_done is True


def test_completion_persists_reentry_shows_results(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(9))   # pass
    _fresh()
    assert db.session.get(type(u), u.id).post_test_done is True

    # Return to map, come back: GET must show RESULTS, not a fresh blank test.
    r = client.get(POST_TEST_GET)
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert 'id="ascent-results"' in body, "re-entry must render the results page"
    assert 'id="ascent-form"' not in body, "re-entry must NOT render a fresh test"
    # ...and completion still persists (GET is read-only, records nothing new)
    _fresh()
    assert db.session.get(type(u), u.id).post_test_done is True
    assert KnowledgeTest.query.filter_by(user_id=u.id).count() == 1


def test_explicit_retake_shows_fresh_test(client, user_factory, login):
    u = user_factory(passed=ALL_LOCATIONS, post_test_done=True,
                     knowledge_tests=[{"score": 9, "answers": {q["key"]: q["correct"] for q in POST_TEST}}])
    login(u)
    r = client.get(POST_TEST_GET + "?retake=1")
    body = r.get_data(as_text=True)
    assert 'id="ascent-form"' in body, "explicit retake must render a fresh test"


# ────────────────────────────────────────────────────────────────────
#  Gating — post-test only after all three locations are passed
# ────────────────────────────────────────────────────────────────────
def test_posttest_gated_until_all_locations_passed(client, user_factory, login, as_correct):
    u = user_factory(passed=("library",))   # only one of three
    login(u)
    # GET redirects to the hub
    r = client.get(POST_TEST_GET)
    assert r.status_code == 302 and "/eval" not in r.headers["Location"]
    # POST is refused and records NOTHING
    r2 = client.post(SUBMIT, data=as_correct(10))
    assert r2.status_code == 302
    _fresh()
    assert KnowledgeTest.query.filter_by(user_id=u.id).count() == 0


def test_posttest_open_when_all_passed(client, user_factory, login):
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    r = client.get(POST_TEST_GET)
    assert r.status_code == 200
    assert 'id="ascent-form"' in r.get_data(as_text=True)


# ────────────────────────────────────────────────────────────────────
#  Condition separation — a game user gets Atlas/NPC; a control user never does
# ────────────────────────────────────────────────────────────────────
def test_control_user_cannot_use_atlas(client, user_factory, login):
    control = user_factory(condition="control", passed=("library",))
    login(control)
    r = client.post("/npc/chat", json={"message": "help", "location": "library"})
    assert r.status_code == 403, "control users must not reach Professor Atlas"


def test_game_user_can_use_atlas(client, user_factory, login):
    game = user_factory(condition="game", passed=("library",))
    login(game)
    r = client.post("/npc/chat", json={"message": "what is AI?", "location": "library"})
    assert r.status_code != 403, "game users must be able to reach Professor Atlas"


# ────────────────────────────────────────────────────────────────────
#  Unknown-input rejection — /progress and /read reject bogus ids
# ────────────────────────────────────────────────────────────────────
def test_progress_rejects_unknown_ids(client, user_factory, login):
    u = user_factory()
    login(u)
    # bogus ids are ignored (not stored)
    client.post("/location/ai_lab/progress", json={"item": "sector-99"})
    client.post("/location/ai_lab/progress", json={"item": "'; DROP TABLE users;--"})
    _fresh()
    assert BookRead.query.filter_by(user_id=u.id, location="ai_lab").count() == 0
    # a valid id IS stored
    r = client.post("/location/ai_lab/progress", json={"item": "sector-0"})
    assert r.status_code == 200
    _fresh()
    rows = BookRead.query.filter_by(user_id=u.id, location="ai_lab").all()
    assert [x.book_id for x in rows] == ["sector-0"]


def test_read_rejects_unknown_book(client, user_factory, login):
    from app.game_content import LOCATIONS
    u = user_factory()
    login(u)
    client.post("/location/library/read", json={"book": "not-a-real-book"})
    _fresh()
    assert BookRead.query.filter_by(user_id=u.id, location="library").count() == 0
    # a real book id IS stored
    real_book = LOCATIONS["library"]["books"][0]["id"]
    r = client.post("/location/library/read", json={"book": real_book})
    assert r.status_code == 200
    _fresh()
    rows = BookRead.query.filter_by(user_id=u.id, location="library").all()
    assert [x.book_id for x in rows] == [real_book]
