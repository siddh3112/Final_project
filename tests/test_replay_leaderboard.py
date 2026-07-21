"""
Replay runs + the cross-player leaderboard.

The non-negotiable these tests exist to protect: a replay is a GAMIFIED second
playthrough and must never touch the research measure. Run 1's KnowledgeTest is
written once and frozen; replays add RunHistory rows only.
"""

import json

from app.eval_content import POST_TEST
from app.models import KnowledgeTest, LocationProgress, QuizAttempt, RunHistory, User, db
from app.services.leaderboard import best_runs, score_of
from app.game_content import LOCATION_ORDER

SUBMIT = "/eval/post-test/submit"
ALL = tuple(LOCATION_ORDER)


def _fresh():
    db.session.expire_all()


def _finish_run(client, as_correct, n):
    """Play the post-test for the current run with n correct answers."""
    return client.post(SUBMIT, data=as_correct(n))


def _relock_and_repass(user):
    """Simulate re-clearing all four locations in the new run (so the post-test
    unlocks again) without going through every Trial in the test."""
    for lp in LocationProgress.query.filter_by(user_id=user.id).all():
        lp.passed = True
        lp.best_score = 4
    db.session.commit()


# ──────────────────────────────────────────────────────────────────────
# 1. A replay creates a NEW run and does NOT touch the research record
# ──────────────────────────────────────────────────────────────────────

def test_replay_never_creates_or_alters_the_research_knowledge_test(
    client, user_factory, login, as_correct
):
    u = user_factory(passed=ALL)
    login(u)
    _finish_run(client, as_correct, 8)          # run 1: the measured attempt
    _fresh()

    kt_rows = KnowledgeTest.query.filter_by(user_id=u.id).all()
    assert len(kt_rows) == 1
    research_score = kt_rows[0].score
    research_id = kt_rows[0].id
    research_answers = kt_rows[0].answers_json
    assert research_score == 8

    # Start a new run and play it with a DIFFERENT score.
    assert client.post("/replay").status_code in (302, 200)
    _fresh()
    u = db.session.get(User, u.id)
    assert u.current_run == 2

    _relock_and_repass(u)
    _finish_run(client, as_correct, 10)         # replay run scores higher
    _fresh()

    # THE NON-NEGOTIABLE: still exactly one research record, unchanged.
    kt_after = KnowledgeTest.query.filter_by(user_id=u.id).all()
    assert len(kt_after) == 1, "a replay must never create a second KnowledgeTest"
    assert kt_after[0].id == research_id, "the research row was replaced"
    assert kt_after[0].score == research_score, "the research value was overwritten"
    assert kt_after[0].answers_json == research_answers

    # But the replay DID produce its own gamified run.
    runs = RunHistory.query.filter_by(user_id=u.id).order_by(RunHistory.id.asc()).all()
    assert len(runs) == 2
    assert [r.run_number for r in runs] == [1, 2]
    assert runs[1].post_test_score == 10


# ──────────────────────────────────────────────────────────────────────
# 2. Better replay raises the best; worse replay never lowers it
# ──────────────────────────────────────────────────────────────────────

def test_better_replay_raises_best_and_worse_replay_does_not_lower(
    client, user_factory, login, as_correct
):
    u = user_factory(passed=ALL)
    login(u)
    _finish_run(client, as_correct, 6)
    _fresh()
    best_1 = best_runs(current_user_id=u.id)[0]["score"]

    # A BETTER run raises the standing.
    client.post("/replay"); _fresh()
    _relock_and_repass(db.session.get(User, u.id))
    _finish_run(client, as_correct, 10)
    _fresh()
    best_2 = best_runs(current_user_id=u.id)[0]["score"]
    assert best_2 > best_1, "a better full run should raise the leaderboard best"

    # A WORSE run must not lower it.
    client.post("/replay"); _fresh()
    _relock_and_repass(db.session.get(User, u.id))
    _finish_run(client, as_correct, 2)
    _fresh()
    best_3 = best_runs(current_user_id=u.id)[0]["score"]
    assert best_3 == best_2, "a worse replay must never lower the standing"
    assert RunHistory.query.filter_by(user_id=u.id).count() == 3


# ──────────────────────────────────────────────────────────────────────
# 3. A run only scores when the WHOLE game is completed
# ──────────────────────────────────────────────────────────────────────

def test_partial_redo_does_not_score(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL)
    login(u)
    _finish_run(client, as_correct, 9)
    _fresh()
    assert RunHistory.query.filter_by(user_id=u.id).count() == 1

    client.post("/replay"); _fresh()
    u = db.session.get(User, u.id)

    # All four are re-locked, so the post-test is refused.
    assert all(not lp.passed for lp in LocationProgress.query.filter_by(user_id=u.id))
    r = client.post(SUBMIT, data=as_correct(10))
    assert r.status_code in (302, 200)
    _fresh()
    assert RunHistory.query.filter_by(user_id=u.id).count() == 1, \
        "a partial re-do must not produce a run score"

    # Re-passing only ONE location is still not enough.
    lp = LocationProgress.query.filter_by(user_id=u.id, location=ALL[0]).first()
    lp.passed = True
    db.session.commit()
    client.post(SUBMIT, data=as_correct(10))
    _fresh()
    assert RunHistory.query.filter_by(user_id=u.id).count() == 1


# ──────────────────────────────────────────────────────────────────────
# 4. Cross-player board: many users, each once, ranked by best run
# ──────────────────────────────────────────────────────────────────────

def test_board_ranks_multiple_players_by_best_run_anonymously(
    client, user_factory, login, as_correct
):
    scores = {}
    users = []
    for n in (5, 9, 7):
        u = user_factory(passed=ALL)
        login(u)
        _finish_run(client, as_correct, n)
        _fresh()
        users.append(u)
        scores[u.id] = n

    board = best_runs()
    assert len(board) == 3, "one row per player"
    assert [e["rank"] for e in board] == [1, 2, 3]
    # Ranked high to low.
    assert board[0]["score"] >= board[1]["score"] >= board[2]["score"]
    # The 9/10 player tops the board.
    top_user = max(scores, key=lambda uid: scores[uid])
    assert board[0]["user_id"] == top_user

    # PRIVACY: every row carries a real anonymised handle (not a placeholder),
    # and no username or email appears anywhere on the board.
    blob = json.dumps(board)
    for e in board:
        assert e["handle"], "every board row needs a handle"
        assert e["handle"] != "Unknown Explorer", "handle should be backfilled, not a placeholder"
    for u in users:
        assert u.username not in blob, "usernames must never appear on the board"
        assert u.email not in blob
        assert u.display_handle and u.username not in u.display_handle, \
            "the handle must not be derived from the username"


def test_a_players_extra_runs_do_not_add_extra_board_rows(
    client, user_factory, login, as_correct
):
    u = user_factory(passed=ALL)
    login(u)
    _finish_run(client, as_correct, 6)
    _fresh()
    client.post("/replay"); _fresh()
    _relock_and_repass(db.session.get(User, u.id))
    _finish_run(client, as_correct, 8)
    _fresh()

    board = best_runs()
    assert len([e for e in board if e["user_id"] == u.id]) == 1, "a player appears once"
    row = next(e for e in board if e["user_id"] == u.id)
    assert row["total_runs"] == 2
    assert row["run_number"] == 2, "the board shows their BEST run"


# ──────────────────────────────────────────────────────────────────────
# 5. The single-attempt research gate still holds within a run
# ──────────────────────────────────────────────────────────────────────

def test_single_attempt_research_gate_still_holds(client, user_factory, login, as_correct):
    u = user_factory(passed=ALL)
    login(u)
    _finish_run(client, as_correct, 7)
    _finish_run(client, as_correct, 10)   # rejected: run 1 is closed
    _fresh()
    kts = KnowledgeTest.query.filter_by(user_id=u.id).all()
    assert len(kts) == 1
    assert kts[0].score == 7, "the first attempt stays authoritative"
    assert RunHistory.query.filter_by(user_id=u.id).count() == 1


def test_replay_preserves_history_and_keeps_attempts_monotonic(
    client, user_factory, login, as_correct
):
    """A replay re-locks without deleting anything, and attempts_count is NOT
    reset, so QuizAttempt.attempt_number keeps its research sequence."""
    u = user_factory(passed=ALL)
    login(u)
    # Give a location a couple of recorded attempts.
    lp = LocationProgress.query.filter_by(user_id=u.id, location=ALL[0]).first()
    lp.attempts_count = 3
    db.session.commit()
    _finish_run(client, as_correct, 8)
    _fresh()

    client.post("/replay"); _fresh()
    u = db.session.get(User, u.id)

    lp = LocationProgress.query.filter_by(user_id=u.id, location=ALL[0]).first()
    assert lp.passed is False, "locations re-locked for the new run"
    assert lp.best_score == 0
    assert lp.run == 2, "progress row stamped with the new run"
    assert lp.attempts_count == 3, "attempts_count must stay monotonic (not reset)"

    # Past run + research record preserved.
    assert RunHistory.query.filter_by(user_id=u.id, run_number=1).count() == 1
    assert KnowledgeTest.query.filter_by(user_id=u.id).count() == 1


def test_replay_refused_mid_run(client, user_factory, login):
    """You cannot bail out of an unfinished run to dodge a score."""
    u = user_factory(passed=ALL)
    login(u)
    assert RunHistory.query.filter_by(user_id=u.id).count() == 0
    client.post("/replay")
    _fresh()
    assert db.session.get(User, u.id).current_run == 1, "no new run while one is unfinished"
