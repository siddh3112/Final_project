"""
The Hallucination Hunt — the Observatory's WHOLE Trial.

All four Observatory Trial rounds are hunt sets: Atlas states four claims and
exactly one is a hallucination (confidently worded but false); catching it scores
the round. Each round is 1 point, graded INDEPENDENTLY through the same shared
server path as every other item (score = count of correct rounds, 3/4 to pass).
These tests verify the behaviour; they never relax grading, the shown-set rule, or
the no-answer-in-DOM guarantee to pass.
"""

import json
import re

import pytest

from app import shuffle_options
from app.game_content import (
    QUIZZES,
    TAUGHT_CONCEPTS,
    TRIAL_COUNT,
    TRIAL_DRAW_ONLY,
    get_questions_by_keys,
    select_trial_questions,
)
from app.models import LocationProgress, QuizAttempt, TrialAttempt, db

# Derived from the bank, so adding/removing a hunt set never desyncs the tests.
HUNT_KEYS = [q["key"] for q in QUIZZES["observatory"] if q.get("hunt")]
RETIRED_MCQ_KEYS = [q["key"] for q in QUIZZES["observatory"] if not q.get("hunt")]


def _fresh():
    db.session.expire_all()


def _unlock_obs(user_factory):
    """A user with the first three locations passed → the Observatory is unlocked."""
    return user_factory(passed=("library", "chronicle", "ai_lab"))


def _start_obs_trial(client):
    """GET the Observatory Trial; return (token, stored_keys, html)."""
    html = client.get("/location/observatory/trial").get_data(as_text=True)
    m = re.search(r'name="attempt_id" value="([^"]+)"', html)
    assert m, "no attempt token rendered for the Observatory Trial"
    token = m.group(1)
    att = TrialAttempt.query.filter_by(token=token).first()
    assert att is not None and att.status == "open"
    return token, json.loads(att.question_keys), html


def _q(key):
    return get_questions_by_keys("observatory", [key])[0]


def _submit_with(client, token, keys, n_correct):
    """Submit the Trial with exactly n_correct rounds caught (the rest a true claim)."""
    data = {"attempt_id": token}
    for i, k in enumerate(keys):
        q = _q(k)
        correct = q["correct"]
        data[k] = correct if i < n_correct else next(l for l in q["options"] if l != correct)
    return client.post("/location/observatory/submit", data=data)


# ── content: enough hunt sets, each well-formed, tagged, inside the taught set ──
def test_hunt_bank_wellformed():
    hunts = [q for q in QUIZZES["observatory"] if q.get("hunt")]
    assert len(hunts) >= 6, "author at least 6 hunt sets so a draw of 4 varies"
    seen = set()
    for q in hunts:
        assert q["key"] not in seen, f"duplicate hunt key {q['key']}"
        seen.add(q["key"])
        assert set(q["options"]) == {"A", "B", "C", "D"}
        assert q["correct"] in q["options"], f"{q['key']}: correct is not an option"
        assert q["concept"] == "hallucination" and q["concept"] in TAUGHT_CONCEPTS
        assert q["false_concept"] in TAUGHT_CONCEPTS, f"{q['key']}: false_concept must be taught"
        # elaborative feedback is the learning payoff on resolve
        assert q["feedback_correct"] and q["feedback_wrong"] and q["explanation"]


def test_bias_nlp_fewshot_now_assessed():
    """The gap this closes: bias, nlp and few_shot_prompting were taught but never
    assessed by a graded item. Now each is the FALSE claim in at least one set."""
    false_concepts = {q["false_concept"] for q in QUIZZES["observatory"] if q.get("hunt")}
    assert {"bias", "nlp", "few_shot_prompting"} <= false_concepts, (
        f"bias/nlp/few_shot must each be a graded false claim; got {sorted(false_concepts)}"
    )
    assert false_concepts <= set(TAUGHT_CONCEPTS), "every false_concept must be taught"


def test_false_statement_letter_varies_across_sets():
    """No cross-set tell: the false claim is not always the same option letter."""
    letters = {_q(k)["correct"] for k in HUNT_KEYS}
    assert len(letters) > 1, "the false claim must not sit at a fixed letter across sets"


def test_false_statement_position_varies():
    """shuffle randomises display order, so the false claim moves between slots
    (no positional tell across repeated renders/attempts)."""
    q = _q(HUNT_KEYS[0])
    positions = {tuple(l for l, _t in shuffle_options(q)).index(q["correct"]) for _ in range(60)}
    assert len(positions) > 1, "shuffle must move the false claim between positions"


# ── composition: the whole Trial is hunts; obs_s* are retired from the draw ──
def test_observatory_draws_only_hunts():
    assert TRIAL_DRAW_ONLY.get("observatory") == "hunt"
    assert RETIRED_MCQ_KEYS, "the plain obs_s* MCQs should still exist in the bank (not deleted)"
    for _ in range(50):
        chosen = select_trial_questions("observatory")
        assert len(chosen) == TRIAL_COUNT
        assert len(set(chosen)) == TRIAL_COUNT, "no repeated round in one Trial"
        assert set(chosen) <= set(HUNT_KEYS), "every drawn round must be a hunt set"
        assert set(chosen).isdisjoint(RETIRED_MCQ_KEYS), "retired obs_s* must never be drawn"


def test_server_varies_the_four_sets():
    seen = set()
    for _ in range(60):
        seen.update(select_trial_questions("observatory"))
    assert len(seen) > TRIAL_COUNT, "the server should vary which hunt sets it serves"


def test_trial_page_draws_four_hunts(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    _token, keys, _html = _start_obs_trial(client)
    assert len(keys) == TRIAL_COUNT
    assert set(keys) <= set(HUNT_KEYS), "all four served rounds are hunts"


# ── grading: independent, 1 point per round, 3/4 to pass (NOT all-or-nothing) ──
def test_four_correct_scores_four(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    r = _submit_with(client, token, keys, 4)
    assert r.status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="observatory").first()
    assert lp.best_score == 4 and lp.passed is True
    assert QuizAttempt.query.filter_by(user_id=u.id, location="observatory").count() == TRIAL_COUNT


def test_three_correct_passes(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    r = _submit_with(client, token, keys, 3)
    assert r.status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="observatory").first()
    assert lp.best_score == 3 and lp.passed is True, "3/4 caught rounds passes"


def test_two_correct_fails_independent_not_all_or_nothing(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    r = _submit_with(client, token, keys, 2)
    assert r.status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="observatory").first()
    # score is the COUNT of caught rounds (2), not 0 — the board is not all-or-nothing.
    assert lp.best_score == 2 and lp.passed is False
    rows = QuizAttempt.query.filter_by(user_id=u.id, location="observatory").all()
    assert sum(1 for x in rows if x.is_correct) == 2, "exactly two rounds scored, graded independently"


def test_catching_false_scores_and_true_misses(client, user_factory, login):
    """Per round: picking the false claim = 1 point; picking a true claim = 0."""
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = keys[0]
    q = _q(hk)
    a_true = next(l for l in q["options"] if l != q["correct"])
    client.post("/location/observatory/submit", data={"attempt_id": token, hk: q["correct"]})
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="observatory", question_key=hk).first()
    assert row.selected_answer == q["correct"] and row.is_correct is True

    # a fresh attempt: pick a TRUE claim → the round is missed
    u2 = _unlock_obs(user_factory)
    login(u2)
    token2, keys2, _ = _start_obs_trial(client)
    hk2 = keys2[0]
    q2 = _q(hk2)
    true2 = next(l for l in q2["options"] if l != q2["correct"])
    client.post("/location/observatory/submit", data={"attempt_id": token2, hk2: true2})
    _fresh()
    row2 = QuizAttempt.query.filter_by(user_id=u2.id, location="observatory", question_key=hk2).first()
    assert row2.selected_answer == true2 and row2.is_correct is False


# ── first-answer lock + elaborative feedback via /answer (no answer key in DOM) ──
def test_first_answer_locks_and_feedback_explains(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = keys[0]
    q = _q(hk)
    correct = q["correct"]
    wrong = next(l for l in q["options"] if l != correct)

    first = client.post(
        "/location/observatory/answer",
        json={"attempt_id": token, "qkey": hk, "letter": wrong},
    ).get_json()
    retry = client.post(
        "/location/observatory/answer",
        json={"attempt_id": token, "qkey": hk, "letter": correct},
    ).get_json()

    assert first["is_correct"] is False
    assert first["feedback"], "resolve must return elaborative feedback"
    assert retry["committed"] == wrong, "first commit is locked; a retry cannot switch it"

    client.post("/location/observatory/submit", data={"attempt_id": token})
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="observatory", question_key=hk).first()
    assert row.selected_answer == wrong and row.is_correct is False


def test_correct_catch_returns_the_why(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = keys[0]
    q = _q(hk)
    resp = client.post(
        "/location/observatory/answer",
        json={"attempt_id": token, "qkey": hk, "letter": q["correct"]},
    ).get_json()
    assert resp["is_correct"] is True
    assert resp["feedback"] == q["feedback_correct"], "the WHY must be delivered on a catch"


# ── forged submissions are rejected, not scored ──
def test_forged_letter_is_rejected(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    r = client.post(
        "/location/observatory/answer",
        json={"attempt_id": token, "qkey": keys[0], "letter": "Z"},  # not an option for this round
    )
    assert r.status_code == 400


def test_forged_offround_hunt_is_rejected(client, user_factory, login):
    """A claim id for a hunt set NOT served this attempt is rejected, not scored."""
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    other = next((k for k in HUNT_KEYS if k not in keys), None)
    assert other is not None, "with 8 sets and a draw of 4, some hunt is always off-attempt"
    r = client.post(
        "/location/observatory/answer",
        json={"attempt_id": token, "qkey": other, "letter": "A"},
    )
    assert r.status_code == 400, "an off-attempt hunt set must be rejected"


def test_forged_form_value_is_not_scored(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = keys[0]
    r = client.post("/location/observatory/submit", data={"attempt_id": token, hk: "Z"})
    assert r.status_code == 200
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="observatory", question_key=hk).first()
    assert row.selected_answer is None and row.is_correct is False, "a forged letter is unanswered, not a point"


# ── no truth data in the DOM for any round ──
def test_no_truth_data_in_dom(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    _token, keys, html = _start_obs_trial(client)
    for hk in keys:
        q = _q(hk)
        # the four claims themselves ARE shown (the learner must read them)…
        for text in q["options"].values():
            assert text in html
        # …but nothing reveals WHICH is false, for any round.
        assert q["explanation"] not in html
        assert q["feedback_correct"] not in html
        assert q["feedback_wrong"] not in html
    assert "data-correct" not in html
    assert "data-false" not in html
    assert "data-answer" not in html
    assert 'name="shown_keys"' not in html
    # every round is a hunt, so NO A/B/C/D letter label is rendered anywhere in the
    # quiz (that markup only exists on plain MCQs, which are retired from this Trial).
    quiz_block = re.search(r'id="quiz-questions".*?</form>', html, re.S)
    assert quiz_block is not None
    assert "q-option-letter" not in quiz_block.group(0), "no A/B/C/D positional tell in any round"
