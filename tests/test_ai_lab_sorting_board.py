"""
The Classification Board — the AI Lab's whole Trial is one drag-and-drop sorting
task. The server draws 4 data objects; the learner sorts each into a bin; each
correct placement is 1 point, graded INDEPENDENTLY through the shared core (score
= count correct, 3/4 to pass). These tests verify the behaviour; they never relax
grading, independence, or the correct-bin-not-in-DOM guarantee to pass.
"""

import json
import re

import pytest

from app.game_content import (
    BIN_IDS,
    DATA_BINS,
    PINNED_QUESTIONS,
    QUIZZES,
    TAUGHT_CONCEPTS,
    TRIAL_COUNT,
    get_questions_by_keys,
    grade_quiz,
    select_trial_questions,
)
from app.models import LocationProgress, QuizAttempt, TrialAttempt, db


def _fresh():
    db.session.expire_all()


def _unlock_lab(user_factory):
    """Library + Chronicle passed → the AI Lab is unlocked."""
    return user_factory(passed=("library", "chronicle"))


def _q(key):
    return get_questions_by_keys("ai_lab", [key])[0]


def _start_board(client):
    html = client.get("/location/ai_lab").get_data(as_text=True)
    m = re.search(r'name="attempt_id" value="([^"]+)"', html)
    assert m, "no attempt token rendered for the AI Lab terminal"
    token = m.group(1)
    att = TrialAttempt.query.filter_by(token=token).first()
    assert att is not None and att.status == "open"
    return token, json.loads(att.question_keys), html


def _wrong_bin(correct):
    return next(b for b in BIN_IDS if b != correct)


# ── content: enough unambiguous sort objects, all in the taught set ──
def test_board_bank_is_sort_objects():
    bank = QUIZZES["ai_lab"]
    assert all(q.get("kind") == "sort" for q in bank), "the AI Lab bank is all sorting objects"
    assert len(bank) >= 8, "author ~8-10+ so the 4-object draw varies"
    for q in bank:
        assert q["correct"] in BIN_IDS, f"{q['key']}: correct must be a real bin"
        assert q["concept"] in TAUGHT_CONCEPTS
        assert q["feedback_correct"] and q["feedback_wrong"] and q["explanation"]


def test_every_bin_is_represented():
    covered = {q["correct"] for q in QUIZZES["ai_lab"]}
    assert covered == BIN_IDS, "objects should span all four bins (structured/semi/unstructured/dark)"


def test_ai_lab_no_longer_pinned():
    assert "ai_lab" not in PINNED_QUESTIONS


# ── selection: draws 4 distinct sort objects ──
def test_draw_is_four_sort_objects():
    for _ in range(30):
        keys = select_trial_questions("ai_lab")
        assert len(keys) == TRIAL_COUNT and len(set(keys)) == TRIAL_COUNT
        assert all(_q(k).get("kind") == "sort" for k in keys)


# ── shared grading core: each object graded independently, 1 point each ──
def test_grade_quiz_scores_each_object_independently():
    keys = select_trial_questions("ai_lab")
    qs = get_questions_by_keys("ai_lab", keys)
    # all correct → 4
    allc = {q["key"]: q["correct"] for q in qs}
    _r, s4, _t, p4 = grade_quiz("ai_lab", allc, shown_keys=keys)
    assert s4 == 4 and p4 is True
    # exactly 3 correct → 3, passes
    three = dict(allc)
    three[qs[0]["key"]] = _wrong_bin(qs[0]["correct"])
    _r, s3, _t, p3 = grade_quiz("ai_lab", three, shown_keys=keys)
    assert s3 == 3 and p3 is True
    # exactly 2 correct → 2, fails (independence: not all-or-nothing)
    two = dict(allc)
    two[qs[0]["key"]] = _wrong_bin(qs[0]["correct"])
    two[qs[1]["key"]] = _wrong_bin(qs[1]["correct"])
    _r, s2, _t, p2 = grade_quiz("ai_lab", two, shown_keys=keys)
    assert s2 == 2 and p2 is False


# ── integration: a fully correct board scores 4 and passes ──
def test_correct_board_scores_four(client, user_factory, login):
    u = _unlock_lab(user_factory)
    login(u)
    token, keys, _ = _start_board(client)
    data = {"attempt_id": token}
    for k in keys:
        data[k] = _q(k)["correct"]
    r = client.post("/location/ai_lab/submit", data=data)
    assert r.status_code == 200
    _fresh()
    rows = QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab").all()
    assert len(rows) == TRIAL_COUNT and all(a.is_correct for a in rows)
    lp = LocationProgress.query.filter_by(user_id=u.id, location="ai_lab").first()
    assert lp.passed is True and lp.best_score == 4
    # each object's chosen bin is logged
    for k in keys:
        row = next(a for a in rows if a.question_key == k)
        assert row.selected_answer == _q(k)["correct"]


def test_three_correct_passes_two_fails(client, user_factory, login):
    # three correct → pass 3/4
    u = _unlock_lab(user_factory)
    login(u)
    token, keys, _ = _start_board(client)
    data = {"attempt_id": token}
    for i, k in enumerate(keys):
        c = _q(k)["correct"]
        data[k] = c if i < 3 else _wrong_bin(c)
    client.post("/location/ai_lab/submit", data=data)
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="ai_lab").first()
    assert lp.passed is True and lp.best_score == 3

    # a fresh attempt: two correct → fail 2/4
    u2 = _unlock_lab(user_factory)
    login(u2)
    token2, keys2, _ = _start_board(client)
    data2 = {"attempt_id": token2}
    for i, k in enumerate(keys2):
        c = _q(k)["correct"]
        data2[k] = c if i < 2 else _wrong_bin(c)
    client.post("/location/ai_lab/submit", data=data2)
    _fresh()
    lp2 = LocationProgress.query.filter_by(user_id=u2.id, location="ai_lab").first()
    assert lp2.passed is False and lp2.best_score == 2


# ── forged / malformed submissions cannot score ──
def test_unknown_bin_is_not_scored(client, user_factory, login):
    u = _unlock_lab(user_factory)
    login(u)
    token, keys, _ = _start_board(client)
    data = {"attempt_id": token}
    for k in keys:
        data[k] = _q(k)["correct"]
    data[keys[0]] = "not_a_bin"          # forged bin
    client.post("/location/ai_lab/submit", data=data)
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab", question_key=keys[0]).first()
    assert row.selected_answer is None and row.is_correct is False, "an unknown bin is unplaced, not a point"


def test_unknown_object_id_is_ignored(client, user_factory, login):
    u = _unlock_lab(user_factory)
    login(u)
    token, keys, _ = _start_board(client)
    data = {"attempt_id": token, "lab_o99": "structured"}   # object not in this attempt
    for k in keys:
        data[k] = _q(k)["correct"]
    client.post("/location/ai_lab/submit", data=data)
    _fresh()
    rows = QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab").all()
    assert len(rows) == TRIAL_COUNT, "only the 4 served objects are graded/logged"
    assert all(a.question_key in keys for a in rows), "a forged object id creates no row"


def test_missing_object_scores_wrong(client, user_factory, login):
    u = _unlock_lab(user_factory)
    login(u)
    token, keys, _ = _start_board(client)
    data = {"attempt_id": token}
    for k in keys[1:]:                    # omit the first object entirely
        data[k] = _q(k)["correct"]
    client.post("/location/ai_lab/submit", data=data)
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab", question_key=keys[0]).first()
    assert row.selected_answer is None and row.is_correct is False


def test_sort_item_cannot_be_committed_via_answer(client, user_factory, login):
    u = _unlock_lab(user_factory)
    login(u)
    token, keys, _ = _start_board(client)
    r = client.post(
        "/location/ai_lab/answer",
        json={"attempt_id": token, "qkey": keys[0], "letter": "A"},
    )
    assert r.status_code == 400, "the board commits at submit, not via /answer"


# ── no correct-bin data in the Trial page DOM ──
def test_no_correct_bin_in_dom(client, user_factory, login):
    u = _unlock_lab(user_factory)
    login(u)
    _token, keys, html = _start_board(client)
    # the object labels ARE shown; the bins ARE shown (drop targets)…
    for k in keys:
        assert _q(k)["question"] in html
    # …but nothing maps an object to its correct bin.
    assert "data-correct" not in html
    assert "data-correctval" not in html
    # the object cards carry no data-bin (that would leak the answer)
    board = re.search(r'id="sort-board".*?</section>', html, re.S)
    assert board is not None
    objs = re.search(r'id="intake-items".*?</div>\s*</div>', html, re.S)
    if objs:
        assert "data-bin" not in objs.group(0), "object cards must not carry their bin"
