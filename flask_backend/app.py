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
import json
import re
import sys
from datetime import datetime
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

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from extensions import db, jwt, migrate
from blueprints import auth, jobs, dashboard, applications, saved_jobs, stats
from services.recruitment_trust import RecruitmentTrustService


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

    # ------------------------------------------------------------------ #
    # ML / Trust service (singleton, thread-safe read)
    # ------------------------------------------------------------------ #
    predictor = RecruitmentTrustService()
    predictor.load_assets()
    app.config["PREDICTOR"] = predictor

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
    # Routes  — health, jobs, analysis, blacklist
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
            }
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
