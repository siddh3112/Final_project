"""
Revisit is READ-ONLY for the record (research-data integrity).

The bug: the AI Lab (its terminal embeds the location's Trial) re-asked and
RE-RECORDED an already-answered question on revisit, writing new scored attempts.
Fix: a passed Trial is replayable for PRACTICE but writes NOTHING, and a passive
reread of a passed AI Lab creates no TrialAttempt at all. First-time flow (and a
not-yet-passed retry before the first pass) records exactly once, unchanged.
"""

import json
import re

from app.game_content import get_questions_by_keys, QUIZZES
from app.models import LocationProgress, QuizAttempt, TrialAttempt, db


def _fresh():
    db.session.expire_all()


def _terminal_attempt(client, mode=""):
    """GET the AI Lab terminal; return (attempt_id, stored_keys) or (\"\", []) when
    a passive reread serves no attempt."""
    url = "/location/ai_lab" + ("?mode=practice" if mode == "practice" else "")
    html = client.get(url).get_data(as_text=True)
    m = re.search(r'name="attempt_id" value="([^"]*)"', html)
    aid = m.group(1) if m else ""
    if not aid:
        return "", []
    att = TrialAttempt.query.filter_by(token=aid).first()
    return aid, (json.loads(att.question_keys) if att else [])


def _all_correct(location, keys):
    """{key: correct-bin} for a sort/mcq bank so a submit scores full marks."""
    data = {}
    for q in get_questions_by_keys(location, keys):
        data[q["key"]] = q["correct"]   # sort items: the correct bin id
    return data


def _ai_lab_user(user_factory, login):
    u = user_factory(passed=("library", "chronicle"))   # AI Lab unlocked, not passed
    login(u)
    return u


# ── the AI Lab: first pass records once; revisit + practice write nothing ──
def test_ai_lab_first_pass_records_once_then_revisit_and_practice_write_nothing(client, user_factory, login):
    u = _ai_lab_user(user_factory, login)

    # FIRST PASS — records exactly once.
    aid, keys = _terminal_attempt(client)
    assert aid and keys, "a not-yet-passed lab must serve a live board attempt"
    data = {"attempt_id": aid}
    data.update(_all_correct("ai_lab", keys))
    assert client.post("/location/ai_lab/submit", data=data).status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="ai_lab").first()
    assert lp.passed is True and lp.attempts_count == 1
    qa = QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab").count()
    assert qa == len(keys), "first pass records exactly one attempt's worth of rows"
    ta = TrialAttempt.query.filter_by(user_id=u.id, location="ai_lab").count()

    # PASSIVE REVISIT — no board attempt served, and NO TrialAttempt created.
    aid2, keys2 = _terminal_attempt(client)
    _fresh()
    assert aid2 == "" and keys2 == [], "a passed lab revisit must not serve a live attempt"
    assert TrialAttempt.query.filter_by(user_id=u.id, location="ai_lab").count() == ta, \
        "passive revisit must create NO TrialAttempt"
    assert QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab").count() == qa

    # PRACTICE RUN — a board attempt is served, submitting grades but records nothing.
    paid, pkeys = _terminal_attempt(client, mode="practice")
    assert paid and paid != aid, "practice serves a fresh board attempt"
    pdata = {"attempt_id": paid}
    pdata.update(_all_correct("ai_lab", pkeys))
    resp = client.post("/location/ai_lab/submit", data=pdata)
    assert resp.status_code == 200
    _fresh()
    assert QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab").count() == qa, \
        "PRACTICE must add NO QuizAttempt"
    lp2 = LocationProgress.query.filter_by(user_id=u.id, location="ai_lab").first()
    assert lp2.attempts_count == 1, "PRACTICE must not bump attempts_count"
    assert TrialAttempt.query.filter_by(token=paid).first() is None, \
        "the practice TrialAttempt must be deleted (nothing persisted)"
    assert "not recorded" in resp.get_data(as_text=True).lower(), \
        "practice results must be marked not recorded"


# ── the uniform rule: replaying ANY passed Trial is practice and writes nothing ──
def test_passed_trial_replay_is_practice_and_records_nothing(client, user_factory, login):
    # Observatory Trial (all-hunt). Pass it once (recorded), then replay it.
    u = user_factory(passed=("library", "chronicle", "ai_lab"))   # Observatory unlocked
    login(u)

    def start_trial():
        html = client.get("/location/observatory/trial").get_data(as_text=True)
        aid = re.search(r'name="attempt_id" value="([^"]+)"', html).group(1)
        att = TrialAttempt.query.filter_by(token=aid).first()
        return aid, json.loads(att.question_keys)

    aid, keys = start_trial()
    data = {"attempt_id": aid}
    for q in get_questions_by_keys("observatory", keys):
        data[q["key"]] = q["correct"]           # catch every false claim => pass
    assert client.post("/location/observatory/submit", data=data).status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="observatory").first()
    assert lp.passed is True and lp.attempts_count == 1
    qa = QuizAttempt.query.filter_by(user_id=u.id, location="observatory").count()

    # REPLAY (already passed) — practice: writes nothing, deletes the attempt.
    aid2, keys2 = start_trial()
    d2 = {"attempt_id": aid2}
    for q in get_questions_by_keys("observatory", keys2):
        d2[q["key"]] = q["correct"]
    resp = client.post("/location/observatory/submit", data=d2)
    assert resp.status_code == 200
    _fresh()
    assert QuizAttempt.query.filter_by(user_id=u.id, location="observatory").count() == qa, \
        "a passed-Trial replay must record no new QuizAttempt"
    lp2 = LocationProgress.query.filter_by(user_id=u.id, location="observatory").first()
    assert lp2.attempts_count == 1, "a passed-Trial replay must not bump attempts_count"
    assert TrialAttempt.query.filter_by(token=aid2).first() is None, \
        "the replayed (practice) attempt must be deleted"


# ── first-time flow is unchanged: a not-yet-passed retry BEFORE the first pass records ──
def test_not_yet_passed_retry_still_records(client, user_factory, login):
    u = _ai_lab_user(user_factory, login)

    # A FAILING attempt (all wrong) still records as attempt 1 (not passed).
    aid, keys = _terminal_attempt(client)
    bins = ["structured", "semi", "unstructured", "dark"]
    wrong = {}
    for q in get_questions_by_keys("ai_lab", keys):
        wrong[q["key"]] = next(b for b in bins if b != q["correct"])   # deliberately wrong
    d1 = {"attempt_id": aid}
    d1.update(wrong)
    assert client.post("/location/ai_lab/submit", data=d1).status_code == 200
    _fresh()
    lp = LocationProgress.query.filter_by(user_id=u.id, location="ai_lab").first()
    assert lp.passed is False and lp.attempts_count == 1, "a failing first attempt records"
    qa1 = QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab").count()
    assert qa1 == len(keys)

    # A RETRY while still not passed records again (attempt 2) — first-time flow intact.
    aid2, keys2 = _terminal_attempt(client)
    assert aid2 and aid2 != aid, "a not-yet-passed lab still serves a live board attempt"
    d2 = {"attempt_id": aid2}
    d2.update(_all_correct("ai_lab", keys2))
    assert client.post("/location/ai_lab/submit", data=d2).status_code == 200
    _fresh()
    lp2 = LocationProgress.query.filter_by(user_id=u.id, location="ai_lab").first()
    assert lp2.passed is True and lp2.attempts_count == 2, "a not-yet-passed retry records (attempt 2)"
    assert QuizAttempt.query.filter_by(user_id=u.id, location="ai_lab").count() == qa1 + len(keys2)
