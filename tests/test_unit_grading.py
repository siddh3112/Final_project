"""
UNIT tests — the pure grading + question-selection core (no HTTP, no DB).

These pin the deterministic behaviour of grade_quiz / select_trial_questions /
get_questions_by_keys directly, across every location. They VERIFY the code —
if one fails it is a test mismatch (fix the test) or a real grading bug (report
it); they never license weakening grading, the shown-set rule, or the pin.
"""

import pytest

from app.game_content import (
    BIN_IDS,
    LOCATION_ORDER,
    PASS_THRESHOLD,
    TRIAL_COUNT,
    PINNED_QUESTIONS,
    QUIZZES,
    grade_quiz,
    get_questions_by_keys,
    select_trial_questions,
)

LEARNING_LOCATIONS = [loc for loc in LOCATION_ORDER if QUIZZES.get(loc)]


def _bank_keys(loc):
    return [q["key"] for q in QUIZZES[loc]]


def _submission(loc, shown, n_correct):
    """Answer the first `n_correct` of `shown` correctly, the rest wrong.

    Handles MCQ items (a wrong option letter) and `sort` items (a wrong bin id) —
    both grade through the same core as `selected == correct`.
    """
    qs = get_questions_by_keys(loc, shown)
    submitted = {}
    for i, q in enumerate(qs):
        if i < n_correct:
            submitted[q["key"]] = q["correct"]
        elif q.get("kind") == "sort":
            submitted[q["key"]] = next(b for b in BIN_IDS if b != q["correct"])
        else:
            submitted[q["key"]] = next(l for l in q["options"] if l != q["correct"])
    return submitted


# ── grade_quiz: score == number correct, for every location ──────────────
@pytest.mark.parametrize("loc", LEARNING_LOCATIONS)
def test_score_equals_number_correct(loc):
    shown = _bank_keys(loc)[:TRIAL_COUNT]
    for n in range(TRIAL_COUNT + 1):
        _r, score, total, _p = grade_quiz(loc, _submission(loc, shown, n), shown_keys=shown)
        assert score == n, f"{loc}: {n} correct should score {n}, got {score}"
        assert total == TRIAL_COUNT


# ── grade_quiz: pass boundary sits exactly at PASS_THRESHOLD, every location ──
@pytest.mark.parametrize("loc", LEARNING_LOCATIONS)
def test_pass_boundary_at_threshold(loc):
    shown = _bank_keys(loc)[:TRIAL_COUNT]
    for n in range(TRIAL_COUNT + 1):
        _r, _s, _t, passed = grade_quiz(loc, _submission(loc, shown, n), shown_keys=shown)
        assert passed is (n >= PASS_THRESHOLD), f"{loc}: {n}/4 passed={passed}"


# ── grade_quiz: only the SHOWN keys are graded (graded set == shown set) ──
def test_only_shown_keys_are_graded():
    loc = "chronicle"
    shown = _bank_keys(loc)[:2]              # grade just two questions
    submitted = _submission(loc, shown, 2)   # both correct
    # Smuggle in a (correct) answer for a NON-shown question — must be ignored.
    hidden_key = _bank_keys(loc)[3]
    hidden_q = next(q for q in QUIZZES[loc] if q["key"] == hidden_key)
    submitted[hidden_key] = hidden_q["correct"]

    results, score, total, _p = grade_quiz(loc, submitted, shown_keys=shown)
    assert total == 2, "only the 2 shown questions are graded"
    assert score == 2
    assert {r["key"] for r in results} == set(shown), "results cover exactly the shown set"


# ── grade_quiz: an unanswered question (None) is wrong, never a free point ──
def test_unanswered_is_incorrect():
    loc = "library"
    shown = _bank_keys(loc)[:TRIAL_COUNT]
    submitted = _submission(loc, shown, TRIAL_COUNT)  # all correct
    submitted[shown[0]] = None                        # blank the first
    results, score, _t, _p = grade_quiz(loc, submitted, shown_keys=shown)
    assert score == TRIAL_COUNT - 1
    first = next(r for r in results if r["key"] == shown[0])
    assert first["is_correct"] is False and first["selected"] is None


# ── grade_quiz: result rows carry what the template needs, correctly ─────
def test_result_rows_are_wellformed():
    loc = "observatory"
    shown = _bank_keys(loc)[:TRIAL_COUNT]
    submitted = _submission(loc, shown, 1)  # exactly the first correct
    results, _s, _t, _p = grade_quiz(loc, submitted, shown_keys=shown)
    for r in results:
        assert {"key", "question", "options", "selected", "correct", "is_correct", "feedback"} <= set(r)
        assert (r["selected"] == r["correct"]) is r["is_correct"]
        assert r["feedback"], "each row must carry non-empty feedback/explanation"


# ── select_trial_questions: right count, valid, unique ───────────────────
@pytest.mark.parametrize("loc", LEARNING_LOCATIONS)
def test_selection_count_valid_unique(loc):
    bank = _bank_keys(loc)
    chosen = select_trial_questions(loc)
    assert len(chosen) == min(TRIAL_COUNT, len(bank))
    assert len(set(chosen)) == len(chosen), "no duplicate questions in one trial"
    assert set(chosen) <= set(bank), "every chosen key is a real question in the bank"


# ── select_trial_questions: pinned questions are always present AND first ──
def test_pinned_question_always_first():
    # The Chronicle pins both ordering items (single keys), so they lead every draw
    # in order. (The AI Lab no longer pins — its whole Trial is the sorting board.)
    loc = "chronicle"
    pinned = PINNED_QUESTIONS[loc]
    for _ in range(40):
        chosen = select_trial_questions(loc)
        assert chosen[: len(pinned)] == pinned, "pinned items must lead every draw"


# ── select_trial_questions: genuinely samples (not a fixed slice) ────────
@pytest.mark.parametrize("loc", LEARNING_LOCATIONS)
def test_selection_varies_when_bank_larger_than_trial(loc):
    if len(_bank_keys(loc)) <= TRIAL_COUNT:
        pytest.skip("bank not larger than a full trial — nothing to vary")
    seen = {tuple(select_trial_questions(loc)) for _ in range(60)}
    assert len(seen) > 1, "selection should vary across attempts, not be a fixed slice"


# ── get_questions_by_keys: preserves order, drops unknown keys ───────────
def test_get_questions_by_keys_order_and_filter():
    loc = "library"
    keys = _bank_keys(loc)
    picked = get_questions_by_keys(loc, [keys[2], keys[0], "bogus"])
    assert [q["key"] for q in picked] == [keys[2], keys[0]]
