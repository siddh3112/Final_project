import json
import secrets
from datetime import datetime

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..prefs import mark_seen, seen_flags, set_prefs

from ..game_content import (
    BIN_IDS,
    CINEMATIC_LINES,
    DATA_BINS,
    GAME_INTRO_STEPS,
    LOCATION_ORDER,
    LOCATIONS,
    QUIZZES,
    REFLECTION_PROMPTS,
    TRIAL_COUNT,
    build_library_shelves,
    get_hooks,
    get_questions_by_keys,
    grade_quiz,
    lexicon_pool,
    lexicon_pool_sids,
    normalize_order,
    order_canonical,
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
    TrialAttempt,
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
    validation. Sectors = one per AI-Lab learn card; stars = one per Observatory
    constellation star (authored 1:1 with the hooks, currently 10)."""
    interaction = loc.get("interaction")
    if interaction == "bookshelf":
        return {b.get("id") for b in loc.get("books", [])}
    if interaction == "terminal":
        return {"sector-%d" % i for i in range(len(loc.get("learn_cards", [])))}
    if interaction == "constellation":
        # The Observatory renders one constellation star per guess-first hook
        # (hooks are authored 1:1 with the stars — see HOOKS["observatory"] and
        # observatory.js OBS_HOOKS[i]). Derive the count from that server-side
        # content list so the accepted ids (star-0 … star-N-1) always match the
        # real number of stars — the same way terminal/timeline derive theirs
        # from learn_cards / beats, never a hardcoded number.
        return {"star-%d" % i for i in range(len(get_hooks(loc.get("key", ""))))}
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
    # The Final Assessment pin is clickable whenever it's unlocked (all four
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

    # Atlas Sage → post-test score + rank reached. Read the FIRST (authoritative,
    # single-attempt) KnowledgeTest with id.asc(), matching results/certificate.
    if "atlas_sage" in em:
        kt = (KnowledgeTest.query.filter_by(user_id=user.id)
              .order_by(KnowledgeTest.id.asc()).first())
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
        # The terminal embeds the graded Trial. The SERVER draws + stores this
        # attempt's questions; the page gets only the attempt id, never a trusted
        # shown-keys list.
        #
        # REVISIT of a PASSED lab is read-only for the record: a passive reread
        # creates NO TrialAttempt at all (nothing is written). A board attempt is
        # started only for the first-time / not-yet-passed flow, or an explicit
        # "?mode=practice" run (which submit_quiz grades but records nothing).
        want_practice = request.args.get("mode") == "practice"
        if lp.passed and not want_practice:
            return render_template(
                "game/terminal.html", loc=loc, quiz=[], attempt_id="",
                hooks=hooks, explored=library_read_ids(key), lab_passed=True,
                practice=False, data_bins=DATA_BINS,
            )
        aid, quiz = _start_trial_attempt(key)
        return render_template(
            "game/terminal.html", loc=loc, quiz=quiz, attempt_id=aid,
            hooks=hooks, explored=library_read_ids(key), lab_passed=bool(lp.passed),
            practice=bool(lp.passed and want_practice), data_bins=DATA_BINS,
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


# ── Server-authoritative Trial attempts ───────────────────────────────────
# A served Trial attempt is valid for this long; after that a fresh draw is
# required (guards against a stale form being submitted much later).
TRIAL_TTL_SECONDS = 2 * 60 * 60


def _attempt_keys(att):
    try:
        return json.loads(att.question_keys) or []
    except (TypeError, ValueError):
        return []


def _attempt_answers(att):
    try:
        return json.loads(att.answers_json) or {}
    except (TypeError, ValueError):
        return {}


def _start_trial_attempt(key):
    """Begin a Trial attempt SERVER-side and DURABLY. The server chooses the
    TRIAL_COUNT unique question keys and stores them in a `TrialAttempt` DB row
    (status 'open') under a fresh random opaque token. The browser is given ONLY
    that token — never a trusted list of which questions to grade, and never the
    answer key. Returns (token, quiz dicts to render)."""
    keys = list(dict.fromkeys(select_trial_questions(key)))[:TRIAL_COUNT]
    token = secrets.token_urlsafe(16)
    att = TrialAttempt(
        token=token,
        user_id=current_user.id,
        location=key,
        question_keys=json.dumps(keys),
        answers_json="{}",
        status="open",
        started_at=datetime.utcnow(),
    )
    db.session.add(att)
    db.session.commit()
    return token, get_questions_by_keys(key, keys)


def _load_trial_attempt(key, token):
    """Return (TrialAttempt, None) for a valid 'open', unexpired attempt that
    belongs to THIS user + location and whose stored key-set is exactly
    TRIAL_COUNT unique known keys; otherwise (None, reason). Loads the durable DB
    row by its opaque token — never trusts anything the browser says about WHICH
    questions were shown."""
    if not token:
        return None, "invalid"
    att = TrialAttempt.query.filter_by(token=token).first()
    if att is None or att.user_id != current_user.id or att.location != key:
        return None, "invalid"
    if att.status != "open":
        return None, att.status  # 'submitted' (replay) or 'expired'
    if (datetime.utcnow() - (att.started_at or datetime.utcnow())).total_seconds() > TRIAL_TTL_SECONDS:
        att.status = "expired"
        db.session.commit()
        return None, "expired"
    keys = _attempt_keys(att)
    bank = {q["key"] for q in QUIZZES.get(key, [])}
    if len(keys) != TRIAL_COUNT or len(set(keys)) != TRIAL_COUNT or not set(keys) <= bank:
        return None, "corrupt"
    return att, None


@game_bp.route("/location/<key>/answer", methods=["POST"])
@login_required
def commit_answer(key):
    """Commit ONE Trial answer and return its correctness + elaborative feedback.

    This is how instant feedback works WITHOUT the answer key in the DOM: the
    page ships no `data-correct`; the client asks the server. The FIRST letter
    committed for a question is recorded server-side and locked — later calls
    (or a throwaway letter fished for the answer) return that same recorded
    answer, so this can't be used as an answer oracle. submit_quiz grades from
    these recorded answers."""
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("stub", False):
        abort(404)
    if not is_unlocked(current_user, key):
        return jsonify({"error": "locked"}), 403
    data = request.get_json(silent=True) or {}
    att, err = _load_trial_attempt(key, data.get("attempt_id", ""))
    qkey = data.get("qkey", "")
    if att is None or qkey not in _attempt_keys(att):
        return jsonify({"error": err or "invalid"}), 400
    q = get_questions_by_keys(key, [qkey])
    if not q:
        return jsonify({"error": "unknown-question"}), 400
    q = q[0]
    answers = _attempt_answers(att)

    # Ordering item ("Broken Timeline"): the payload is a sequence of event ids.
    # Validate it names EXACTLY this item's events (unique, complete) — else reject
    # (400), never score it. The correct sequence is revealed only in THIS response,
    # after the first commit is locked, never in the page the learner starts from.
    if q.get("kind") == "order":
        norm = normalize_order(data.get("order", ""), q)
        if norm is None:
            return jsonify({"error": "bad-order"}), 400
        if qkey not in answers:                 # record only the FIRST commit
            answers[qkey] = norm
            att.answers_json = json.dumps(answers)
            db.session.commit()
        committed = answers[qkey]
        correct = order_canonical(q)
        is_correct = committed == correct
        feedback = (q.get("feedback_correct") if is_correct else q.get("feedback_wrong")) or q.get("explanation", "")
        return jsonify({
            "is_correct": is_correct,
            "correct_order": correct,
            "committed": committed,
            "feedback": feedback,
        })

    if q.get("kind") in ("sort", "matching"):
        # The sorting board and the Lexicon matching board both commit at SUBMIT
        # (not per-item), so /answer is not part of their flow. Reject a stray commit.
        return jsonify({"error": "not-committable"}), 400

    letter = data.get("letter", "")
    if letter not in q["options"]:
        return jsonify({"error": "bad-option"}), 400
    if qkey not in answers:                     # record only the FIRST commit
        answers[qkey] = letter
        att.answers_json = json.dumps(answers)
        db.session.commit()
    committed = answers[qkey]
    is_correct = committed == q["correct"]
    feedback = (q.get("feedback_correct") if is_correct else q.get("feedback_wrong")) or q.get("explanation", "")
    return jsonify({
        "is_correct": is_correct,
        "correct": q["correct"],
        "committed": committed,
        "feedback": feedback,
    })


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
    # The SERVER draws + stores this attempt's questions; the page gets only the
    # attempt id (see _start_trial_attempt / submit_quiz).
    aid, quiz = _start_trial_attempt(key)
    # For a Lexicon matching board, also build the scenario pool (4 correct + 2
    # deterministic decoys). The pool is derived from the stored concept keys, so
    # grading re-derives it identically; the template shuffles it for display.
    scenarios = None
    if quiz and quiz[0].get("kind") == "matching":
        scenarios = lexicon_pool(key, [q["key"] for q in quiz])
    return render_template(
        "game/trial.html", loc=loc, quiz=quiz, attempt_id=aid, scenarios=scenarios
    )


@game_bp.route("/location/<key>/submit", methods=["POST"])
@login_required
def submit_quiz(key):
    loc = LOCATIONS.get(key)
    if loc is None or loc.get("stub", False):
        abort(404)
    if not is_unlocked(current_user, key):
        return redirect(url_for("game.hub"))

    # SERVER-AUTHORITATIVE grading. The browser sends only an attempt id; the
    # graded set is the exact TRIAL_COUNT unique keys the server stored for that
    # attempt. Any browser-provided question list is ignored — so forged or
    # duplicated keys (e.g. lib_s1×4) cannot be graded, and a replayed/expired
    # attempt is refused. See _start_trial_attempt / _load_trial_attempt.
    fresh = url_for(
        "game.location" if loc.get("interaction") == "terminal" else "game.trial",
        key=key,
    )
    att, err = _load_trial_attempt(key, request.form.get("attempt_id", ""))
    if att is None:
        flash("That Trial attempt has expired or was already submitted — here is a fresh Trial.", "warning")
        return redirect(fresh)

    stored_keys = _attempt_keys(att)
    quiz = get_questions_by_keys(key, stored_keys)

    # Lexicon board: the legal scenario ids are re-derived from the stored concept
    # keys (same deterministic pool as at render), so a forged/off-pool id can't score.
    matching_pool_sids = (
        lexicon_pool_sids(key, stored_keys) if quiz and quiz[0].get("kind") == "matching" else set()
    )

    # The FIRST answer committed per question (recorded server-side via
    # /answer) is authoritative; fall back to a validated form value only for a
    # question that was never committed (e.g. JavaScript disabled). Anything that
    # isn't one of THAT question's option letters is treated as unanswered.
    recorded = _attempt_answers(att)
    submitted = {}
    for q in quiz:
        if q.get("kind") == "order":
            # Ordering item: the server-recorded first commit is authoritative;
            # fall back to a validated form value only if none was committed. A
            # malformed sequence normalises to None → graded wrong, never a point.
            val = normalize_order(recorded.get(q["key"]), q)
            if val is None:
                val = normalize_order(request.form.get(q["key"]), q)
        elif q.get("kind") == "sort":
            # Sorting board: the placement is a bin id from the form (the board
            # commits at submit, not per-drag). Server-authoritative: only a bin id
            # that is one of the served bins counts; anything else (unknown bin,
            # missing, forged) is treated as unplaced → graded wrong, never a point.
            fv = request.form.get(q["key"])
            val = fv if fv in BIN_IDS else None
        elif q.get("kind") == "matching":
            # Lexicon board: the inked link is a scenario id from the form. Only a
            # scenario id from THIS attempt's served pool counts; an unknown id (or a
            # scenario reused for the wrong concept) is graded wrong, never a point.
            # Independent per concept — each concept's correct scenario is its own.
            fv = request.form.get(q["key"])
            val = fv if fv in matching_pool_sids else None
        else:
            val = recorded.get(q["key"])
            if val not in q["options"]:
                fv = request.form.get(q["key"])
                val = fv if fv in q["options"] else None
        submitted[q["key"]] = val
    results, score, total, passed = grade_quiz(key, submitted, shown_keys=stored_keys)

    lp = get_or_create_progress(current_user, key)

    # ── PRACTICE REPLAY: a Trial the learner has ALREADY passed is replayable for
    # practice, but READ-ONLY for the record. Grade it and show feedback, but write
    # NOTHING: no QuizAttempt, no attempts_count/best_score change, no run_history,
    # no achievements, no GameSession close, and no TrialAttempt left behind (the
    # transient attempt is deleted). First-time flow, and a not-yet-passed retry
    # BEFORE the first pass, are recorded exactly once by the branch below. ──
    if lp.passed:
        db.session.delete(att)      # transient attempt: leave nothing persisted
        db.session.commit()
        return render_template(
            "game/results.html", loc=loc, results=results, score=score,
            total=total, passed=passed, reflection_prompt=None, practice=True,
        )

    # One grading per attempt (durable) — flip 'open' -> 'submitted' so a replayed
    # POST is refused, and record the outcome on the attempt row.
    att.status = "submitted"
    att.score = score
    att.passed = passed
    att.submitted_at = datetime.utcnow()

    attempt_number = lp.attempts_count + 1

    # Which questions the user took a Professor Atlas hint on (per-question).
    consulted_raw = request.form.get("consulted", "")
    consulted = {c for c in consulted_raw.split(",") if c}

    # One quiz_attempts row per question. is_correct comes from the SHARED grading
    # core (grade_quiz results) so MCQ and ordering items score by one rule.
    result_by_key = {r["key"]: r for r in results}
    for q in quiz:
        selected = submitted.get(q["key"])
        db.session.add(
            QuizAttempt(
                user_id=current_user.id,
                location=key,
                question_key=q["key"],
                selected_answer=selected,
                is_correct=bool(result_by_key.get(q["key"], {}).get("is_correct")),
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
        practice=False,
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

    # Professor Atlas replies ONCE to a real reflection, generated here (a write
    # endpoint) and stored on the row so the Journal only ever reads it. Guarded so a
    # generation failure never blocks sealing; a skipped reflection gets no reply.
    atlas_response = None
    atlas_source = None
    if not skipped:
        try:
            from ..services.npc_service import reflect_response
            atlas_response, atlas_source = reflect_response(
                key, prompt["text"], text,
                ollama_enabled=current_app.config.get("OLLAMA_ENABLED", False),
            )
        except Exception:
            atlas_response, atlas_source = None, None

    db.session.add(
        Reflection(
            user_id=current_user.id,
            location=key,
            prompt_key=prompt["key"],
            prompt_text=prompt["text"],
            response_text="" if skipped else text,
            skipped=skipped,
            atlas_response=atlas_response,
            atlas_source=atlas_source,
        )
    )
    db.session.commit()
    return jsonify({"ok": True, "skipped": skipped})


@game_bp.route("/journal")
@login_required
def journal():
    """The Journal: a READ-ONLY archive of the learner's own sealed reflections, one
    slot per location that offers a reflection.

    Purely presentational. It reads reflections and location metadata and writes
    nothing: it never grades, unlocks, scores, or changes progression, and whether a
    slot is filled has no bearing on any of those. Locations not yet reflected on
    show as empty slots, so the set visibly fills as thoughts are sealed. N (the
    denominator) is DERIVED from the prompt-bearing locations, never hardcoded."""
    # One real (non-skipped) reflection per location; the reflect route dedups, but
    # if any dup exists the most recent wins.
    rows = (
        Reflection.query
        .filter_by(user_id=current_user.id, skipped=False)
        .order_by(Reflection.created_at.asc())
        .all()
    )
    by_loc = {r.location: r for r in rows}

    entries = []
    for key in LOCATION_ORDER:
        prompt = REFLECTION_PROMPTS.get(key)
        if not prompt:
            continue  # only locations that actually offer a reflection are slots
        loc = LOCATIONS[key]
        r = by_loc.get(key)
        source_label = None
        if r is not None and r.atlas_source:
            source_label = "Granite generated" if r.atlas_source == "granite" else "System generated"
        entries.append({
            "key": key,
            "name": loc["name"],
            "accent": loc["accent"],
            "theme": loc.get("theme"),
            "prompt": prompt["text"],
            "sealed": r is not None,
            "response_text": r.response_text if r is not None else None,
            "sealed_at": r.created_at if r is not None else None,
            "atlas_response": r.atlas_response if r is not None else None,
            "atlas_source_label": source_label,
        })

    sealed_count = sum(1 for e in entries if e["sealed"])
    total = len(entries)  # N derived from prompt-bearing locations

    return render_template(
        "game/journal.html",
        entries=entries,
        sealed_count=sealed_count,
        total=total,
    )
