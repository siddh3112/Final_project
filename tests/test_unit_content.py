"""
UNIT tests — content integrity (no HTTP, no DB).

Authoring guards: catch a malformed question (missing correct option, dup keys,
too few questions to fill a Trial, a pin that doesn't exist) the moment it's
introduced, in any location or the post-test. Pure data assertions.
"""

import os
import re

import pytest

from app.game_content import (
    BIN_IDS,
    LOCATION_ORDER,
    LOCATIONS,
    QUIZZES,
    TRIAL_COUNT,
    PINNED_QUESTIONS,
)
from app.eval_content import POST_TEST, POST_TEST_PASS

LEARNING_LOCATIONS = [loc for loc in LOCATION_ORDER if QUIZZES.get(loc)]

_OBSERVATORY_JS = os.path.join(
    os.path.dirname(__file__), "..", "app", "static", "js", "observatory.js"
)


def _observatory_js():
    with open(_OBSERVATORY_JS, encoding="utf-8") as f:
        return f.read()


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
        assert q["key"] not in seen, f"{loc}: duplicate question key {q['key']}"
        seen.add(q["key"])
        if q.get("kind") == "order":
            # Ordering item ("Broken Timeline"): a stem + >= 2 events with unique
            # ids and non-empty labels. The correct order is the authored order.
            assert {"key", "question", "events"} <= set(q), f"{loc}/{q['key']}: missing order fields"
            evs = q["events"]
            assert isinstance(evs, list) and len(evs) >= 2, f"{loc}/{q['key']}: needs >= 2 events"
            ids = [e["id"] for e in evs]
            assert len(set(ids)) == len(ids), f"{loc}/{q['key']}: duplicate event id"
            assert all(str(e.get("label", "")).strip() for e in evs), f"{loc}/{q['key']}: empty event label"
            continue
        if q.get("kind") == "sort":
            # Classification object ("Sorting Board"): a stem/label + a correct bin.
            assert {"key", "question", "correct"} <= set(q), f"{loc}/{q['key']}: missing sort fields"
            assert str(q["question"]).strip(), f"{loc}/{q['key']}: empty object label"
            assert q["correct"] in BIN_IDS, f"{loc}/{q['key']}: correct bin '{q['correct']}' is not a real bin"
            continue
        if q.get("kind") == "matching":
            # Lexicon pair ("The Lexicon"): a concept + a scenario + the scenario id
            # it pairs with. The correct id must be this pair's own scenario id.
            assert {"key", "concept", "scenario", "sid", "correct"} <= set(q), f"{loc}/{q['key']}: missing matching fields"
            assert str(q["concept"]).strip() and str(q["scenario"]).strip(), f"{loc}/{q['key']}: empty concept/scenario"
            assert q["correct"] == q["sid"], f"{loc}/{q['key']}: a concept must pair with its OWN scenario id"
            continue
        assert {"key", "question", "options", "correct"} <= set(q), f"{loc}: missing fields"
        opts = q["options"]
        assert isinstance(opts, dict) and set(opts) == {"A", "B", "C", "D"}, f"{loc}/{q['key']}: options must be A–D"
        assert q["correct"] in opts, f"{loc}/{q['key']}: correct '{q['correct']}' is not an option"
        assert all(str(v).strip() for v in opts.values()), f"{loc}/{q['key']}: empty option text"


# ── pinned questions must exist in their location's bank ─────────────────
def test_pinned_questions_exist():
    for loc, pins in PINNED_QUESTIONS.items():
        bank = {q["key"] for q in QUIZZES.get(loc, [])}
        for pin in pins:
            # A pin is either a single key or a GROUP (a list/tuple of
            # interchangeable keys — e.g. the Observatory Hallucination Hunt sets).
            members = pin if isinstance(pin, (list, tuple)) else [pin]
            for key in members:
                assert key in bank, f"pinned {key} is not in {loc}'s bank"


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
    a SUBSET of the concepts the game teaches, so no item tests untaught material.

    Deliberately a subset and not an equality. Teaching more than you assess is
    fine and expected; assessing something you never taught is a content-validity
    fault, because a wrong answer would then measure the gap in the game rather
    than the learner's understanding. Only the orphan direction is an error.
    """
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


# ── Observatory star count is ONE number across JS content + server hooks ─
def test_observatory_star_count_consistent_across_sources():
    """The Observatory's star count must be a single N everywhere: the JS concept
    list (stars), the JS quick-checks, and the server-side per-star hooks (which
    drive explore_valid_ids). Guards the count from drifting between files — the
    root of the earlier 5-vs-10 bugs."""
    from app.game_content import get_hooks

    js = _observatory_js()
    n_concepts = len(re.findall(r"\bheading:", js))   # CONCEPTS entries (one per star)
    n_checks = len(re.findall(r"\bcorrect:", js))     # CHECKS entries (one per star)
    n_hooks = len(get_hooks("observatory"))           # server per-star hooks (H1 source)
    # the 4th list: CONSTELLATION_STARS coordinates (one { x:, y: } per star), the
    # array whose .length every JS count (completion, gate, progress, finale) derives from.
    stars_block = re.search(r"const CONSTELLATION_STARS\s*=\s*\[(.*?)\];", js, re.S)
    assert stars_block, "CONSTELLATION_STARS array not found"
    n_stars = len(re.findall(r"\{\s*x:", stars_block.group(1)))
    assert n_stars == n_concepts == n_checks == n_hooks, (
        f"Observatory counts diverge: stars={n_stars} concepts={n_concepts} "
        f"checks={n_checks} hooks={n_hooks}"
    )
    assert n_stars == 10, f"Observatory should have 10 stars, found {n_stars}"


# ── Observatory Trial gate opens ONLY after ALL N stars (not a partial beat) ─
def test_observatory_trial_unlocks_only_after_all_stars():
    """Regression (recurring bug): the Trial gate must open ONLY once every star is
    mapped — derived from CONSTELLATION_STARS.length — never at a mid-journey
    'present' beat (which previously opened it at star 5). Source-level guard so it
    can't silently regress: the single unlock trigger must be gated by the full
    star count."""
    js = _observatory_js()
    pending = [ln for ln in js.splitlines() if re.search(r"pendingUnlock\s*=\s*true", ln)]
    assert len(pending) == 1, f"expected exactly one pendingUnlock trigger, found {len(pending)}"
    assert re.search(r"discoveredCount\s*>=\s*CONSTELLATION_STARS\.length", pending[0]), (
        "the Trial unlock must derive from the FULL star count (all N stars), "
        "not a concept type or a partial number"
    )


# ── the finale SOUND fires ONCE at completion, never on the type=='present' path ─
def test_observatory_finale_sound_gated_by_completion_not_present():
    """Regression (Problem 7, the recurring 5-vs-10 family): the finale fanfare
    (soundFinal) must fire ONCE at true completion, gated by the FULL star count, and
    must NOT be reachable via the mid-journey concept type 'present' (a 5-star-era
    marker that still sits on stars 5 and 8). Source-level guard so it can't regress."""
    js = _observatory_js()
    # soundFinal appears exactly twice: its definition + exactly ONE call site.
    assert len(re.findall(r"soundFinal\s*\(", js)) == 2, "expected exactly one soundFinal() call site"
    # the call fires inside the completion-count gate (the SAME single source as the
    # unlock gate), so it agrees with the readout and the gate.
    assert re.search(r"discoveredCount\s*>=\s*CONSTELLATION_STARS\.length\s*\)\s*\{\s*soundFinal\s*\(", js), (
        "soundFinal() must be gated by the FULL star count (>= CONSTELLATION_STARS.length), "
        "not fired at a partial count"
    )
    # it must NOT be triggered by concept.type === 'present' (stars 5 and 8).
    assert not re.search(r'type\s*===\s*"present"[^{}]*\{\s*soundFinal', js), (
        "soundFinal() must not be triggered by concept.type === 'present'"
    )


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
