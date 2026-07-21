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
    """Build a 4-item Library trial submission with exactly n correct.

    The Library Trial is now "The Lexicon" — matching items whose answer is a
    scenario id — so a correct answer is the item's own scenario id and a wrong one
    is another item's scenario id. Grading is the same shared core (selected==correct).
    """
    shown = [q["key"] for q in QUIZZES["library"]][:4]
    qs = get_questions_by_keys("library", shown)
    submitted = {}
    for i, q in enumerate(qs):
        if i < n_correct:
            submitted[q["key"]] = q["correct"]
        else:
            submitted[q["key"]] = next(o["correct"] for o in qs if o["correct"] != q["correct"])
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
    """Exactly ONE KnowledgeTest is recorded (answers + score); a later submission
    is rejected and never overwrites the first. Timing is server-authoritative:
    the browser-supplied value is NOT the recorded duration (only kept as a
    non-authoritative reference)."""
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.get(POST_TEST_GET)                                        # server-stamps the start
    client.post(SUBMIT, data=as_correct(8, time_spent_seconds=111))  # the one attempt
    client.post(SUBMIT, data=as_correct(3, time_spent_seconds=222))  # rejected — no new row
    _fresh()
    rows = KnowledgeTest.query.filter_by(user_id=u.id).order_by(KnowledgeTest.id.asc()).all()
    assert len(rows) == 1, "the graded assessment is single-attempt"
    assert rows[0].score == 8
    # server-measured duration, NOT the forged browser value
    assert rows[0].time_spent_seconds != 111, "recorded time must not be the browser value"
    assert rows[0].time_spent_seconds is not None and rows[0].time_spent_seconds >= 0
    stored = json.loads(rows[0].answers_json)
    assert all(q["key"] in stored for q in POST_TEST)
    # the browser value is retained only as a non-authoritative reference
    assert stored.get("_client_time_spent_seconds") == 111


def test_assessment_timing_is_server_authoritative(client, user_factory, login, as_correct):
    """M2: the recorded/scoring duration is measured from the SERVER-stamped start
    (GET) to submit — a forged browser time is ignored. We push the server start
    5 minutes into the past and assert the recorded time reflects THAT, not the
    tiny client value, and that it also feeds the run (speed bonus) path."""
    from datetime import datetime, timedelta
    from app.models import GameSession, RunHistory
    from app.routes.eval_routes import ASSESSMENT_KEY

    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.get(POST_TEST_GET)   # server-stamps the assessment start
    _fresh()
    gs = GameSession.query.filter_by(
        user_id=u.id, location=ASSESSMENT_KEY, ended_at=None
    ).first()
    assert gs is not None, "GET must server-stamp an assessment start session"
    gs.started_at = datetime.utcnow() - timedelta(seconds=300)   # pretend 5 min elapsed
    db.session.commit()

    client.post(SUBMIT, data=as_correct(8, time_spent_seconds=1))   # forged tiny client time
    _fresh()
    kt = KnowledgeTest.query.filter_by(user_id=u.id).order_by(KnowledgeTest.id.asc()).first()
    assert kt.time_spent_seconds is not None
    assert 290 <= kt.time_spent_seconds <= 360, \
        f"recorded time must be server-measured ~300s, not the forged 1 (got {kt.time_spent_seconds})"
    # the server duration — not the browser value — feeds the run / speed bonus
    run = RunHistory.query.filter_by(user_id=u.id).first()
    assert run.time_spent_seconds == kt.time_spent_seconds
    # the forged client value is retained only as a non-authoritative reference
    assert json.loads(kt.answers_json).get("_client_time_spent_seconds") == 1
    # the timing session was closed on submit
    _fresh()
    assert GameSession.query.filter_by(
        user_id=u.id, location=ASSESSMENT_KEY, ended_at=None
    ).count() == 0


def test_knowledge_test_is_unique_per_user(app, user_factory):
    """M6: knowledge_tests has a DB-level unique index on user_id, so a second row
    for the same user is rejected — a concurrent double-submit can never create two
    KnowledgeTest rows (the losing racer hits IntegrityError)."""
    from sqlalchemy.exc import IntegrityError
    u = user_factory(passed=ALL_LOCATIONS)
    db.session.add(KnowledgeTest(user_id=u.id, answers_json="{}", score=8))
    db.session.commit()
    db.session.add(KnowledgeTest(user_id=u.id, answers_json="{}", score=3))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
    _fresh()
    assert KnowledgeTest.query.filter_by(user_id=u.id).count() == 1, \
        "only ONE KnowledgeTest may exist per user"


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


def test_locked_location_npc_is_refused(client, user_factory, login):
    """L1: a game user cannot pull tutor content for a location they haven't
    unlocked yet — /npc/chat refuses a locked location and logs nothing. (The
    control-user 403 is a separate, earlier gate.)"""
    from app.models import NpcInteraction
    u = user_factory(condition="game")   # only the Library is unlocked
    login(u)
    # the unlocked first location is allowed…
    ok = client.post("/npc/chat", json={"message": "what is narrow AI?", "location": "library"})
    assert ok.status_code != 403
    # …a locked later location is refused
    r = client.post("/npc/chat", json={"message": "what is overfitting?", "location": "observatory"})
    assert r.status_code == 403, "a locked location's tutor content must be refused"
    _fresh()
    assert NpcInteraction.query.filter_by(user_id=u.id, location="observatory").count() == 0, \
        "a refused locked-location chat logs nothing"


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


def test_observatory_high_stars_persist(client, user_factory, login):
    """Regression (audit H1): the Observatory now has 10 constellation stars, so
    star ids star-0..star-9 must ALL be accepted and persisted. Previously a
    hardcoded range(5) silently dropped star-5..star-9, so a learner who lit all
    ten, left, and returned found the last five dark and the Trial gate re-locked.
    The valid-id count is now derived from the Observatory's content (its hooks),
    which is 10. Presentation-progress only (BookRead) — never grading data."""
    from app.game_content import get_hooks
    n_stars = len(get_hooks("observatory"))
    assert n_stars >= 6, "the Observatory should have well more than the old 5 stars"

    u = user_factory()
    login(u)
    # A high star (the 8th) and the very last star must both be accepted + stored.
    last = "star-%d" % (n_stars - 1)
    r7 = client.post("/location/observatory/progress", json={"item": "star-7"})
    r_last = client.post("/location/observatory/progress", json={"item": last})
    assert r7.status_code == 200 and "star-7" in r7.get_json()["explored"]
    assert r_last.status_code == 200 and last in r_last.get_json()["explored"]

    _fresh()
    stored = {b.book_id for b in BookRead.query.filter_by(user_id=u.id, location="observatory").all()}
    assert {"star-7", last} <= stored, "high stars must persist (survive navigation)"

    # A subsequent read (re-entering the location) returns them for the restore loop.
    ids = client.post("/location/observatory/progress", json={"item": "star-0"}).get_json()["explored"]
    assert {"star-0", "star-7", last} <= set(ids), "saved stars are read back for restore"

    # Boundary: an id beyond the real star count is still rejected (never stored).
    client.post("/location/observatory/progress", json={"item": "star-%d" % n_stars})
    client.post("/location/observatory/progress", json={"item": "star-99"})
    _fresh()
    stored2 = {b.book_id for b in BookRead.query.filter_by(user_id=u.id, location="observatory").all()}
    assert "star-99" not in stored2 and ("star-%d" % n_stars) not in stored2, \
        "ids beyond the derived star count are rejected"


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
    """The personal best-runs list shows the Chronicle in the L·C·A·O line.

    Lives on the full leaderboard page (it used to be a slide-in panel on the hub);
    the assertion is unchanged, only the page it is read from."""
    import re
    u = user_factory(passed=ALL_LOCATIONS)
    login(u)
    client.post(SUBMIT, data=as_correct(8))          # records a run
    body = client.get("/leaderboard").get_data(as_text=True)
    assert re.search(r'lb-locs">L\d+ · C\d+ · A\d+ · O\d+', body), \
        "leaderboard breakdown must show all four: L (Library) · C (Chronicle) · A (AI Lab) · O (Observatory)"
