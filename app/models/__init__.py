"""
Database models for Atlas Quest — 11 tables.

The single SQLAlchemy instance `db` lives here and is initialised in
app/__init__.py via db.init_app(app). SQLite auto-creates at
instance/atlas_quest.db on first run.
"""

from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    condition = db.Column(db.String(20), nullable=False, default="game")  # game | control
    post_test_done = db.Column(db.Boolean, nullable=False, default=False)
    # Whether this user has been shown the opening instructions (cinematic +
    # how-to-play) — tracked per USER so each participant sees them once,
    # independent of browser/session state. Presentation only.
    seen_intro = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class GameSession(db.Model):
    __tablename__ = "game_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)


class NpcInteraction(db.Model):
    __tablename__ = "npc_interactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("game_sessions.id"), nullable=True)
    location = db.Column(db.String(40), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    npc_response = db.Column(db.Text, nullable=False)
    response_time_ms = db.Column(db.Integer, nullable=True)
    is_fallback = db.Column(db.Boolean, default=False)
    # Which engine produced the reply: "granite" (local LLM) or "rules" (a Socratic
    # deflection, a keyword explanation, or the generic fallback). This is the
    # accurate source for the UI label and research data; is_fallback is a narrower
    # flag (generic catch-all only) and must NOT be used to infer Granite-vs-rules.
    source = db.Column(db.String(16), default="rules")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    question_key = db.Column(db.String(20), nullable=False)
    # A letter (MCQ) OR a comma-joined event-id sequence (ordering items). Widened
    # from String(4) to hold a sequence; non-breaking (SQLite doesn't enforce length).
    selected_answer = db.Column(db.String(64), nullable=True)
    is_correct = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    npc_consulted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TrialAttempt(db.Model):
    """Durable, SERVER-AUTHORITATIVE record of one Trial attempt.

    The server chooses the TRIAL_COUNT unique question keys and stores them here
    (never the browser); the page carries only this row's opaque `token`. Grading
    reads the stored keys + the recorded first-committed answers, so a forged /
    duplicated / mismatched key list from the client cannot influence the result,
    and an attempt is graded at most once (status 'open' -> 'submitted').

    This is NOT the same as `quiz_attempts`, which remains the per-question
    research log (one row per graded question, unchanged)."""
    __tablename__ = "trial_attempts"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)  # opaque server attempt id
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    location = db.Column(db.String(40), nullable=False)
    question_keys = db.Column(db.Text, nullable=False)               # JSON list of the 4 server-chosen unique keys
    answers_json = db.Column(db.Text, nullable=False, default="{}")  # JSON {qkey: first-committed letter}
    status = db.Column(db.String(16), nullable=False, default="open")  # open | submitted | expired
    score = db.Column(db.Integer, nullable=True)
    passed = db.Column(db.Boolean, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)


class KnowledgeTest(db.Model):
    __tablename__ = "knowledge_tests"
    # SINGLE-ATTEMPT: the graded Final Assessment is a one-shot research measure —
    # exactly one row per participant. This DB-level uniqueness makes a concurrent
    # double-submit impossible (the losing racer's insert raises IntegrityError),
    # backing up the check-then-insert guard in eval_routes.submit_post_test.
    __table_args__ = (
        db.UniqueConstraint("user_id", name="ux_knowledge_test_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    answers_json = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    # Silent research telemetry: total wall-clock seconds on the assessment.
    # Never shown to the learner and never affects the score.
    time_spent_seconds = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LocationProgress(db.Model):
    __tablename__ = "location_progress"
    __table_args__ = (
        db.UniqueConstraint("user_id", "location", name="ux_progress_user_location"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    passed = db.Column(db.Boolean, default=False)
    best_score = db.Column(db.Integer, default=0)
    attempts_count = db.Column(db.Integer, default=0)
    unlocked_at = db.Column(db.DateTime, nullable=True)


class Achievement(db.Model):
    """One row per achievement a user has earned (research/engagement data)."""

    __tablename__ = "achievements"
    __table_args__ = (
        db.UniqueConstraint("user_id", "achievement_key", name="ux_achievement_user_key"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_key = db.Column(db.String(40), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)


class BookRead(db.Model):
    """One row per content volume (Library book) a user has studied.

    Per-user reading progress so the Knowledge Core / Concept Deck survive
    navigation and logins. Presentation/progress convenience only — never
    scored and not a research measure.
    """

    __tablename__ = "book_reads"
    __table_args__ = (
        db.UniqueConstraint("user_id", "location", "book_id", name="ux_book_read"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    book_id = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Reflection(db.Model):
    """One learner reflection per Trial-pass prompt (generative learning).

    New qualitative research data, additive only. A reflection is ungraded and
    never affects scoring, progression, XP, or any existing measure. `skipped`
    rows (empty response) are kept so the skip-rate itself is analysable.
    """

    __tablename__ = "reflections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    prompt_key = db.Column(db.String(60), nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text, nullable=True)
    skipped = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Professor Atlas's one-line reply to a real (non-skipped) reflection, generated
    # ONCE at seal time and persisted so the Journal can show it read-only. atlas_source
    # is "granite" (LLM) or "rules" (authored fallback): the same engine-source signal
    # the hint UI uses. Both nullable, so skipped rows and pre-upgrade rows have neither.
    atlas_response = db.Column(db.Text, nullable=True)
    atlas_source = db.Column(db.String(16), nullable=True)


class RunHistory(db.Model):
    """One row per completed post-test run — a PERSONAL best-runs history.

    This is per-user history for a personal leaderboard; it is never ranked
    across users or by condition. Additive telemetry: it does not affect scoring.
    """

    __tablename__ = "run_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    combined_score = db.Column(db.Integer, nullable=False)
    post_test_score = db.Column(db.Integer, nullable=False)
    post_test_max = db.Column(db.Integer, nullable=False)
    library_score = db.Column(db.Integer, nullable=False, default=0)
    chronicle_score = db.Column(db.Integer, nullable=False, default=0)
    ai_lab_score = db.Column(db.Integer, nullable=False, default=0)
    observatory_score = db.Column(db.Integer, nullable=False, default=0)
    badges_count = db.Column(db.Integer, nullable=False, default=0)
    time_spent_seconds = db.Column(db.Integer, nullable=True)
    xp = db.Column(db.Integer, nullable=False, default=0)
    rank = db.Column(db.String(40), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
