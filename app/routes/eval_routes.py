import json

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..eval_content import POST_TEST
from ..models import KnowledgeTest, db
from ..services.achievements import grant_new
from ..services.progress import all_passed

eval_bp = Blueprint("eval", __name__, url_prefix="/eval")


@eval_bp.route("/post-test")
@login_required
def post_test():
    # Gated: only after all three locations are passed, and only once.
    if not all_passed(current_user):
        return redirect(url_for("game.hub"))
    if current_user.post_test_done:
        return redirect(url_for("game.hub"))
    return render_template("eval/post_test.html", questions=POST_TEST)


@eval_bp.route("/post-test/submit", methods=["POST"])
@login_required
def submit_post_test():
    if not all_passed(current_user):
        return redirect(url_for("game.hub"))
    if current_user.post_test_done:
        return redirect(url_for("game.hub"))

    answers = {}
    score = 0
    for q in POST_TEST:
        selected = request.form.get(q["key"])
        answers[q["key"]] = selected
        if selected == q["correct"]:
            score += 1

    db.session.add(
        KnowledgeTest(
            user_id=current_user.id,
            answers_json=json.dumps(answers),
            score=score,
        )
    )
    current_user.post_test_done = True
    db.session.commit()

    # Grant the Atlas Sage (and any pending) achievement; hub celebrates it.
    session["atlas_new_achievements"] = grant_new(current_user)

    # The app ends here.
    return render_template("eval/post_test_done.html", score=score, total=len(POST_TEST))
