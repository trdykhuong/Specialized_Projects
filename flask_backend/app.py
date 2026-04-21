"""
app.py — Entry point chính.

Cấu trúc:
  - create_app() khởi tạo Flask, đăng ký extensions và blueprints.
  - RecruitmentTrustService (ML/heuristic) được khởi tạo một lần và
    truyền vào blueprints liên quan qua app.config.

Chạy:
  flask --app app run --debug
  # hoặc
  python app.py
"""
import csv
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import inspect, text
from scipy.sparse import hstack

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "JOB_DATA_HIGH_CONFIDENCE_KHOA.csv"
MODELS_DIR = BASE_DIR / "models"
BLACKLIST_PATH = Path(__file__).resolve().parent / "blacklist.json"
DEMO_ACCOUNT_EMAIL = "customer@gmail.com"
DEMO_ACCOUNT_PASSWORD = "123456"
DEMO_ACCOUNT_NAME = "Customer"
DEMO_NOTE_PREFIX = "[demo-seed]"
DEMO_APPLICATION_COUNT = 18
DEMO_SAVED_COUNT = 2
DEMO_TOTAL_ITEMS = DEMO_APPLICATION_COUNT + DEMO_SAVED_COUNT

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from extensions import db, jwt, migrate
from blueprints import auth, jobs, dashboard, applications, saved_jobs, stats
from models.application import Application, ApplicationStatus
from models.saved_job import SavedJob
from models.user import User
from services.recruitment_trust import RecruitmentTrustService
from services.training_pipeline import TrainingPipelineManager


def _ensure_user_preference_columns() -> None:
    inspector = inspect(db.engine)
    column_names = {column["name"] for column in inspector.get_columns("users")}
    statements: list[str] = []

    if "preferred_risk" not in column_names:
        statements.append("ALTER TABLE users ADD COLUMN preferred_risk VARCHAR(50) DEFAULT 'LOW,MEDIUM'")
    if "keywords_json" not in column_names:
        statements.append("ALTER TABLE users ADD COLUMN keywords_json TEXT DEFAULT '[]'")
    if "job_types_json" not in column_names:
        statements.append("ALTER TABLE users ADD COLUMN job_types_json TEXT DEFAULT '[]'")

    for statement in statements:
        db.session.execute(text(statement))

    if statements:
        db.session.commit()


def _ensure_demo_customer_account() -> None:
    user = User.query.filter_by(email=DEMO_ACCOUNT_EMAIL).first()
    if not user:
        user = User(email=DEMO_ACCOUNT_EMAIL, name=DEMO_ACCOUNT_NAME)
        user.set_password(DEMO_ACCOUNT_PASSWORD)
        user.keywords = ["data", "analyst", "python", "sql", "remote"]
        user.job_types = ["Toàn thời gian", "Remote", "Hybrid"]
        user.preferred_risk = "LOW,MEDIUM"
        db.session.add(user)
        db.session.commit()

    demo_applications = (
        Application.query
        .filter_by(user_id=user.id)
        .filter(Application.note.like(f"{DEMO_NOTE_PREFIX}%"))
        .count()
    )
    demo_saved_jobs = (
        SavedJob.query
        .filter_by(user_id=user.id)
        .filter(SavedJob.note.like(f"{DEMO_NOTE_PREFIX}%"))
        .count()
    )
    if demo_applications + demo_saved_jobs >= DEMO_TOTAL_ITEMS:
        return

    Application.query.filter_by(user_id=user.id).filter(
        Application.note.like(f"{DEMO_NOTE_PREFIX}%")
    ).delete(synchronize_session=False)
    SavedJob.query.filter_by(user_id=user.id).filter(
        SavedJob.note.like(f"{DEMO_NOTE_PREFIX}%")
    ).delete(synchronize_session=False)

    rows = _load_demo_job_rows(limit=DEMO_TOTAL_ITEMS)
    if len(rows) < DEMO_TOTAL_ITEMS:
        db.session.commit()
        return

    now = datetime.now(timezone.utc)
    application_statuses = [
        ApplicationStatus.APPLIED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.OFFERED,
        ApplicationStatus.OFFERED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.APPLIED,
        ApplicationStatus.INTERVIEWING,
    ]
    risk_levels = ["LOW", "MEDIUM", "HIGH"]

    for index, row in enumerate(rows[:DEMO_APPLICATION_COUNT]):
        applied_at = now - timedelta(days=(index * 9) + 2)
        risk_level = risk_levels[index % len(risk_levels)]
        risk_score = 18 + (index % 7) * 9
        trust_score = max(12, 100 - risk_score)
        app = Application(
            user_id=user.id,
            job_id=_safe_int(row.get("JobID")),
            status=application_statuses[index],
            note=f"{DEMO_NOTE_PREFIX} Hồ sơ mẫu {index + 1} cho dashboard thống kê.",
            personal_rating=(index % 5) + 1,
            risk_score=risk_score,
            trust_score=trust_score,
            risk_level=risk_level,
            applied_at=applied_at,
            updated_at=applied_at + timedelta(days=(index % 4)),
        )
        app.job_data = _build_job_snapshot(row)
        db.session.add(app)

    for index, row in enumerate(rows[DEMO_APPLICATION_COUNT:DEMO_TOTAL_ITEMS]):
        job_id = _safe_int(row.get("JobID"))
        saved_at = now - timedelta(days=index + 1)
        risk_score = 22 + index * 11
        
        # Check if already exists to avoid UNIQUE constraint violation
        existing = SavedJob.query.filter_by(
            user_id=user.id,
            job_id=job_id
        ).first()
        
        if existing:
            # Update existing record
            existing.note = f"{DEMO_NOTE_PREFIX} Tin lưu sẵn {index + 1} để demo saved jobs."
            existing.risk_score = risk_score
            existing.trust_score = max(10, 100 - risk_score)
            existing.risk_level = risk_levels[(index + 1) % len(risk_levels)]
            existing.saved_at = saved_at
            existing.job_data = _build_job_snapshot(row)
        else:
            # Create new record
            saved = SavedJob(
                user_id=user.id,
                job_id=job_id,
                note=f"{DEMO_NOTE_PREFIX} Tin lưu sẵn {index + 1} để demo saved jobs.",
                risk_score=risk_score,
                trust_score=max(10, 100 - risk_score),
                risk_level=risk_levels[(index + 1) % len(risk_levels)],
                saved_at=saved_at,
            )
            saved.job_data = _build_job_snapshot(row)
            db.session.add(saved)

    db.session.commit()


def _load_demo_job_rows(limit: int) -> list[dict[str, str]]:
    candidate_paths = [
        BASE_DIR / "data" / "JOB_DATA_FINAL.csv",
        BASE_DIR / "data" / "JOB_DATA_HIGH_CONFIDENCE_KHOA.csv",
    ]
    for path in candidate_paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            rows: list[dict[str, str]] = []
            for row in reader:
                if not row:
                    continue
                title = str(row.get("Job Title", "")).strip()
                company = str(row.get("Name Company", "")).strip()
                if not title or not company:
                    continue
                rows.append(row)
                if len(rows) >= limit:
                    return rows
    return []


def _build_job_snapshot(row: dict[str, str]) -> dict[str, str]:
    return {
        "title": str(row.get("Job Title", "")).strip(),
        "jobTitle": str(row.get("Job Title", "")).strip(),
        "companyName": str(row.get("Name Company", "")).strip(),
        "nameCompany": str(row.get("Name Company", "")).strip(),
        "companyOverview": str(row.get("Company Overview", "")).strip(),
        "companySize": str(row.get("Company Size", "")).strip(),
        "companyAddress": str(row.get("Company Address", "")).strip(),
        "description": str(row.get("Job Description", "")).strip(),
        "requirements": str(row.get("Job Requirements", "")).strip(),
        "benefits": str(row.get("Benefits", "")).strip(),
        "salary": str(row.get("Salary", "")).strip(),
        "location": str(row.get("Job Address", "")).strip(),
        "address": str(row.get("Job Address", "")).strip(),
        "jobAddress": str(row.get("Job Address", "")).strip(),
        "email": "",
        "phone": "",
        "jobType": str(row.get("Job Type", "")).strip(),
        "gender": str(row.get("Gender", "")).strip(),
        "candidates": str(row.get("Number Cadidate", "")).strip(),
        "numberCadidate": str(row.get("Number Cadidate", "")).strip(),
        "careerLevel": str(row.get("Career Level", "")).strip(),
        "experience": str(row.get("Years of Experience", "")).strip(),
        "yearsOfExperience": str(row.get("Years of Experience", "")).strip(),
        "submissionDeadline": str(row.get("Submission Deadline", "")).strip(),
        "industry": str(row.get("Industry", "")).strip(),
        "urlJob": str(row.get("URL Job", "")).strip(),
    }


def _safe_int(value) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ------------------------------------------------------------------ #
    # Config
    # ------------------------------------------------------------------ #
    app.config.setdefault("SECRET_KEY", "change-me-in-production")
    app.config.setdefault("JWT_SECRET_KEY", "jwt-change-me-in-production")
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        f"sqlite:///{Path(__file__).resolve().parent / 'recruitment.db'}",
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    if config:
        app.config.update(config)

    # ------------------------------------------------------------------ #
    # Extensions
    # ------------------------------------------------------------------ #
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()
        _ensure_user_preference_columns()
        _ensure_demo_customer_account()

    # ------------------------------------------------------------------ #
    # ML / Trust service (singleton, thread-safe read)
    # ------------------------------------------------------------------ #
    predictor = RecruitmentTrustService()
    predictor.load_assets()
    app.config["PREDICTOR"] = predictor
    trainer = TrainingPipelineManager(BASE_DIR, on_success=predictor.load_assets)
    app.config["TRAINING_PIPELINE"] = trainer

    # ------------------------------------------------------------------ #
    # Blueprints — user / tracking / stats
    # ------------------------------------------------------------------ #
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(jobs.jobs_bp)
    app.register_blueprint(dashboard.dashboard_bp)
    app.register_blueprint(applications.applications_bp)
    app.register_blueprint(saved_jobs.saved_jobs_bp)
    app.register_blueprint(stats.stats_bp)

    # ------------------------------------------------------------------ #
    # Routes giữ nguyên — health, jobs, analysis, blacklist
    # ------------------------------------------------------------------ #

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "message": "Hệ thống hoạt động bình thường.",
                "timestamp": datetime.utcnow().isoformat(),
                "modelLoaded": predictor.model_ready,
                "datasetLoaded": predictor.dataset_ready,
                "training": trainer.get_status(),
            }
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
