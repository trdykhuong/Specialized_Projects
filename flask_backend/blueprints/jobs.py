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


def _trainer():
    return current_app.config["TRAINING_PIPELINE"]


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


@jobs_bp.get("/<int:job_id>")
def get_job(job_id: int):
    job = _predictor().get_job(job_id)
    if not job:
        return jsonify({"error": "Không tìm thấy job."}), 404
    return jsonify(job)


@jobs_bp.post("")
def create_job():
    from extensions import db
    from models import CustomJob

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    company_name = str(payload.get("companyName", "")).strip()
    description = str(payload.get("description", "")).strip()

    if not title:
        return jsonify({"error": "Job title là bắt buộc."}), 400

    existing = (
        CustomJob.query
        .filter_by()
        .order_by(CustomJob.created_at.desc())
        .all()
    )

    for item in existing:
        data = item.job_data
        if (
            str(data.get("title", "")).strip().lower() == title.lower()
            and str(data.get("companyName", "")).strip().lower() == company_name.lower()
            and str(data.get("description", "")).strip().lower() == description.lower()
        ):
            return jsonify(item.to_dict()), 200

    custom_job = CustomJob()
    custom_job.job_data = {
        "title": title,
        "companyName": company_name,
        "companyOverview": str(payload.get("companyOverview", "")).strip(),
        "companyAddress": str(payload.get("companyAddress", "")).strip(),
        "description": description,
        "requirements": str(payload.get("requirements", "")).strip(),
        "benefits": str(payload.get("benefits", "")).strip(),
        "address": str(payload.get("address", "")).strip(),
        "jobType": str(payload.get("jobType", "")).strip(),
        "gender": str(payload.get("gender", "")).strip(),
        "candidates": int(payload.get("candidates", 0) or 0),
        "careerLevel": str(payload.get("careerLevel", "")).strip(),
        "experience": str(payload.get("experience", "")).strip(),
        "salary": str(payload.get("salary", "")).strip(),
        "submissionDeadline": str(payload.get("submissionDeadline", "")).strip(),
        "industry": str(payload.get("industry", "")).strip(),
        "email": str(payload.get("email", "")).strip(),
        "phone": str(payload.get("phone", "")).strip(),
    }
    db.session.add(custom_job)
    db.session.commit()
    return jsonify(custom_job.to_dict()), 201


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
            if user:
                payload.setdefault("candidateProfile", {})
                payload["candidateProfile"].setdefault("keywords", user.keywords)
                payload["candidateProfile"].setdefault("jobTypes", user.job_types)
    except Exception:
        pass

    training = _trainer().ensure_training_started(triggered_by="analyze")
    result = _predictor().analyze_job(payload)
    result["training"] = training
    return jsonify(result)


@jobs_bp.get("/training-status")
def training_status():
    return jsonify(_trainer().get_status())


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
                payload.setdefault("keywords", user.keywords)
                payload.setdefault("jobTypes", user.job_types)
                payload.setdefault("preferredRisk", user.preferred_risk_levels)
    except Exception:
        pass

    return jsonify(_predictor().recommend_jobs(payload))
