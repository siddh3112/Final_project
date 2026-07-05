"""
UNIT tests — service layer.

Professor Atlas guardrails + fallback semantics (pure, Ollama off), the XP
formula, the leaderboard's combined score / speed bonus, and the achievements
qualifier. The DB-backed ones use the in-memory fixtures; none touch Ollama.
"""

import pytest

from app.services import npc_service
from app.services.npc_service import get_response, _looks_like_answer_request, FALLBACK, KEYWORDS
from app.services import gamification as G
from app.services import leaderboard as LB
from app.services import achievements as A
from app.models import LocationProgress, Achievement, db


# ══════════════════════ Professor Atlas — guardrails ══════════════════════

def test_atlas_refuses_to_hand_over_answers():
    for msg in ["what is the answer?", "just tell me the correct answer",
                "which option is right", "is it C?"]:
        assert _looks_like_answer_request(msg), f"should be flagged as an answer-grab: {msg!r}"
        text, is_fallback = get_response("library", msg, ollama_enabled=False)
        assert text != FALLBACK
        assert is_fallback is False
        # a deflection never leaks a bare option letter as "the answer"
        assert "the answer is" not in text.lower()


def test_atlas_explains_a_known_keyword():
    for loc, kws in KEYWORDS.items():
        keyword = next(iter(kws))
        text, is_fallback = get_response(loc, f"tell me about {keyword}", ollama_enabled=False)
        assert text == kws[keyword], f"{loc}: '{keyword}' should return its authored explanation"
        assert is_fallback is False


def test_atlas_fallback_only_when_nothing_matches():
    text, is_fallback = get_response("library", "zxqw flibberjabber", ollama_enabled=False)
    assert text == FALLBACK
    assert is_fallback is True, "is_fallback must be True only when no rule matched"


def test_non_answer_question_is_not_flagged():
    assert not _looks_like_answer_request("can you explain narrow AI?")


# ══════════════════════════ XP formula ══════════════════════════════════

def test_compute_xp_formula(app, user_factory):
    # library passed 4/4, chronicle attempted best 2/4 (not passed)
    u = user_factory(passed=("library",))
    db.session.add(LocationProgress(user_id=u.id, location="chronicle",
                                    passed=False, best_score=2, attempts_count=1))
    db.session.commit()
    # library: 4*25 + 100 bonus = 200 ; chronicle: 2*25 + 0 = 50
    expected = (4 * G.XP_PER_CORRECT + G.XP_LOCATION_BONUS) + (2 * G.XP_PER_CORRECT)
    assert G.compute_xp(u) == expected


def test_compute_xp_ignores_posttest_until_done(app, user_factory):
    # a passed post-test only counts once post_test_done is set
    u = user_factory(passed=("library",), post_test_done=False,
                     knowledge_tests=[{"score": 9, "answers": {}}])
    without = G.compute_xp(u)
    u.post_test_done = True
    db.session.commit()
    assert G.compute_xp(u) == without + 9 * G.XP_PER_POSTTEST_CORRECT


# ══════════════════════ Leaderboard scoring ═════════════════════════════

def test_speed_bonus_capped_and_floored():
    assert LB.speed_bonus(None) == 0
    assert LB.speed_bonus(10_000) == 0                  # very slow → floored at 0
    assert LB.speed_bonus(0) == LB.SPEED_BONUS_CAP      # instant → capped
    # monotonic: faster is never worth less
    assert LB.speed_bonus(120) >= LB.speed_bonus(300)


def test_combined_score_weights():
    # 8 correct post-test, three trials 4/4, 4 badges, unknown time
    total = LB.combined_score(8, [4, 4, 4], 4, None)
    expected = 8 * LB.WEIGHTS["post_test"] + 12 * LB.WEIGHTS["location"] + 4 * LB.WEIGHTS["badge"]
    assert total == expected


# ══════════════════════ Achievements qualifier ══════════════════════════

def test_achievement_granted_on_location_pass(app, user_factory):
    u = user_factory(passed=("library",))
    assert "first_steps" in A._qualifying(u)
    new = A.grant_new(u)
    assert "first_steps" in new
    assert Achievement.query.filter_by(user_id=u.id, achievement_key="first_steps").count() == 1


def test_grant_new_is_idempotent(app, user_factory):
    u = user_factory(passed=("library", "chronicle"))
    A.grant_new(u)
    again = A.grant_new(u)   # second call must not double-grant
    assert again == []
    assert Achievement.query.filter_by(user_id=u.id).count() == 2  # first_steps + chronicler


def test_atlas_sage_requires_post_test_done(app, user_factory):
    u = user_factory(passed=("library",), post_test_done=False)
    assert "atlas_sage" not in A._qualifying(u)
    u.post_test_done = True
    db.session.commit()
    assert "atlas_sage" in A._qualifying(u)
