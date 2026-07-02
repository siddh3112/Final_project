"""
Database models for Atlas Quest — 7 tables.

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    question_key = db.Column(db.String(20), nullable=False)
    selected_answer = db.Column(db.String(4), nullable=True)
    is_correct = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    npc_consulted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class KnowledgeTest(db.Model):
    __tablename__ = "knowledge_tests"

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

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_key = db.Column(db.String(40), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    ai_lab_score = db.Column(db.Integer, nullable=False, default=0)
    observatory_score = db.Column(db.Integer, nullable=False, default=0)
    badges_count = db.Column(db.Integer, nullable=False, default=0)
    time_spent_seconds = db.Column(db.Integer, nullable=True)
    xp = db.Column(db.Integer, nullable=False, default=0)
    rank = db.Column(db.String(40), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
