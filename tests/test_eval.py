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
#  Post-test — score = count of correct answers (ONE graded attempt per user)
# ────────────────────────────────────────────────────────────────────
def test_posttest_score_is_count_of_correct(client, user_factory, login, as_correct):
    # Single attempt per participant, so use a FRESH user for each score.
    for n in (0, 6, len(POST_TEST)):
        u = user_factory(passed=ALL_LOCATIONS)
        login(u)
        r = client.post(SUBMIT, data=as_correct(n))
        assert r.status_code == 200
        _fresh()
        kt = KnowledgeTest.query.filter_by(user_id=u.id).order_by(KnowledgeTest.id.asc()).first()
        assert kt.score == n, f"post-test score should be #correct ({n}), got {kt.score}"


def test_posttest_pass_mark_is_8_of_10():
    # Confirm the pass gate actually exists in the code (not invented by the test).
    assert POST_TEST_PASS == 8
    assert len(POST_TEST) == 10


# ────────────────────────────────────────────────────────────────────
#  SINGLE ATTEMPT — the graded post-test is closed after the first submission
# ────────────────────────────────────────────────────────────────────
def test_knowledge_test_records_the_single_attempt(client, user_factory, login, as_correct):
    """Exactly ONE KnowledgeTest is recorded (answers + score + time); a later
    submission is rejected and never overwrites the first."""
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(8, time_spent_seconds=111))   # the one attempt
    client.post(SUBMIT, data=as_correct(3, time_spent_seconds=222))   # rejected — no new row
    _fresh()
    rows = KnowledgeTest.query.filter_by(user_id=u.id).order_by(KnowledgeTest.id.asc()).all()
    assert len(rows) == 1, "the graded assessment is single-attempt"
    assert rows[0].score == 8 and rows[0].time_spent_seconds == 111
    stored = json.loads(rows[0].answers_json)
    assert all(q["key"] in stored for q in POST_TEST)


def test_second_submission_after_pass_is_rejected(client, user_factory, login, as_correct):
    """After a PASS, a second submission is rejected: results are shown, no new
    KnowledgeTest, and the first (authoritative) score is not overwritten."""
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(9))       # pass
    r = client.post(SUBMIT, data=as_correct(2))   # attempt to overwrite with a fail
    body = r.get_data(as_text=True)
    assert 'id="ascent-results"' in body and 'id="ascent-form"' not in body, \
        "a resubmission shows the existing results, never a fresh test"
    _fresh()
    rows = KnowledgeTest.query.filter_by(user_id=u.id).all()
    assert len(rows) == 1 and rows[0].score == 9, "first attempt authoritative, not overwritten"


def test_second_submission_after_fail_is_rejected(client, user_factory, login, as_correct):
    """After a FAIL, a second submission is ALSO rejected — one attempt only; a
    fail is final and cannot be retried into a pass."""
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(4))       # fail
    client.post(SUBMIT, data=as_correct(10))      # rejected
    _fresh()
    rows = KnowledgeTest.query.filter_by(user_id=u.id).all()
    assert len(rows) == 1 and rows[0].score == 4
    assert db.session.get(type(u), u.id).post_test_done is False, "a failed attempt is final"


# ────────────────────────────────────────────────────────────────────
#  assessment_completed (attempt exists) is tracked SEPARATELY from passing
# ────────────────────────────────────────────────────────────────────
def test_assessment_completed_true_after_first_submission_regardless_of_score(
    client, user_factory, login, as_correct
):
    from app.routes.eval_routes import _assessment_completed
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    assert _assessment_completed(u) is False, "not completed before any attempt"
    client.post(SUBMIT, data=as_correct(3))   # a FAIL still COMPLETES the assessment
    _fresh()
    assert _assessment_completed(u) is True, "completed on first submission, pass or fail"
    assert db.session.get(type(u), u.id).post_test_done is False, \
        "completion is tracked separately from passing"


def test_post_test_done_only_on_pass(client, user_factory, login, as_correct):
    # A passing single attempt sets post_test_done…
    winner = user_factory(passed=ALL_LOCATIONS)
    login(winner)
    client.post(SUBMIT, data=as_correct(8))
    _fresh()
    assert db.session.get(type(winner), winner.id).post_test_done is True
    # …a failing single attempt does not (and can't be retried into a pass).
    loser = user_factory(passed=ALL_LOCATIONS)
    login(loser)
    client.post(SUBMIT, data=as_correct(7))
    _fresh()
    assert db.session.get(type(loser), loser.id).post_test_done is False


# ────────────────────────────────────────────────────────────────────
#  run_history: exactly one run; a blocked resubmit adds/overwrites nothing
# ────────────────────────────────────────────────────────────────────
def test_single_run_recorded_no_retake(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(8))
    client.post(SUBMIT, data=as_correct(10))   # rejected
    _fresh()
    rows = RunHistory.query.filter_by(user_id=u.id).order_by(RunHistory.id.asc()).all()
    assert len(rows) == 1, "single-attempt: no second run_history"
    assert rows[0].post_test_score == 8, "the one authoritative run is unchanged"


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
    _fresh()
    assert db.session.get(type(u), u.id).post_test_done is True
    assert KnowledgeTest.query.filter_by(user_id=u.id).count() == 1


def test_no_retake_of_graded_assessment(client, user_factory, login, as_correct):
    """Even a FAILED completion cannot re-open a fresh test; re-entry (including
    the old ?retake=1) shows the recorded results, never a blank test."""
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(5))   # completed (fail)
    for path in (POST_TEST_GET, POST_TEST_GET + "?retake=1"):
        body = client.get(path).get_data(as_text=True)
        assert 'id="ascent-results"' in body and 'id="ascent-form"' not in body, f"{path}: no fresh test"


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


# ────────────────────────────────────────────────────────────────────
#  Chronicle (4th location) is fully integrated into run_history + leaderboard
# ────────────────────────────────────────────────────────────────────
def test_run_records_chronicle_score_and_five_badges(client, user_factory, login, as_correct):
    """A completed run records the Chronicle Trial's best_score, and the combined
    score counts all FOUR locations and up to 5 badges."""
    from app.services.leaderboard import combined_score, score_of
    u = user_factory(passed=ALL_LOCATIONS)   # all 4 passed, best_score 4 each
    login(u)
    client.post(SUBMIT, data=as_correct(8))  # pass → Atlas Sage granted too
    _fresh()
    run = RunHistory.query.filter_by(user_id=u.id).first()
    assert run.chronicle_score == 4, "the Chronicle Trial best_score is recorded in run_history"
    assert run.library_score == run.chronicle_score == run.ai_lab_score == run.observatory_score == 4
    assert run.badges_count == 5, "all 5 badges are counted (incl. Chronicler + Atlas Sage)"
    # the stored/derived combined score includes the Chronicle among the 4 locations
    expected = combined_score(
        run.post_test_score,
        [run.library_score, run.chronicle_score, run.ai_lab_score, run.observatory_score],
        run.badges_count, run.time_spent_seconds,
    )
    assert score_of(run) == run.combined_score == expected


def test_leaderboard_breakdown_includes_chronicle(client, user_factory, login, as_correct):
    """The personal best-runs panel shows the Chronicle in the L·C·A·O line."""
    import re
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(8))          # records a run
    body = client.get("/").get_data(as_text=True)    # hub renders the best-runs panel server-side
    assert re.search(r'lb-locs">L\d+ · C\d+ · A\d+ · O\d+', body), \
        "leaderboard breakdown must show all four: L (Library) · C (Chronicle) · A (AI Lab) · O (Observatory)"
