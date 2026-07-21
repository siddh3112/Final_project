import json
import re
from datetime import datetime
from io import BytesIO

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..eval_content import CHAPTER_TITLES, EPILOGUE_LINES, POST_TEST, POST_TEST_PASS
from ..models import GameSession, KnowledgeTest, db
from ..services.achievements import grant_new
from ..services.gamification import XP_PER_POSTTEST_CORRECT, gamification_summary
from ..services.leaderboard import record_run, run_stats
from ..services.progress import all_passed, get_or_create_open_session, progress_map

eval_bp = Blueprint("eval", __name__, url_prefix="/eval")

# Server-side pseudo-location key for the Final Assessment's timing session. It is
# NOT a real game location (absent from LOCATION_ORDER), so it never affects
# progress/unlock — it exists only to server-stamp the assessment's start/submit
# times so the recorded duration is authoritative, not browser-supplied.
ASSESSMENT_KEY = "assessment"


def _server_assessment_seconds(user):
    """Server-authoritative assessment duration, in seconds.

    Closes the open server-stamped assessment session(s) for this user and returns
    the elapsed time from the EARLIEST start to now. Returns None if the assessment
    was never opened via GET (e.g. a direct POST) — a duration is never fabricated,
    and browser-supplied timing is never consulted."""
    now = datetime.utcnow()
    sessions = GameSession.query.filter_by(
        user_id=user.id, location=ASSESSMENT_KEY, ended_at=None
    ).all()
    if not sessions:
        return None
    start = min((s.started_at or now) for s in sessions)
    for s in sessions:
        s.ended_at = now
    return max(0, int((now - start).total_seconds()))


def _assessment_completed(user):
    """The graded Final Assessment is a ONE-shot research measure. It counts as
    COMPLETED the moment the user's FIRST KnowledgeTest exists — pass OR fail —
    after which the graded test is CLOSED: no resubmit, no fresh test, no retake.

    This is deliberately distinct from user.post_test_done, which means the user
    PASSED (>= POST_TEST_PASS). Completion gates the single attempt; passing only
    controls the certificate / Atlas Sage / journey-complete rewards."""
    return KnowledgeTest.query.filter_by(user_id=user.id).first() is not None


def _chapters():
    """Group POST_TEST into ordered chapters for the cinematic flow.

    Display order only — scoring reads answers by question key, so grouping and
    ordering here never affect what is scored.
    """
    chapters = []
    for num in sorted(CHAPTER_TITLES):
        qs = [q for q in POST_TEST if q.get("chapter") == num]
        if qs:
            chapters.append({"num": num, "title": CHAPTER_TITLES[num], "questions": qs})
    return chapters


def _review_from_answers(answers):
    """Rebuild the per-question review list from stored answers (display only)."""
    review = []
    for q in POST_TEST:
        selected = answers.get(q["key"])
        review.append(
            {
                "chapter": q.get("chapter"),
                "question": q["question"],
                "options": q["options"],
                "selected": selected,
                "correct": q["correct"],
                "is_correct": selected == q["correct"],
                "explanation": q.get("explanation", ""),
            }
        )
    return review


def _render_completed_results():
    """Render the RESULTS page for the user's latest completed attempt, rebuilt
    from the stored KnowledgeTest — READ-ONLY (no new KnowledgeTest, no new
    run_history, no scoring). Returns None if there is no attempt to show."""
    kt = (
        KnowledgeTest.query.filter_by(user_id=current_user.id)
        .order_by(KnowledgeTest.id.asc())  # the FIRST (only) graded attempt is authoritative
        .first()
    )
    if kt is None:
        return None
    try:
        answers = json.loads(kt.answers_json or "{}")
    except (TypeError, ValueError):
        answers = {}
    score = kt.score
    stats = gamification_summary(current_user)
    best = run_stats(current_user).get("best_score")
    return render_template(
        "eval/post_test_done.html",
        score=score,
        total=len(POST_TEST),
        passed=score >= POST_TEST_PASS,
        pass_mark=POST_TEST_PASS,
        xp_per_correct=XP_PER_POSTTEST_CORRECT,
        xp_gained=score * XP_PER_POSTTEST_CORRECT,
        stats=stats,
        review=_review_from_answers(answers),
        seal_date=kt.created_at.strftime("%d %B %Y"),
        combined_score=best or 0,
        is_personal_best=False,
        personal_best=best,
        epilogue_lines=EPILOGUE_LINES,
        epi_auto=False,            # re-entry never auto-replays the ending
        journey_complete=bool(stats.get("journey_complete")),
        epi_standalone=False,
        is_review=True,            # re-entry / completed state (adds Retake, no PB line)
    )


def _run_recorded(user):
    """Has the CURRENT run already produced its gamified score?"""
    from ..models import RunHistory
    return RunHistory.query.filter_by(
        user_id=user.id, run_number=user.current_run or 1
    ).first() is not None


def _assessment_closed(user):
    """Is the Final Assessment closed for the run the learner is currently on?

    Run 1 keeps the ORIGINAL research gate untouched: the moment a KnowledgeTest
    exists (pass or fail) the measured attempt is over and can never be retaken.

    Run 2+ is a replay, which produces only a gamified RunHistory score, so it is
    closed once that run has been scored. This is what lets a learner play the
    whole journey again without ever reopening the research measure.
    """
    if (user.current_run or 1) == 1:
        return _assessment_completed(user)
    return _run_recorded(user)


@eval_bp.route("/post-test")
@login_required
def post_test():
    # Gated: only after all locations are passed.
    if not all_passed(current_user):
        return redirect(url_for("game.hub"))
    # SINGLE-ATTEMPT (run 1): once the graded assessment is completed (an attempt
    # exists, pass OR fail) it is CLOSED. Re-entering ALWAYS shows the recorded
    # results — never a fresh blank test. There is no retake of the graded measure.
    # On a replay run this instead means "this run is already scored".
    if _assessment_closed(current_user):
        results = _render_completed_results()
        if results is not None:
            return results
        # No stored attempt (shouldn't happen) → fall through to a fresh test.
    # Server-stamp the assessment START so timing is server-authoritative (not
    # browser-supplied). Reuses an open session on re-entry, so the start time
    # stays fixed at the first view; it is closed and measured on submit.
    get_or_create_open_session(current_user, ASSESSMENT_KEY)
    return render_template(
        "eval/post_test.html",
        chapters=_chapters(),
        total=len(POST_TEST),
        pass_mark=POST_TEST_PASS,
    )


@eval_bp.route("/post-test/submit", methods=["POST"])
@login_required
def submit_post_test():
    if not all_passed(current_user):
        return redirect(url_for("game.hub"))
    # SINGLE-ATTEMPT: reject any submission once the graded assessment is already
    # completed (pass OR fail). The FIRST KnowledgeTest is authoritative and is
    # never overwritten — the user simply sees their existing results.
    if _assessment_closed(current_user):
        results = _render_completed_results()
        return results if results is not None else redirect(url_for("game.hub"))

    # ── Scoring (UNCHANGED) ──
    answers = {}
    score = 0
    for q in POST_TEST:
        selected = request.form.get(q["key"])
        answers[q["key"]] = selected
        if selected == q["correct"]:
            score += 1

    # ── Timing is SERVER-AUTHORITATIVE: measured from the server-stamped start
    # (recorded when GET /eval/post-test rendered the test) to the server's submit
    # time. Any browser-supplied time_spent_seconds is IGNORED for both the score
    # (speed bonus) and the recorded research value — it cannot be forged. ──
    total_time = _server_assessment_seconds(current_user)

    # Optional per-question seconds → stored under a reserved key that scoring
    # never reads (scoring only checks the p1..p10 question keys).
    answers_out = dict(answers)
    # Non-authoritative, client-reported total — kept for reference ONLY; it never
    # feeds the score, the speed bonus, or the recorded duration (all server-side).
    client_raw = request.form.get("time_spent_seconds")
    if client_raw not in (None, ""):
        try:
            answers_out["_client_time_spent_seconds"] = max(0, int(float(client_raw)))
        except (TypeError, ValueError):
            pass
    try:
        pq = json.loads(request.form.get("per_question_seconds") or "{}")
        if isinstance(pq, dict) and pq:
            answers_out["_per_question_seconds"] = {
                k: int(v) for k, v in pq.items() if str(k).startswith("p")
            }
    except (TypeError, ValueError):
        pass

    # ══ RESEARCH DATA — WRITTEN ONCE, ON RUN 1 ONLY ══════════════════════════
    # This is THE measured knowledge record: one row per participant, pass or
    # fail, never overwritten. A replay (current_run >= 2) deliberately writes NO
    # KnowledgeTest at all, so the research value is frozen at the first
    # playthrough while the learner can still improve their leaderboard score.
    # The gamified counterpart is the RunHistory row created further down.
    is_research_run = (current_user.current_run or 1) == 1
    if is_research_run:
        db.session.add(
            KnowledgeTest(
                user_id=current_user.id,
                answers_json=json.dumps(answers_out),
                score=score,
                time_spent_seconds=total_time,
            )
        )
    # Pass requires at least POST_TEST_PASS correct. Only a PASS marks the Final
    # Ascent conquered (journey complete / Atlas Sage / certificate). A fail can
    # be retaken; a prior pass is never revoked.
    passed = score >= POST_TEST_PASS
    if passed:
        current_user.post_test_done = True
    # SINGLE-ATTEMPT at the DB level: if a concurrent double-submit slipped past
    # the check-then-insert guard above, the unique index on
    # knowledge_tests(user_id) rejects the losing racer's row here. Roll back and
    # show the first (authoritative) attempt — so a race can only ever create ONE
    # KnowledgeTest and (since we return before record_run) ONE RunHistory.
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        results = _render_completed_results()
        return results if results is not None else redirect(url_for("game.hub"))

    # Grant the Atlas Sage (and any pending) achievement; hub celebrates it.
    session["atlas_new_achievements"] = grant_new(current_user)

    # ── Presentation context for the cinematic reveal + post-test review ──
    # (does not affect scoring or storage above)
    review = []
    for q in POST_TEST:
        selected = answers.get(q["key"])
        review.append(
            {
                "chapter": q.get("chapter"),
                "question": q["question"],
                "options": q["options"],
                "selected": selected,
                "correct": q["correct"],
                "is_correct": selected == q["correct"],
                "explanation": q.get("explanation", ""),
            }
        )

    stats = gamification_summary(current_user)

    # ── Record this run in the PERSONAL best-runs history (additive) ──
    # Snapshot of already-stored data; never changes scoring/storage above.
    pmap = progress_map(current_user)
    run, is_personal_best, personal_best = record_run(
        current_user,
        post_test_score=score,
        post_test_max=len(POST_TEST),
        library_score=pmap["library"]["best_score"],
        chronicle_score=pmap["chronicle"]["best_score"],
        ai_lab_score=pmap["ai_lab"]["best_score"],
        observatory_score=pmap["observatory"]["best_score"],
        badges_count=stats["badges_earned"],
        time_spent_seconds=total_time,
        xp=stats["xp"],
        rank=stats["rank"],
        # GAMIFIED score for this playthrough. Unlike the KnowledgeTest above,
        # this is written on EVERY completed run, which is what makes the
        # leaderboard replayable without touching the research measure.
        run_number=current_user.current_run or 1,
    )

    # ── Closing cinematic (epilogue): auto-play once, after the reveal, when the
    # journey is now complete and it hasn't been seen this session. Presentation
    # only — never gates or alters progress. ──
    journey_complete = bool(stats.get("journey_complete"))
    # Play the closing cinematic on EVERY passing completion (score >= pass mark),
    # not just the first time — passing the Final Assessment (8/10) always earns
    # the ending. A failing attempt never triggers it.
    epi_auto = passed and journey_complete

    return render_template(
        "eval/post_test_done.html",
        score=score,
        total=len(POST_TEST),
        passed=passed,
        pass_mark=POST_TEST_PASS,
        xp_per_correct=XP_PER_POSTTEST_CORRECT,
        xp_gained=score * XP_PER_POSTTEST_CORRECT,
        stats=stats,
        review=review,
        seal_date=datetime.utcnow().strftime("%d %B %Y"),
        combined_score=run.combined_score,
        is_personal_best=is_personal_best,
        personal_best=personal_best,
        epilogue_lines=EPILOGUE_LINES,
        epi_auto=epi_auto,
        journey_complete=journey_complete,
        epi_standalone=False,
    )


@eval_bp.route("/review")
@login_required
def review():
    """Standalone per-question review of the most recent Final Assessment
    attempt, reached via 'View your review'. Read-only — rebuilt from the
    stored KnowledgeTest answers; nothing is written."""
    kt = (
        KnowledgeTest.query.filter_by(user_id=current_user.id)
        .order_by(KnowledgeTest.id.asc())  # the FIRST (only) graded attempt is authoritative
        .first()
    )
    if kt is None:
        return redirect(url_for("game.hub"))
    try:
        answers = json.loads(kt.answers_json or "{}")
    except (TypeError, ValueError):
        answers = {}

    review = []
    for q in POST_TEST:
        selected = answers.get(q["key"])
        review.append(
            {
                "chapter": q.get("chapter"),
                "question": q["question"],
                "options": q["options"],
                "selected": selected,
                "correct": q["correct"],
                "is_correct": selected == q["correct"],
                "explanation": q.get("explanation", ""),
            }
        )
    score = kt.score
    return render_template(
        "eval/review.html",
        review=review,
        score=score,
        total=len(POST_TEST),
        passed=score >= POST_TEST_PASS,
        pass_mark=POST_TEST_PASS,
    )


@eval_bp.route("/epilogue")
@login_required
def epilogue():
    """Standalone replay of the closing cinematic (Settings → Replay ending).
    Presentation only; only for players who have finished everything."""
    if not (all_passed(current_user) and current_user.post_test_done):
        return redirect(url_for("game.hub"))
    return render_template(
        "eval/epilogue.html",
        epilogue_lines=EPILOGUE_LINES,
        epi_auto=True,
        epi_standalone=True,
    )


@eval_bp.route("/certificate")
@login_required
def certificate():
    """Stream a downloadable PDF completion certificate. READ-ONLY — it only
    reads existing scoring/leaderboard data; nothing is written (no disk, no DB).
    Gated to players who finished the Final Ascent."""
    if not current_user.post_test_done:
        flash("Pass the Final Assessment (8 of 10) to earn your certificate.", "warning")
        return redirect(url_for("game.hub"))

    stats = gamification_summary(current_user)
    kt = (
        KnowledgeTest.query.filter_by(user_id=current_user.id)
        .order_by(KnowledgeTest.id.asc())  # the FIRST (only) graded attempt is authoritative
        .first()
    )
    score = kt.score if kt else 0
    completed_at = kt.created_at if kt else datetime.utcnow()
    mastery = run_stats(current_user).get("best_score")

    try:
        buf = _build_certificate_pdf(
            name=current_user.username,
            rank=stats.get("rank", "Atlas Sage"),
            score=score,
            total=len(POST_TEST),
            badges_earned=stats.get("badges_earned", 0),
            badges_total=stats.get("badges_total", 5),
            mastery=mastery,
            date_str=completed_at.strftime("%d %B %Y"),
        )
    except ImportError:
        # reportlab (in requirements) isn't installed on this host — degrade
        # gracefully instead of a 500. Nothing was written; the user keeps their
        # completion and can retry once the dependency is present.
        flash(
            "Certificate generation is temporarily unavailable on this server. "
            "Your Atlas Sage rank is safe — please try again later.",
            "warning",
        )
        return redirect(url_for("game.hub"))
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", current_user.username).strip("_") or "player"
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Atlas_Quest_Certificate_{safe}.pdf",
    )


def _build_certificate_pdf(*, name, rank, score, total, badges_earned,
                           badges_total, mastery, date_str):
    """Render the certificate to an in-memory PDF (A4 landscape, purple + gold).
    reportlab is imported lazily so the app still boots if it isn't installed."""
    import math

    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    PURPLE = HexColor("#160a30")
    GOLD = HexColor("#f0c96b")
    GOLD_DIM = HexColor("#c9a24b")
    INK = HexColor("#ece8ff")
    MUTED = HexColor("#9c93c4")

    buf = BytesIO()
    W, H = landscape(A4)  # ~841.9 x 595.3 pt
    c = canvas.Canvas(buf, pagesize=(W, H))
    cx = W / 2

    def star(px, py, r, color, inner=0.4):
        c.setFillColor(color)
        p = c.beginPath()
        for k in range(8):
            ang = math.pi / 2 + k * math.pi / 4
            rad = r if k % 2 == 0 else r * inner
            x, y = px + rad * math.cos(ang), py + rad * math.sin(ang)
            (p.moveTo if k == 0 else p.lineTo)(x, y)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    # Background
    c.setFillColor(PURPLE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Gold double-border frame
    c.setStrokeColor(GOLD)
    c.setLineWidth(2.4)
    c.rect(26, 26, W - 52, H - 52, fill=0, stroke=1)
    c.setStrokeColor(GOLD_DIM)
    c.setLineWidth(0.8)
    c.rect(34, 34, W - 68, H - 68, fill=0, stroke=1)

    # Corner star flourishes (just inside the inner frame)
    for fx, fy in ((48, H - 48), (W - 48, H - 48), (48, 48), (W - 48, 48)):
        star(fx, fy, 7, GOLD)

    # Title
    c.setFillColor(GOLD)
    c.setFont("Times-Bold", 32)
    c.drawCentredString(cx, H - 118, "CERTIFICATE OF COMPLETION")
    c.setFillColor(INK)
    c.setFont("Helvetica", 12.5)
    c.drawCentredString(cx, H - 140, "Atlas Quest  —  Introduction to Artificial Intelligence")

    # Divider
    c.setStrokeColor(GOLD_DIM)
    c.setLineWidth(1)
    c.line(cx - 150, H - 156, cx + 150, H - 156)
    star(cx, H - 156, 4.5, GOLD)

    # Body
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 13)
    c.drawCentredString(cx, H - 208, "This certifies that")

    c.setFillColor(INK)
    c.setFont("Times-Bold", 34)
    c.drawCentredString(cx, H - 250, name)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 12.5)
    c.drawCentredString(cx, H - 286, "has journeyed through the four realms and earned the rank of")

    c.setFillColor(GOLD)
    c.setFont("Times-Bold", 27)
    c.drawCentredString(cx, H - 328, (rank or "Atlas Sage").upper())

    # Stats row
    mastery_txt = str(mastery) if mastery is not None else "—"
    stats_line = (
        f"Post-Test Score  {score}/{total}      ·      "
        f"Achievements  {badges_earned}/{badges_total}      ·      "
        f"Mastery Score  {mastery_txt}      ·      {date_str}"
    )
    c.setFillColor(INK)
    c.setFont("Helvetica", 11.5)
    c.drawCentredString(cx, H - 372, stats_line)

    # Gold wax seal (filled circle + ring + star + AQ monogram)
    seal_y = 138
    c.setFillColor(GOLD)
    c.circle(cx, seal_y, 42, fill=1, stroke=0)
    c.setStrokeColor(PURPLE)
    c.setLineWidth(1.4)
    c.circle(cx, seal_y, 34, fill=0, stroke=1)
    star(cx, seal_y + 15, 6, PURPLE)
    c.setFillColor(PURPLE)
    c.setFont("Times-Bold", 22)
    c.drawCentredString(cx, seal_y - 12, "AQ")

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(
        cx, 46,
        "Atlas Quest  ·  MSc project  ·  content adapted from IBM SkillsBuild: Introduction to AI",
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
