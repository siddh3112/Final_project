from datetime import datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..prefs import mark_seen, seen_flags, set_prefs

from ..game_content import (
    CINEMATIC_LINES,
    GAME_INTRO_STEPS,
    LOCATION_ORDER,
    LOCATIONS,
    QUIZZES,
    REFLECTION_PROMPTS,
    build_library_shelves,
    get_hooks,
    get_questions_by_keys,
    grade_quiz,
    select_trial_questions,
)
from ..eval_content import POST_TEST
from ..models import (
    BookRead,
    GameSession,
    KnowledgeTest,
    LocationProgress,
    NpcInteraction,
    QuizAttempt,
    Reflection,
    db,
)
from ..services.achievements import (
    ACH_BY_KEY,
    earned_map,
    grant_new,
)
from ..services.gamification import gamification_summary
from ..services.leaderboard import run_stats, user_runs
from ..services.progress import (
    all_passed,
    get_or_create_open_session,
    get_or_create_progress,
    is_unlocked,
    progress_map,
)

game_bp = Blueprint("game", __name__)


# ── Per-user reading progress (which content volumes a user has studied) ──
# Stored in the book_reads table (keyed by user) so it survives logins and
# leaving a location for its Trial never wipes the Knowledge Core / Concept
# Deck. Progress/presentation state, NOT a research measure — never scored.
def library_read_ids(key):
    rows = BookRead.query.filter_by(user_id=current_user.id, location=key).all()
    return [r.book_id for r in rows]


def mark_book_read(key, book_id):
    if book_id:
        exists = BookRead.query.filter_by(
            user_id=current_user.id, location=key, book_id=book_id
        ).first()
        if exists is None:
            db.session.add(
                BookRead(user_id=current_user.id, location=key, book_id=book_id)
            )
            try:
                db.session.commit()
            except Exception:  # unique-constraint race: the row already exists
                db.session.rollback()
    return library_read_ids(key)


def explore_valid_ids(loc):
    """Valid explored-item ids for a location (books / sectors / stars), used to
    reject unknown ids. Presentation-progress only — mirrors the Library's book
    validation. Sectors = one per AI-Lab learn card; stars = the 5 Observatory
    constellation points."""
    interaction = loc.get("interaction")
    if interaction == "bookshelf":
        return {b.get("id") for b in loc.get("books", [])}
    if interaction == "terminal":
        return {"sector-%d" % i for i in range(len(loc.get("learn_cards", [])))}
    if interaction == "constellation":
        return {"star-%d" % i for i in range(5)}
    if interaction == "timeline":
        return {"beat-%d" % i for i in range(len(loc.get("beats", [])))}
    return set()


@game_bp.route("/")
@login_required
def hub():
    grant_new(current_user)  # keep the achievements table consistent

    # First-visit instructions (opening cinematic + how-to-play) show once PER
    # USER, not per browser — so each participant is instructed exactly once,
    # even on a shared machine. Flip the flag the first time the hub renders.
    show_intro = not current_user.seen_intro
    if show_intro:
        current_user.seen_intro = True
        db.session.commit()

    pmap = progress_map(current_user)
    # The Final Assessment pin is clickable whenever it's unlocked (all three
    # locations passed). If already done, re-entry shows the completed RESULTS
    # (not a fresh test) — the GET /eval/post-test route decides. The pin still
    # renders its 'passed' 🏆 state once post_test_done is True.
    show_post_test = all_passed(current_user)
    new_keys = session.pop("atlas_new_achievements", [])
    new_achievements = [ACH_BY_KEY[k] for k in new_keys if k in ACH_BY_KEY]

    stats = gamification_summary(current_user)
    badge_detail = _badge_detail(current_user, pmap, stats)

    # Living-map state for the reveal layer (READ-ONLY snapshot of data already
    # computed above — no new queries, no writes, purely presentational).
    seen = seen_flags()
    hub_state = {
        "zones": {
            k: {"passed": pmap[k]["passed"], "unlocked": pmap[k]["unlocked"]}
            for k in LOCATION_ORDER
        },
        "final": {
            "unlocked": bool(show_post_test or current_user.post_test_done),
            "done": bool(current_user.post_test_done),
        },
        "seen": seen,
    }

    return render_template(
        "game/hub.html",
        locations=LOCATIONS,
        order=LOCATION_ORDER,
        pmap=pmap,
        show_post_test=show_post_test,
        post_test_done=current_user.post_test_done,
        stats=stats,
        badge_detail=badge_detail,
        game_steps=GAME_INTRO_STEPS,
        cine_lines=CINEMATIC_LINES,
        show_intro=show_intro,
        seen=seen,
        hub_state=hub_state,
        new_achievement_keys=new_keys,
        new_achievements=new_achievements,
        runs=user_runs(current_user),
        run_stats=run_stats(current_user),
    )


# Maps each location-completion badge to its location key.
_BADGE_LOCATION = {"first_steps": "library", "chronicler": "chronicle", "field_researcher": "ai_lab", "stargazer": "observatory"}


def _badge_detail(user, pmap, stats):
    """Read-only detail for each EARNED badge, keyed by achievement_key.

    Assembles already-stored data (location_progress, quiz_attempts,
    knowledge_tests, gamification) for the hub's badge cards. Locked badges are
    intentionally omitted. Nothing is written or recomputed here.
    """
    em = earned_map(user)
    detail = {}

    def meta(key):
        a = ACH_BY_KEY.get(key, {})
        return {"name": a.get("name"), "icon": a.get("icon"), "desc": a.get("desc")}

    # Location-completion badges → that Trial's best score + attempts.
    for bkey, lkey in _BADGE_LOCATION.items():
        if bkey in em:
            p = pmap[lkey]
            d = meta(bkey)
            d.update({
                "kind": "location",
                "location": LOCATIONS[lkey]["name"],
                "score": p["best_score"], "max": 4,
                "attempts": p["attempts_count"],
                "perfect": p["best_score"] >= 4,
            })
            detail[bkey] = d

    # Atlas Sage → post-test score + rank reached.
    if "atlas_sage" in em:
        kt = (KnowledgeTest.query.filter_by(user_id=user.id)
              .order_by(KnowledgeTest.id.desc()).first())
        d = meta("atlas_sage")
        d.update({
            "kind": "atlas_sage",
            "score": kt.score if kt else 0, "max": len(POST_TEST),
            "perfect": bool(kt and kt.score >= len(POST_TEST)),
            "rank": stats.get("rank"),
        })
        detail["atlas_sage"] = d

    return detail


@game_bp.route("/prefs", methods=["POST"])
@login_required
def save_prefs():
    """Persist front-of-house presentation prefs to the session (audio /
    accessibility only — never anything that affects scoring or research data)."""
    data = request.get_json(silent=True) or {}
    return jsonify({"ok": True, "prefs": set_prefs(data)})


@game_bp.route("/seen", methods=["POST"])
@login_required
def save_seen():
    """Mark one-time hub reveals (cinematic, fog recede, path draw, pin ignite)
    as played. Session-only presentation state — never research data."""
    data = request.get_json(silent=True) or {}
    return jsonify({"ok": True, "seen": mark_seen(data.get("flags"))})


@game_bp.route("/location/<key>")
@login_required
def location(key):
    loc = LOCATIONS.get(key)
    if loc is None:
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))
    if loc.get("stub", False):
        return render_template("game/coming_soon.html", loc=loc)

    # Ensure a progress row + an open game session exist for logging.
    lp = get_or_create_progress(current_user, key)
    get_or_create_open_session(current_user, key)

    quiz = QUIZZES.get(key, [])
    interaction = loc.get("interaction")

    hooks = get_hooks(key)  # guess-first priming beats (never logged/graded)

    if interaction == "terminal":
        # The terminal embeds the graded Trial: pick this attempt's questions
        # (pinning the sorting diagnostic) and remember exactly what was shown.
        shown_keys = select_trial_questions(key)
        session[f"shown_{key}"] = shown_keys
        quiz = get_questions_by_keys(key, shown_keys)
        return render_template(
            "game/terminal.html", loc=loc, quiz=quiz, shown_keys=shown_keys,
            hooks=hooks, explored=library_read_ids(key), lab_passed=bool(lp.passed),
        )

    if interaction == "constellation":
        return render_template(
            "game/observatory.html", loc=loc, quiz=quiz, hooks=hooks,
            explored=library_read_ids(key),
        )

    if interaction == "timeline":
        return render_template(
            "game/timeline.html", loc=loc, quiz=quiz, hooks=hooks,
            explored=library_read_ids(key),
        )

    shelves = None
    books = None
    read_books = []
    if interaction == "bookshelf":
        books = loc.get("books", [])
        shelves = build_library_shelves(books)
        read_books = library_read_ids(key)
    return render_template(
        "game/location.html", loc=loc, quiz=quiz, shelves=shelves, books=books,
        read_books=read_books, hooks=hooks,
    )


@game_bp.route("/location/<key>/read", methods=["POST"])
@login_required
def mark_read(key):
    """Record that the user has studied one content volume (book) in this
    location, so their reading progress survives navigation. Presentation/
    progress only — never scoring or research data."""
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("interaction") != "bookshelf":
        abort(404)
    data = request.get_json(silent=True) or {}
    book_id = str(data.get("book", ""))
    valid = {b.get("id") for b in loc.get("books", [])}
    if book_id in valid:
        ids = mark_book_read(key, book_id)
    else:
        ids = library_read_ids(key)
    return jsonify({"ok": True, "read": ids})


@game_bp.route("/location/<key>/progress", methods=["POST"])
@login_required
def mark_progress(key):
    """Persist one explored item (AI-Lab sector / Observatory star) so exploration
    survives navigation — mirrors /read for the Library and reuses the same
    per-user BookRead store. Presentation/progress only: never scoring, Trial
    grading, or research data. Unknown ids are rejected."""
    loc = LOCATIONS.get(key)
    if loc is None:
        abort(404)
    data = request.get_json(silent=True) or {}
    item_id = str(data.get("item", ""))
    if item_id in explore_valid_ids(loc):
        ids = mark_book_read(key, item_id)
    else:
        ids = library_read_ids(key)
    return jsonify({"ok": True, "explored": ids})


@game_bp.route("/location/<key>/trial")
@login_required
def trial(key):
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("stub", False):
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))
    # Terminal locations embed their Trial in the scene itself (with the pinned
    # sorting diagnostic) — the generic trial page would bypass it.
    if loc.get("interaction") == "terminal":
        return redirect(url_for("game.location", key=key))
    # Draw this attempt's questions at random and remember what was shown so the
    # graded set == the shown set (see submit_quiz).
    shown_keys = select_trial_questions(key)
    session[f"shown_{key}"] = shown_keys
    quiz = get_questions_by_keys(key, shown_keys)
    return render_template("game/trial.html", loc=loc, quiz=quiz, shown_keys=shown_keys)


@game_bp.route("/location/<key>/submit", methods=["POST"])
@login_required
def submit_quiz(key):
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("stub", False):
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))

    # Grade only the questions this attempt actually showed. Prefer the hidden
    # field posted with the form (authoritative for this exact page), then the
    # session record. If BOTH are missing (expired session / crafted POST) the
    # attempt cannot be graded faithfully — never fall back to the whole bank,
    # because the graded set must always equal the shown set.
    bank_keys = [q["key"] for q in QUIZZES.get(key, [])]
    shown_raw = request.form.get("shown_keys", "")
    shown_keys = [k for k in shown_raw.split(",") if k in bank_keys]
    if not shown_keys:
        shown_keys = [k for k in session.get(f"shown_{key}", []) if k in bank_keys]
    if not shown_keys:
        flash("That attempt expired — here is a fresh Trial.", "warning")
        return redirect(url_for("game.location", key=key))

    quiz = get_questions_by_keys(key, shown_keys)
    submitted = {q["key"]: request.form.get(q["key"]) for q in quiz}
    results, score, total, passed = grade_quiz(key, submitted, shown_keys=shown_keys)

    lp = get_or_create_progress(current_user, key)
    attempt_number = lp.attempts_count + 1

    # Which questions the user took a Professor Atlas hint on (per-question).
    consulted_raw = request.form.get("consulted", "")
    consulted = {c for c in consulted_raw.split(",") if c}

    # One quiz_attempts row per question.
    for q in quiz:
        selected = submitted.get(q["key"])
        db.session.add(
            QuizAttempt(
                user_id=current_user.id,
                location=key,
                question_key=q["key"],
                selected_answer=selected,
                is_correct=(selected == q["correct"]),
                attempt_number=attempt_number,
                npc_consulted=(q["key"] in consulted),
            )
        )

    # Update progress.
    lp.attempts_count = attempt_number
    if score > lp.best_score:
        lp.best_score = score
    if passed:
        lp.passed = True

    # Close the open time-on-task session(s) for this location so
    # game_sessions.ended_at is actually recorded.
    now = datetime.utcnow()
    for gs in GameSession.query.filter_by(
        user_id=current_user.id, location=key, ended_at=None
    ).all():
        gs.ended_at = now

    db.session.commit()

    # Grant any newly-earned achievements; the hub celebrates them on return.
    session["atlas_new_achievements"] = grant_new(current_user)

    # Post-Trial reflection (generative learning): offer it on a PASS, but only
    # if this user hasn't already answered a real (non-skipped) one here. This
    # is additive qualitative data — it never affects grading or progression.
    reflection_prompt = None
    if passed:
        prompt = REFLECTION_PROMPTS.get(key)
        if prompt:
            answered = Reflection.query.filter_by(
                user_id=current_user.id, location=key, skipped=False
            ).first()
            if answered is None:
                reflection_prompt = prompt

    return render_template(
        "game/results.html",
        loc=loc,
        results=results,
        score=score,
        total=total,
        passed=passed,
        reflection_prompt=reflection_prompt,
    )


@game_bp.route("/location/<key>/reflect", methods=["POST"])
@login_required
def reflect(key):
    """Save a post-Trial reflection (ungraded qualitative data). Submit saves the
    learner's sentence; Skip saves an empty, skipped=True row (skip-rate is data).
    Never affects scoring, progression, XP, or any existing measure."""
    loc = LOCATIONS.get(key)
    prompt = REFLECTION_PROMPTS.get(key)
    if loc is None or prompt is None:
        abort(404)

    # Reflections are only offered after a PASS — never accept one out-of-band.
    lp = LocationProgress.query.filter_by(
        user_id=current_user.id, location=key, passed=True
    ).first()
    if lp is None:
        abort(403)

    # Never overwrite / duplicate a real reflection already on record here.
    answered = Reflection.query.filter_by(
        user_id=current_user.id, location=key, skipped=False
    ).first()
    if answered is not None:
        return jsonify({"ok": True, "duplicate": True})

    data = request.get_json(silent=True) or {}
    text = (data.get("response") or "").strip()[:280]
    skipped = bool(data.get("skipped")) or not text

    db.session.add(
        Reflection(
            user_id=current_user.id,
            location=key,
            prompt_key=prompt["key"],
            prompt_text=prompt["text"],
            response_text="" if skipped else text,
            skipped=skipped,
        )
    )
    db.session.commit()
    return jsonify({"ok": True, "skipped": skipped})
