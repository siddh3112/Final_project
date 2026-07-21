"""
The Journal — a read-only archive of the learner's own sealed reflections.

These tests pin the guarantees the Journal must keep:
  - it LISTS sealed reflections (the learner's verbatim text + Atlas's reply + the
    engine-source label) per location,
  - it shows unreflected locations as EMPTY slots with an "X / N" readout where N is
    DERIVED from the prompt-bearing locations (not hardcoded),
  - it is reachable, login-gated, and strictly READ-ONLY (no writes, no grading, no
    progression), and reflections stay OPTIONAL (skipping shows an empty slot).
"""

from app.models import LocationProgress, QuizAttempt, Reflection, TrialAttempt, db
from app.game_content import LOCATION_ORDER, REFLECTION_PROMPTS

# N is whatever the app derives: the locations, in order, that offer a reflection.
REFLECTABLE = [k for k in LOCATION_ORDER if k in REFLECTION_PROMPTS]
N = len(REFLECTABLE)


def _seal(client, location, text):
    """Seal a real reflection via the same endpoint the results page uses."""
    return client.post(
        f"/location/{location}/reflect",
        json={"response": text, "skipped": False},
    )


# ──────────────────────────────────────────────────────────────────────────
# Reachability + login gating
# ──────────────────────────────────────────────────────────────────────────

def test_journal_requires_login(client):
    """Anonymous users are redirected to login, never shown the Journal."""
    resp = client.get("/journal")
    assert resp.status_code in (302, 401)
    if resp.status_code == 302:
        assert "/auth/login" in resp.headers["Location"]


def test_journal_reachable_from_hub(client, user_factory, login):
    """The hub renders a link to /journal (the entry point)."""
    user = user_factory()
    login(user)
    hub = client.get("/")
    assert hub.status_code == 200
    assert "/journal" in hub.get_data(as_text=True)


def test_journal_page_renders(client, user_factory, login):
    user = user_factory()
    login(user)
    resp = client.get("/journal")
    assert resp.status_code == 200
    assert "The Journal" in resp.get_data(as_text=True)


# ──────────────────────────────────────────────────────────────────────────
# Content: sealed reflections + Atlas reply + source label; N derived
# ──────────────────────────────────────────────────────────────────────────

def test_readout_denominator_is_derived(client, user_factory, login):
    """The 'X / N' readout uses N derived from the prompt-bearing locations."""
    user = user_factory()
    login(user)
    html = client.get("/journal").get_data(as_text=True)
    assert f"/ {N}" in html
    # Nothing sealed yet -> 0 / N.
    assert "<strong>0</strong>" in html


def test_sealed_reflection_shows_text_reply_and_source(client, user_factory, login):
    """A sealed reflection lists the learner's verbatim words, Atlas's reply, and
    the engine-source label. With Ollama OFF in tests the source is the rules
    fallback, shown as 'System generated'."""
    loc = REFLECTABLE[0]
    user = user_factory(passed=(loc,))
    login(user)

    my_words = "Narrow AI is a specialist and general AI would be a generalist."
    assert _seal(client, loc, my_words).status_code == 200

    # It was stored with an Atlas reply and a rules source (Ollama disabled).
    r = Reflection.query.filter_by(user_id=user.id, location=loc, skipped=False).one()
    assert r.response_text == my_words
    assert r.atlas_source == "rules"
    assert r.atlas_response  # non-empty authored reply

    html = client.get("/journal").get_data(as_text=True)
    assert my_words in html                    # verbatim sealed thought
    assert r.atlas_response in html            # Atlas's reply
    assert "System generated" in html          # source label (rules -> System)
    assert "Granite generated" not in html
    assert "<strong>1</strong>" in html        # readout incremented


def test_unsealed_locations_show_as_empty_slots(client, user_factory, login):
    """Locations not reflected on appear as empty 'Not yet sealed' slots, and every
    reflectable location has a slot (so gaps are visible)."""
    loc = REFLECTABLE[0]
    user = user_factory(passed=(loc,))
    login(user)
    _seal(client, loc, "A sealed thought.")

    html = client.get("/journal").get_data(as_text=True)
    # One sealed, the rest empty -> the empty marker appears (N-1 >= 1 here).
    assert "Not yet sealed" in html
    # Every reflectable location is represented by name.
    from app.game_content import LOCATIONS
    for k in REFLECTABLE:
        assert LOCATIONS[k]["name"] in html


def test_skipped_reflection_is_not_a_sealed_slot(client, user_factory, login):
    """Skipping is still optional: a skipped reflection does NOT fill the slot; the
    location stays an empty slot and the sealed count does not rise."""
    loc = REFLECTABLE[0]
    user = user_factory(passed=(loc,))
    login(user)

    resp = client.post(f"/location/{loc}/reflect", json={"response": "", "skipped": True})
    assert resp.status_code == 200

    # A skipped row exists, but it carries no Atlas reply and is not "sealed".
    r = Reflection.query.filter_by(user_id=user.id, location=loc).one()
    assert r.skipped is True
    assert r.atlas_response is None

    html = client.get("/journal").get_data(as_text=True)
    assert "<strong>0</strong>" in html        # still 0 sealed
    assert "Not yet sealed" in html


# ──────────────────────────────────────────────────────────────────────────
# Read-only: the Journal writes nothing and changes no progression
# ──────────────────────────────────────────────────────────────────────────

def test_journal_get_is_read_only(client, user_factory, login):
    """Viewing the Journal must not create or mutate any row: no Reflection,
    LocationProgress, TrialAttempt, or QuizAttempt writes on a GET."""
    loc = REFLECTABLE[0]
    user = user_factory(passed=(loc,))
    login(user)
    _seal(client, loc, "Immutable on view.")

    before = (
        Reflection.query.count(),
        LocationProgress.query.count(),
        TrialAttempt.query.count(),
        QuizAttempt.query.count(),
    )
    # View several times.
    for _ in range(3):
        assert client.get("/journal").status_code == 200
    after = (
        Reflection.query.count(),
        LocationProgress.query.count(),
        TrialAttempt.query.count(),
        QuizAttempt.query.count(),
    )
    assert before == after


def test_journal_does_not_unlock_or_change_progress(client, user_factory, login):
    """A filled or empty Journal has no bearing on progression: the user's passed set
    and best scores are exactly what they were, before and after viewing."""
    loc = REFLECTABLE[0]
    user = user_factory(passed=(loc,))
    login(user)
    _seal(client, loc, "No unlock from this.")

    lp = LocationProgress.query.filter_by(user_id=user.id, location=loc).one()
    passed_before, score_before = lp.passed, lp.best_score

    client.get("/journal")

    db.session.refresh(lp)
    assert lp.passed == passed_before
    assert lp.best_score == score_before
    # No new location was unlocked/passed by sealing or viewing.
    assert LocationProgress.query.filter_by(user_id=user.id, passed=True).count() == 1
