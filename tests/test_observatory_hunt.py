"""
The Hallucination Hunt — the Observatory's signature pinned Trial item.

Atlas states four claims; exactly one is a hallucination (confidently worded but
false). It slots into the EXISTING Trial as 1 of 4 items, 1 point, all-or-nothing,
graded server-side through the same path as every other item. These tests verify
the behaviour; they never relax grading, the pin, the shown-set rule, or the
no-answer-in-DOM guarantee to pass.
"""

import json
import re

import pytest

from app import shuffle_options
from app.game_content import (
    PINNED_QUESTIONS,
    QUIZZES,
    TAUGHT_CONCEPTS,
    TRIAL_COUNT,
    get_questions_by_keys,
    select_trial_questions,
)
from app.models import LocationProgress, QuizAttempt, TrialAttempt, db

HUNT_KEYS = ["obs_hunt1", "obs_hunt2", "obs_hunt3"]


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


def _hunt_key(keys):
    hunts = [k for k in keys if k in HUNT_KEYS]
    assert len(hunts) == 1, f"exactly one hunt set must be served, got {hunts}"
    return hunts[0]


# ── content: three sets exist, well-formed, concept-tagged, inside taught set ──
def test_hunt_sets_authored_and_tagged():
    hunts = [q for q in QUIZZES["observatory"] if q.get("hunt")]
    assert {q["key"] for q in hunts} == set(HUNT_KEYS), "three hunt sets expected"
    for q in hunts:
        assert set(q["options"]) == {"A", "B", "C", "D"}
        assert q["correct"] in q["options"]
        assert q["concept"] in TAUGHT_CONCEPTS, "hunt concept must be a taught concept"
        assert q["concept"] == "hallucination"
        # elaborative feedback for the learning payoff on resolve
        assert q["feedback_correct"] and q["feedback_wrong"] and q["explanation"]


def test_false_statement_letter_varies_across_sets():
    """No cross-set tell: the false claim is not always the same option letter."""
    letters = {_q(k)["correct"] for k in HUNT_KEYS}
    assert len(letters) > 1, "the false statement must not sit at a fixed letter across sets"


# ── pinning + selection: hunt leads, group excluded from the remainder ──
def test_hunt_is_pinned_group_and_leads():
    assert PINNED_QUESTIONS["observatory"] == [HUNT_KEYS]
    for _ in range(40):
        chosen = select_trial_questions("observatory")
        assert len(chosen) == TRIAL_COUNT
        assert chosen[0] in HUNT_KEYS, "a hunt set must lead every Observatory Trial"
        assert len([k for k in chosen if k in HUNT_KEYS]) == 1, "only ONE hunt set is drawn"


def test_server_picks_varying_sets():
    picked = {select_trial_questions("observatory")[0] for _ in range(60)}
    assert picked <= set(HUNT_KEYS)
    assert len(picked) > 1, "the server should vary which hunt set it serves"


# ── shuffle: the false statement does not always occupy the same position ──
def test_false_statement_position_varies():
    q = _q("obs_hunt1")
    positions = set()
    for _ in range(60):
        order = [letter for letter, _text in shuffle_options(q)]
        positions.add(order.index(q["correct"]))
    assert len(positions) > 1, "shuffle must move the false statement between positions"


# ── the Trial still draws 4, hunt pinned, passes at 3/4 ──
def test_observatory_trial_four_items_hunt_pinned(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    _token, keys, _html = _start_obs_trial(client)
    assert len(keys) == TRIAL_COUNT
    assert keys[0] in HUNT_KEYS
    assert set(keys[1:]).isdisjoint(HUNT_KEYS), "the other 3 items are normal obs questions"


def test_three_of_four_passes_with_hunt(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    data = {"attempt_id": token}
    for i, k in enumerate(keys):
        q = _q(k)
        correct = q["correct"]
        data[k] = correct if i < 3 else next(l for l in q["options"] if l != correct)
    r = client.post("/location/observatory/submit", data=data)
    assert r.status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="observatory").first()
    assert lp.passed is True and lp.best_score == 3
    assert QuizAttempt.query.filter_by(user_id=u.id, location="observatory").count() == TRIAL_COUNT


# ── grading: catching the false claim = 1 point; a true claim = 0 ──
def test_picking_false_statement_scores_the_item(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = _hunt_key(keys)
    correct = _q(hk)["correct"]
    data = {"attempt_id": token, hk: correct}
    r = client.post("/location/observatory/submit", data=data)
    assert r.status_code == 200
    _fresh()
    row = QuizAttempt.query.filter_by(
        user_id=u.id, location="observatory", question_key=hk
    ).first()
    assert row.selected_answer == correct and row.is_correct is True


def test_picking_true_statement_misses_the_item(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = _hunt_key(keys)
    q = _q(hk)
    a_true = next(l for l in q["options"] if l != q["correct"])  # a TRUE statement
    r = client.post("/location/observatory/submit", data={"attempt_id": token, hk: a_true})
    assert r.status_code == 200
    _fresh()
    row = QuizAttempt.query.filter_by(
        user_id=u.id, location="observatory", question_key=hk
    ).first()
    assert row.selected_answer == a_true and row.is_correct is False


# ── first-answer lock + elaborative feedback via /answer (no answer key in DOM) ──
def test_hunt_first_answer_locks_and_feedback_explains(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = _hunt_key(keys)
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
    row = QuizAttempt.query.filter_by(
        user_id=u.id, location="observatory", question_key=hk
    ).first()
    assert row.selected_answer == wrong and row.is_correct is False


def test_correct_catch_returns_the_why(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = _hunt_key(keys)
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
    hk = _hunt_key(keys)
    r = client.post(
        "/location/observatory/answer",
        json={"attempt_id": token, "qkey": hk, "letter": "Z"},  # not an option
    )
    assert r.status_code == 400


def test_forged_offattempt_hunt_id_is_rejected(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = _hunt_key(keys)
    other = next(k for k in HUNT_KEYS if k != hk)  # a hunt set NOT served this attempt
    r = client.post(
        "/location/observatory/answer",
        json={"attempt_id": token, "qkey": other, "letter": "A"},
    )
    assert r.status_code == 400, "an off-attempt hunt set must be rejected"


def test_forged_form_value_is_not_scored(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    token, keys, _ = _start_obs_trial(client)
    hk = _hunt_key(keys)
    r = client.post("/location/observatory/submit", data={"attempt_id": token, hk: "Z"})
    assert r.status_code == 200
    _fresh()
    row = QuizAttempt.query.filter_by(
        user_id=u.id, location="observatory", question_key=hk
    ).first()
    assert row.selected_answer is None and row.is_correct is False, "a forged letter is unanswered, not a point"


# ── the false statement's identity is NOT in the Trial DOM ──
def test_false_statement_identity_absent_from_dom(client, user_factory, login):
    u = _unlock_obs(user_factory)
    login(u)
    _token, keys, html = _start_obs_trial(client)
    hk = _hunt_key(keys)
    q = _q(hk)
    # the four claims themselves ARE shown (the learner must read them)…
    for text in q["options"].values():
        assert text in html
    # …but nothing in the page reveals WHICH is false.
    assert q["explanation"] not in html
    assert q["feedback_correct"] not in html
    assert q["feedback_wrong"] not in html
    assert "data-correct" not in html
    assert "data-false" not in html
    assert "data-answer" not in html
    assert 'name="shown_keys"' not in html
    # no per-claim letter label rendered inside the hunt block (no A/B/C/D tell).
    # The hunt-claims container holds only <label>/<span>, so the first </div>
    # after it is its own close — safe to scope the check to that slice.
    block = re.search(r'hunt-claims".*?</div>', html, re.S)
    assert block is not None, "the hunt claims block should render"
    assert "q-option-letter" not in block.group(0)
