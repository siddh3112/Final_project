"""
UNIT tests — content integrity (no HTTP, no DB).

Authoring guards: catch a malformed question (missing correct option, dup keys,
too few questions to fill a Trial, a pin that doesn't exist) the moment it's
introduced, in any location or the post-test. Pure data assertions.
"""

import pytest

from app.game_content import (
    LOCATION_ORDER,
    LOCATIONS,
    QUIZZES,
    TRIAL_COUNT,
    PINNED_QUESTIONS,
)
from app.eval_content import POST_TEST, POST_TEST_PASS

LEARNING_LOCATIONS = [loc for loc in LOCATION_ORDER if QUIZZES.get(loc)]


# ── every ordered location is real and has a quiz bank ───────────────────
def test_location_order_entries_exist():
    for loc in LOCATION_ORDER:
        assert loc in LOCATIONS, f"{loc} is in LOCATION_ORDER but missing from LOCATIONS"
        assert QUIZZES.get(loc), f"{loc} has no quiz bank"


# ── every bank can actually fill a full Trial ────────────────────────────
@pytest.mark.parametrize("loc", LEARNING_LOCATIONS)
def test_bank_can_fill_a_trial(loc):
    assert len(QUIZZES[loc]) >= TRIAL_COUNT, f"{loc}: fewer than {TRIAL_COUNT} questions"


# ── every question is well-formed and its 'correct' is a real option ─────
@pytest.mark.parametrize("loc", LEARNING_LOCATIONS)
def test_questions_wellformed(loc):
    seen = set()
    for q in QUIZZES[loc]:
        assert {"key", "question", "options", "correct"} <= set(q), f"{loc}: missing fields"
        assert q["key"] not in seen, f"{loc}: duplicate question key {q['key']}"
        seen.add(q["key"])
        opts = q["options"]
        assert isinstance(opts, dict) and set(opts) == {"A", "B", "C", "D"}, f"{loc}/{q['key']}: options must be A–D"
        assert q["correct"] in opts, f"{loc}/{q['key']}: correct '{q['correct']}' is not an option"
        assert all(str(v).strip() for v in opts.values()), f"{loc}/{q['key']}: empty option text"


# ── pinned questions must exist in their location's bank ─────────────────
def test_pinned_questions_exist():
    for loc, pins in PINNED_QUESTIONS.items():
        bank = {q["key"] for q in QUIZZES.get(loc, [])}
        for pin in pins:
            assert pin in bank, f"pinned {pin} is not in {loc}'s bank"


# ── the post-test is a 10-question, 8-to-pass assessment, well-formed ────
def test_post_test_wellformed():
    assert len(POST_TEST) == 10
    assert POST_TEST_PASS == 8
    seen = set()
    for q in POST_TEST:
        assert {"key", "question", "options", "correct", "concept", "chapter"} <= set(q)
        assert q["key"] not in seen, f"duplicate post-test key {q['key']}"
        seen.add(q["key"])
        assert set(q["options"]) == {"A", "B", "C", "D"}
        assert q["correct"] in q["options"], f"{q['key']}: correct not an option"
        assert q["chapter"] in (1, 2, 3, 4), f"{q['key']}: chapter out of range"


# ── CONTENT VALIDITY: every tested concept is TAUGHT (no orphan) ─────────
def test_post_test_concepts_are_a_subset_of_taught():
    """Assessment_Blueprint.md: the set of concepts the post-test measures must be
    a SUBSET of the concepts the game teaches — no item tests untaught material."""
    from app.game_content import TAUGHT_CONCEPTS
    tested = {q["concept"] for q in POST_TEST}
    taught = set(TAUGHT_CONCEPTS)
    orphans = tested - taught
    assert not orphans, f"post-test concepts not taught anywhere: {sorted(orphans)}"


def test_post_test_covers_previously_missing_strands():
    """The strands that were taught-but-untested (AI history, data types) are now
    assessed, and every question maps to a real taught concept + location."""
    from app.game_content import TAUGHT_CONCEPTS
    tested = {q["concept"] for q in POST_TEST}
    assert {"eras_and_winters", "ai_milestones"} <= tested, "AI history must now be tested"
    assert {"data_types", "unstructured_data"} <= tested, "data types must now be tested"
    # each tested concept resolves to a location that teaches it
    for q in POST_TEST:
        assert q["concept"] in TAUGHT_CONCEPTS, f"{q['key']} tags an unknown concept {q['concept']}"


# ── the Chronicle's timeline beats each carry a valid quick-check ────────
def test_chronicle_beats_have_valid_checks():
    beats = LOCATIONS["chronicle"].get("beats", [])
    assert beats, "the Chronicle should have era beats"
    for i, beat in enumerate(beats):
        check = beat.get("check")
        assert check, f"beat {i} missing its quick-check"
        opts = check.get("options", [])
        assert len(opts) >= 2, f"beat {i} check needs options"
        assert isinstance(check.get("correct"), int) and 0 <= check["correct"] < len(opts), \
            f"beat {i} check.correct out of range"


# ── the Library's books each carry a valid quick-check + flashcard ───────
def test_library_books_wellformed():
    books = LOCATIONS["library"].get("books", [])
    assert books, "the Library should have books"
    seen = set()
    for b in books:
        assert b["id"] not in seen, f"duplicate book id {b['id']}"
        seen.add(b["id"])
        quiz = b["quiz"]
        assert 0 <= quiz["answer"] < len(quiz["options"]), f"{b['id']}: quiz answer out of range"
        assert {"meaning", "example", "remember"} <= set(b["flashcard"])
