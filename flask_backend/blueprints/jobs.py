"""
blueprints/jobs.py
Phân tích tin tuyển dụng, batch analyze, blacklist.
Blueprint chỉ: parse request → gọi service → trả response.
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from services.user_service import UserService

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


def _predictor():
    return current_app.config["PREDICTOR"]


@jobs_bp.post("/analyze")
def analyze_job():
    payload = request.get_json(silent=True) or {}

    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user, _ = UserService.get_by_id(int(user_id))
            if user:
                payload.setdefault("candidateProfile", {})
                payload["candidateProfile"].setdefault("keywords", user.keywords)
                payload["candidateProfile"].setdefault("jobTypes", user.job_types)
    except Exception:
        pass

    return jsonify(_predictor().analyze_job(payload))


@jobs_bp.post("/batch-analyze")
def batch_analyze():
    return jsonify(_predictor().batch_analyze(request.get_json(silent=True) or {}))


@jobs_bp.get("/blacklist")
def get_blacklist():
    return jsonify(_predictor().get_blacklist())


@jobs_bp.post("/blacklist/check")
def check_blacklist():
    payload = request.get_json(silent=True) or {}
    return jsonify(_predictor().check_blacklist(payload.get("job", {})))


@jobs_bp.post("/blacklist/update")
def update_blacklist():
    return jsonify(_predictor().update_blacklist(request.get_json(silent=True) or {}))
