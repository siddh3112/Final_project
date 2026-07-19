"""
The Lexicon — the Library's click-to-ink matching board. The learner rules a line
from each of 4 concept cards to the real-world case that proves it; each correct
pairing is 1 point, graded INDEPENDENTLY through the shared core (score = count
correct, 3/4 to pass). Two of the 6 scenario slips are server-chosen DECOYS. These
tests verify behaviour; they never relax grading, independence, or the
pairing-not-in-DOM guarantee to pass.
"""

import json
import re

import pytest

from app.game_content import (
    QUIZZES,
    TAUGHT_CONCEPTS,
    TRIAL_COUNT,
    get_questions_by_keys,
    grade_quiz,
    lexicon_pool,
    lexicon_pool_sids,
    select_trial_questions,
)
from app.models import LocationProgress, QuizAttempt, TrialAttempt, db

LEX = [q for q in QUIZZES["library"] if q.get("kind") == "matching"]


def _fresh():
    db.session.expire_all()


def _q(key):
    return get_questions_by_keys("library", [key])[0]


def _start_lex(client):
    html = client.get("/location/library/trial").get_data(as_text=True)
    m = re.search(r'name="attempt_id" value="([^"]+)"', html)
    assert m, "no attempt token rendered for the Lexicon"
    token = m.group(1)
    att = TrialAttempt.query.filter_by(token=token).first()
    assert att is not None and att.status == "open"
    return token, json.loads(att.question_keys), html


def _other_sid(concept_key):
    """A valid-but-wrong scenario id for a concept (another pair's scenario)."""
    return next(q["sid"] for q in LEX if q["key"] != concept_key)


# ── content: authored pairs, unique sids, each concept pairs with its own sid ──
def test_lexicon_pairs_wellformed():
    assert len(LEX) >= 6, "need >= 6 concepts so a draw of 4 leaves >= 2 decoys"
    sids = [q["sid"] for q in LEX]
    assert len(set(sids)) == len(sids), "scenario ids must be unique"
    for q in LEX:
        assert q["correct"] == q["sid"], "a concept pairs with its OWN scenario"
        assert q["concept_tag"] in TAUGHT_CONCEPTS, "concept must be taught"
        assert q["concept"] and q["scenario"] and q["feedback_correct"] and q["feedback_wrong"]


def test_scenario_ids_do_not_echo_concept_keys():
    """A scenario id must not equal/contain its concept key, or the DOM would pair them."""
    for q in LEX:
        assert q["sid"] != q["key"]
        assert q["key"].split("_")[-1] not in q["sid"], f"{q['key']}: sid echoes the concept"


# ── selection + pool: draws 4 matching; pool = 4 correct + 2 decoys ──
def test_draw_is_four_matching_concepts():
    for _ in range(30):
        keys = select_trial_questions("library")
        assert len(keys) == TRIAL_COUNT and len(set(keys)) == TRIAL_COUNT
        assert all(_q(k).get("kind") == "matching" for k in keys)


def test_pool_has_two_decoys_from_undrawn_concepts():
    keys = select_trial_questions("library")
    pool = lexicon_pool("library", keys)
    assert len(pool) == 6, "4 correct + 2 decoys"
    pool_sids = [s["sid"] for s in pool]
    assert len(set(pool_sids)) == 6, "no duplicate slips"
    correct_sids = {_q(k)["sid"] for k in keys}
    decoys = [sid for sid in pool_sids if sid not in correct_sids]
    assert len(decoys) == 2, "exactly two decoy slips"
    # decoys belong to concepts NOT drawn
    drawn_sids = {_q(k)["sid"] for k in keys}
    for d in decoys:
        assert d not in drawn_sids


# ── shared grading core: each pairing independent, 1 point each ──
def test_grade_quiz_scores_each_pairing_independently():
    keys = select_trial_questions("library")
    qs = get_questions_by_keys("library", keys)
    allc = {q["key"]: q["correct"] for q in qs}
    _r, s4, _t, p4 = grade_quiz("library", allc, shown_keys=keys)
    assert s4 == 4 and p4 is True
    three = dict(allc); three[qs[0]["key"]] = _other_sid(qs[0]["key"])
    _r, s3, _t, p3 = grade_quiz("library", three, shown_keys=keys)
    assert s3 == 3 and p3 is True
    two = dict(allc)
    two[qs[0]["key"]] = _other_sid(qs[0]["key"])
    two[qs[1]["key"]] = _other_sid(qs[1]["key"])
    _r, s2, _t, p2 = grade_quiz("library", two, shown_keys=keys)
    assert s2 == 2 and p2 is False, "independent — two right is 2/4, a fail (not all-or-nothing)"


# ── integration: a fully correct board scores 4 and passes ──
def test_correct_board_scores_four(client, user_factory, login):
    u = user_factory()
    login(u)
    token, keys, _ = _start_lex(client)
    data = {"attempt_id": token}
    for k in keys:
        data[k] = _q(k)["correct"]
    r = client.post("/location/library/submit", data=data)
    assert r.status_code == 200
    _fresh()
    rows = QuizAttempt.query.filter_by(user_id=u.id, location="library").all()
    assert len(rows) == TRIAL_COUNT and all(a.is_correct for a in rows)
    lp = LocationProgress.query.filter_by(user_id=u.id, location="library").first()
    assert lp.passed is True and lp.best_score == 4
    for k in keys:
        row = next(a for a in rows if a.question_key == k)
        assert row.selected_answer == _q(k)["correct"]


def test_three_passes_two_fails(client, user_factory, login):
    u = user_factory()
    login(u)
    token, keys, _ = _start_lex(client)
    data = {"attempt_id": token}
    for i, k in enumerate(keys):
        data[k] = _q(k)["correct"] if i < 3 else _other_sid(k)
    client.post("/location/library/submit", data=data)
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="library").first()
    assert lp.passed is True and lp.best_score == 3

    u2 = user_factory()
    login(u2)
    token2, keys2, _ = _start_lex(client)
    data2 = {"attempt_id": token2}
    for i, k in enumerate(keys2):
        data2[k] = _q(k)["correct"] if i < 2 else _other_sid(k)
    client.post("/location/library/submit", data=data2)
    _fresh()
    lp2 = LocationProgress.query.filter_by(user_id=u2.id, location="library").first()
    assert lp2.passed is False and lp2.best_score == 2


# ── forged / malformed submissions cannot score ──
def test_unknown_scenario_id_not_scored(client, user_factory, login):
    u = user_factory()
    login(u)
    token, keys, _ = _start_lex(client)
    data = {"attempt_id": token}
    for k in keys:
        data[k] = _q(k)["correct"]
    data[keys[0]] = "sc_not_real"        # off-pool id
    client.post("/location/library/submit", data=data)
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="library", question_key=keys[0]).first()
    assert row.selected_answer is None and row.is_correct is False


def test_reused_scenario_cannot_inflate(client, user_factory, login):
    """Assigning one scenario to two concepts can't make both correct — a scenario is
    the correct match for at most one concept, and grading is independent."""
    u = user_factory()
    login(u)
    token, keys, _ = _start_lex(client)
    a, b = keys[0], keys[1]
    sid_a = _q(a)["correct"]
    data = {"attempt_id": token, a: sid_a, b: sid_a}   # both inked to A's case
    for k in keys[2:]:
        data[k] = _q(k)["correct"]
    client.post("/location/library/submit", data=data)
    _fresh()
    rows = {r.question_key: r for r in QuizAttempt.query.filter_by(user_id=u.id, location="library").all()}
    assert rows[a].is_correct is True, "A gets its own case"
    assert rows[b].is_correct is False, "B reusing A's case is wrong"


def test_missing_concept_scores_wrong(client, user_factory, login):
    u = user_factory()
    login(u)
    token, keys, _ = _start_lex(client)
    data = {"attempt_id": token}
    for k in keys[1:]:                   # omit the first concept's field
        data[k] = _q(k)["correct"]
    client.post("/location/library/submit", data=data)
    _fresh()
    row = QuizAttempt.query.filter_by(user_id=u.id, location="library", question_key=keys[0]).first()
    assert row.selected_answer is None and row.is_correct is False


def test_matching_not_committable_via_answer(client, user_factory, login):
    u = user_factory()
    login(u)
    token, keys, _ = _start_lex(client)
    r = client.post("/location/library/answer",
                    json={"attempt_id": token, "qkey": keys[0], "letter": "A"})
    assert r.status_code == 400, "the Lexicon commits at submit, not via /answer"


# ── no pairing data in the DOM; decoys indistinguishable; order varies ──
def test_no_pairing_or_decoy_tell_in_dom(client, user_factory, login):
    u = user_factory()
    login(u)
    _token, keys, html = _start_lex(client)
    # the 6 cases render (incl. 2 decoys) — the learner must read them…
    pool = lexicon_pool("library", keys)
    assert len(re.findall(r'class="lex-card lex-scenario"', html)) == 6
    for s in pool:
        assert s["text"] in html
    # …but nothing marks which case is correct for which concept. (The howto text
    # legitimately says two are decoys; what matters is that no individual SLIP is
    # distinguishable — every slip is the same markup: a data-scenario id + text.)
    assert "data-correct" not in html
    slip_tags = re.findall(r'<button[^>]*class="lex-card lex-scenario"[^>]*>', html)
    assert len(slip_tags) == 6
    for tag in slip_tags:
        assert "correct" not in tag and "is-" not in tag and "data-decoy" not in tag
    # a concept card must NOT carry its correct scenario id
    for k in keys:
        sid = _q(k)["sid"]
        m = re.search(r'data-concept="%s"[^>]*>' % re.escape(k), html)
        assert m and sid not in m.group(0), f"{k}: concept card leaks its scenario id"


def test_scenario_order_varies_across_attempts(client, user_factory, login):
    u = user_factory()
    login(u)
    orders = set()
    for _ in range(8):
        _t, _keys, html = _start_lex(client)
        sids = tuple(re.findall(r'data-scenario="([^"]+)"', html))
        orders.add(sids)
    assert len(orders) > 1, "the scenario slips should be shuffled per attempt"
