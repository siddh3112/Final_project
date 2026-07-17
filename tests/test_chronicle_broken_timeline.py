"""
The Broken Timeline — the Chronicle's signature ORDERING items.

The learner repairs a scrambled sequence of events. Two ordering items are pinned
into the Chronicle Trial (2 ordering + 2 MCQ), each 1 point, all-or-nothing,
graded server-side through the SAME core as every other item. These tests verify
the behaviour; they never relax grading, the pin, the whole-sequence rule, or the
correct-order-not-in-DOM guarantee to pass.
"""

import json
import re

import pytest

from app.game_content import (
    PINNED_QUESTIONS,
    QUIZZES,
    TAUGHT_CONCEPTS,
    TRIAL_COUNT,
    get_questions_by_keys,
    grade_quiz,
    order_canonical,
    select_trial_questions,
)
from app.models import LocationProgress, QuizAttempt, TrialAttempt, db

ORDER_KEYS = ["chr_order_eras", "chr_order_winter"]


def _fresh():
    db.session.expire_all()


def _unlock_chr(user_factory):
    """A user who has passed the Library → the Chronicle is unlocked."""
    return user_factory(passed=("library",))


def _q(key):
    return get_questions_by_keys("chronicle", [key])[0]


def _start_chr_trial(client):
    html = client.get("/location/chronicle/trial").get_data(as_text=True)
    m = re.search(r'name="attempt_id" value="([^"]+)"', html)
    assert m, "no attempt token rendered for the Chronicle Trial"
    token = m.group(1)
    att = TrialAttempt.query.filter_by(token=token).first()
    assert att is not None and att.status == "open"
    return token, json.loads(att.question_keys), html


def _reversed(seq):
    return ",".join(reversed(seq.split(",")))


# ── content: two ordering items, pinned, well-formed, concept-tagged ──
def test_order_items_authored_and_tagged():
    orders = [q for q in QUIZZES["chronicle"] if q.get("kind") == "order"]
    assert {q["key"] for q in orders} == set(ORDER_KEYS)
    for q in orders:
        evs = q["events"]
        assert len(evs) >= 4, "an ordering item should sequence several events"
        assert len({e["id"] for e in evs}) == len(evs), "event ids must be unique"
        assert q["concept"] in TAUGHT_CONCEPTS, "order concept must be taught"
        assert q["feedback_correct"] and q["feedback_wrong"] and q["explanation"]


def test_event_ids_do_not_encode_the_order():
    """Ids must be semantic, not ordinal (ev_1, ev_2…), so the DOM can't be sorted
    into the answer by id."""
    for k in ORDER_KEYS:
        ids = [e["id"] for e in _q(k)["events"]]
        assert not any(re.search(r"\d", i) for i in ids), f"{k}: ids must not carry position numbers"


# ── pinning + selection: both ordering items lead, 2 MCQs fill the rest ──
def test_both_order_items_pinned_first():
    assert PINNED_QUESTIONS["chronicle"] == ORDER_KEYS
    for _ in range(40):
        chosen = select_trial_questions("chronicle")
        assert len(chosen) == TRIAL_COUNT
        assert set(chosen[:2]) == set(ORDER_KEYS), "both ordering items lead every Chronicle Trial"
        rest = chosen[2:]
        assert len(rest) == 2 and all(not k.startswith("chr_order") for k in rest), "the other 2 are MCQs"


# ── shared grading core: correct whole sequence = 1, anything else = 0 ──
def test_grade_quiz_scores_order_all_or_nothing():
    q = _q("chr_order_eras")
    correct = order_canonical(q)
    _r, s_ok, _t, _p = grade_quiz("chronicle", {q["key"]: correct}, shown_keys=[q["key"]])
    assert s_ok == 1
    _r, s_rev, _t, _p = grade_quiz("chronicle", {q["key"]: _reversed(correct)}, shown_keys=[q["key"]])
    assert s_rev == 0, "a wrong order scores nothing (no partial credit)"
    # a single swap is still wrong (whole-sequence rule)
    ids = correct.split(",")
    ids[0], ids[1] = ids[1], ids[0]
    _r, s_swap, _t, _p = grade_quiz("chronicle", {q["key"]: ",".join(ids)}, shown_keys=[q["key"]])
    assert s_swap == 0


# ── integration: correct sequence scores the item; wrong does not ──
def test_correct_sequence_scores_the_item(client, user_factory, login):
    u = _unlock_chr(user_factory)
    login(u)
    token, keys, _ = _start_chr_trial(client)
    data = {"attempt_id": token}
    for k in keys:
        q = _q(k)
        data[k] = order_canonical(q) if q.get("kind") == "order" else q["correct"]
    r = client.post("/location/chronicle/submit", data=data)
    assert r.status_code == 200
    _fresh()
    for k in [k for k in keys if k.startswith("chr_order")]:
        row = QuizAttempt.query.filter_by(user_id=u.id, location="chronicle", question_key=k).first()
        assert row.is_correct is True
        assert row.selected_answer == order_canonical(_q(k))


def test_wrong_sequence_misses_the_item(client, user_factory, login):
    u = _unlock_chr(user_factory)
    login(u)
    token, keys, _ = _start_chr_trial(client)
    ok = next(k for k in keys if k.startswith("chr_order"))
    r = client.post(
        "/location/chronicle/submit",
        data={"attempt_id": token, ok: _reversed(order_canonical(_q(ok)))},
    )
    assert r.status_code == 200
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="chronicle", question_key=ok).first()
    assert row.is_correct is False


# ── the Trial still draws 4 with both ordering items pinned, passes at 3/4 ──
def test_trial_four_items_two_order_two_mcq(client, user_factory, login):
    u = _unlock_chr(user_factory)
    login(u)
    _token, keys, _ = _start_chr_trial(client)
    assert len(keys) == TRIAL_COUNT
    assert set(keys[:2]) == set(ORDER_KEYS)
    assert sum(1 for k in keys if k.startswith("chr_order")) == 2


def test_three_of_four_passes(client, user_factory, login):
    u = _unlock_chr(user_factory)
    login(u)
    token, keys, _ = _start_chr_trial(client)
    data = {"attempt_id": token}
    mcq_i = 0
    for k in keys:
        q = _q(k)
        if q.get("kind") == "order":
            data[k] = order_canonical(q)                 # both ordering items correct
        else:
            mcq_i += 1
            data[k] = q["correct"] if mcq_i == 1 else next(l for l in q["options"] if l != q["correct"])
    r = client.post("/location/chronicle/submit", data=data)
    assert r.status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="chronicle").first()
    assert lp.passed is True and lp.best_score == 3
    assert QuizAttempt.query.filter_by(user_id=u.id, location="chronicle").count() == TRIAL_COUNT


# ── first-answer lock + elaborative feedback via /answer ──
def test_order_first_answer_locks_and_feedback(client, user_factory, login):
    u = _unlock_chr(user_factory)
    login(u)
    token, keys, _ = _start_chr_trial(client)
    ok = next(k for k in keys if k.startswith("chr_order"))
    correct = order_canonical(_q(ok))
    wrong = _reversed(correct)

    first = client.post(
        "/location/chronicle/answer",
        json={"attempt_id": token, "qkey": ok, "order": wrong},
    ).get_json()
    retry = client.post(
        "/location/chronicle/answer",
        json={"attempt_id": token, "qkey": ok, "order": correct},
    ).get_json()

    assert first["is_correct"] is False
    assert first["feedback"], "resolve returns elaborative feedback"
    assert retry["committed"] == wrong, "the first committed order is locked"

    client.post("/location/chronicle/submit", data={"attempt_id": token})
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="chronicle", question_key=ok).first()
    assert row.selected_answer == wrong and row.is_correct is False


# ── forged / malformed sequences are rejected, not scored ──
@pytest.mark.parametrize("bad", ["duplicate", "extra", "missing"])
def test_malformed_sequence_rejected_at_commit(client, user_factory, login, bad):
    u = _unlock_chr(user_factory)
    login(u)
    token, keys, _ = _start_chr_trial(client)
    ok = next(k for k in keys if k.startswith("chr_order"))
    ids = [e["id"] for e in _q(ok)["events"]]
    if bad == "duplicate":
        forged = ",".join([ids[0]] * len(ids))
    elif bad == "extra":
        forged = ",".join(ids + ["ev_bogus"])
    else:
        forged = ",".join(ids[:-1])
    r = client.post(
        "/location/chronicle/answer",
        json={"attempt_id": token, "qkey": ok, "order": forged},
    )
    assert r.status_code == 400, f"a {bad} sequence must be rejected at commit"


def test_malformed_form_value_is_not_scored(client, user_factory, login):
    u = _unlock_chr(user_factory)
    login(u)
    token, keys, _ = _start_chr_trial(client)
    ok = next(k for k in keys if k.startswith("chr_order"))
    r = client.post(
        "/location/chronicle/submit",
        data={"attempt_id": token, ok: "ev_bogus,ev_bogus"},  # malformed
    )
    assert r.status_code == 200
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="chronicle", question_key=ok).first()
    assert row.selected_answer is None and row.is_correct is False, "a malformed order is unanswered, not a point"


# ── the correct sequence is NOT in the Trial page DOM ──
def test_correct_sequence_absent_from_dom(client, user_factory, login):
    u = _unlock_chr(user_factory)
    login(u)
    _token, keys, html = _start_chr_trial(client)
    for k in [k for k in keys if k.startswith("chr_order")]:
        q = _q(k)
        # the events themselves ARE shown (the learner must read them)…
        for ev in q["events"]:
            assert ev["label"] in html
        # …but the canonical order string and the resolving text are not.
        assert order_canonical(q) not in html
        assert q["explanation"] not in html
        assert q["feedback_correct"] not in html and q["feedback_wrong"] not in html
        # and the presented chip order is not the correct order (server shuffled)
        block = re.search(r'data-qkey="%s".*?</ol>' % re.escape(k), html, re.S)
        assert block is not None
        shown = re.findall(r'data-ev="([^"]+)"', block.group(0))
        assert shown and shown != order_canonical(q).split(","), "events must be presented shuffled"
    assert "data-correct" not in html
