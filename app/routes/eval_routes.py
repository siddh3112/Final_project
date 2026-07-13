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

from ..eval_content import CHAPTER_TITLES, EPILOGUE_LINES, POST_TEST, POST_TEST_PASS
from ..models import KnowledgeTest, db
from ..services.achievements import grant_new
from ..services.gamification import XP_PER_POSTTEST_CORRECT, gamification_summary
from ..services.leaderboard import record_run, run_stats
from ..services.progress import all_passed, progress_map

eval_bp = Blueprint("eval", __name__, url_prefix="/eval")


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


@eval_bp.route("/post-test")
@login_required
def post_test():
    # Gated: only after all locations are passed.
    if not all_passed(current_user):
        return redirect(url_for("game.hub"))
    # SINGLE-ATTEMPT: once the graded assessment is completed (an attempt exists,
    # pass OR fail) it is CLOSED. Re-entering ALWAYS shows the recorded results —
    # never a fresh blank test. There is no retake of the graded measure.
    if _assessment_completed(current_user):
        results = _render_completed_results()
        if results is not None:
            return results
        # No stored attempt (shouldn't happen) → fall through to a fresh test.
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
    if _assessment_completed(current_user):
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

    # ── Silent timing telemetry (display-only data; never affects the score) ──
    total_time = None
    try:
        raw = request.form.get("time_spent_seconds")
        if raw not in (None, ""):
            total_time = max(0, int(float(raw)))
    except (TypeError, ValueError):
        total_time = None

    # Optional per-question seconds → stored under a reserved key that scoring
    # never reads (scoring only checks the p1..p10 question keys).
    answers_out = dict(answers)
    try:
        pq = json.loads(request.form.get("per_question_seconds") or "{}")
        if isinstance(pq, dict) and pq:
            answers_out["_per_question_seconds"] = {
                k: int(v) for k, v in pq.items() if str(k).startswith("p")
            }
    except (TypeError, ValueError):
        pass

    # Research measurement: EVERY attempt is recorded regardless of pass/fail.
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
    db.session.commit()

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

    buf = _build_certificate_pdf(
        name=current_user.username,
        rank=stats.get("rank", "Atlas Sage"),
        score=score,
        total=len(POST_TEST),
        badges_earned=stats.get("badges_earned", 0),
        badges_total=stats.get("badges_total", 4),
        mastery=mastery,
        date_str=completed_at.strftime("%d %B %Y"),
    )
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
    PURPLE_LINE = HexColor("#3a2570")
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
    c.drawCentredString(cx, H - 286, "has journeyed through the three realms and earned the rank of")

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
