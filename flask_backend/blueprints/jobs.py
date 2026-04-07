"""
blueprints/jobs.py
Danh sách job, phân tích đơn lẻ, batch analyze, blacklist, gợi ý cá nhân.
Tất cả logic ML/heuristic đều delegate sang RecruitmentTrustService (qua app.config).
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


def _predictor():
    return current_app.config["PREDICTOR"]


# ------------------------------------------------------------------ #
# Danh sách jobs (public)
# ------------------------------------------------------------------ #

@jobs_bp.get("")
def list_jobs():
    query = request.args.get("query", "")
    risk = request.args.get("risk", "ALL")
    page = max(int(request.args.get("page", 1)), 1)
    page_size = max(int(request.args.get("pageSize", request.args.get("limit", 12))), 1)
    return jsonify(_predictor().list_jobs(query=query, risk=risk, page=page, page_size=page_size))


# ------------------------------------------------------------------ #
# Phân tích một tin (public — anonymous hoặc có JWT)
# ------------------------------------------------------------------ #

@jobs_bp.post("/analyze")
def analyze_job():
    payload = request.get_json(silent=True) or {}

    # Nếu user đã đăng nhập, bổ sung preferences vào candidateProfile
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            from models import User
            user = User.query.get(int(user_id))
    except Exception:
        pass

    return jsonify(_predictor().analyze_job(payload))


# ------------------------------------------------------------------ #
# Batch analyze (public)
# ------------------------------------------------------------------ #

@jobs_bp.post("/batch-analyze")
def batch_analyze():
    payload = request.get_json(silent=True) or {}
    return jsonify(_predictor().batch_analyze(payload))


# ------------------------------------------------------------------ #
# Blacklist
# ------------------------------------------------------------------ #

@jobs_bp.get("/blacklist")
def get_blacklist():
    return jsonify(_predictor().get_blacklist())


@jobs_bp.post("/blacklist/check")
def check_blacklist():
    payload = request.get_json(silent=True) or {}
    return jsonify(_predictor().check_blacklist(payload.get("job", {})))


@jobs_bp.post("/blacklist/update")
def update_blacklist():
    payload = request.get_json(silent=True) or {}
    return jsonify(_predictor().update_blacklist(payload))


# ------------------------------------------------------------------ #
# Gợi ý cá nhân hóa
# ------------------------------------------------------------------ #

@jobs_bp.post("/recommend")
def recommend():
    """
    Gợi ý job phù hợp. Nếu đã đăng nhập → vẫn cho phép payload tay,
    còn khi chưa có preferences lưu trong backend thì frontend có thể gửi trực tiếp.
    """
    payload = request.get_json(silent=True) or {}

    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            from models import User
            user = User.query.get(int(user_id))
            if user:
                payload.setdefault("keywords", [])
                payload.setdefault("jobTypes", [])
                payload.setdefault("preferredRisk", ["LOW", "MEDIUM"])
    except Exception:
        pass

    return jsonify(_predictor().recommend_jobs(payload))
