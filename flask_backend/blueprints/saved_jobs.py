"""
blueprints/saved_jobs.py
Lưu tin tuyển dụng để ứng tuyển sau: thêm, xóa, liệt kê.
Có thể "nâng cấp" một saved_job thành application (apply ngay).
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.application import Application, ApplicationStatus
from models.saved_job import SavedJob

saved_jobs_bp = Blueprint("saved_jobs", __name__, url_prefix="/api/saved-jobs")


# ------------------------------------------------------------------ #
# List
# ------------------------------------------------------------------ #

@saved_jobs_bp.get("")
@jwt_required()
def list_saved():
    user_id = int(get_jwt_identity())
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("pageSize", 20)), 1), 100)

    paginated = (
        SavedJob.query
        .filter_by(user_id=user_id)
        .order_by(SavedJob.saved_at.desc())
        .paginate(page=page, per_page=page_size, error_out=False)
    )
    return jsonify({
        "items": [s.to_dict() for s in paginated.items],
        "total": paginated.total,
        "page": page,
        "pageSize": page_size,
        "totalPages": paginated.pages,
        "hasNext": paginated.has_next,
        "hasPrevious": paginated.has_prev,
    })


# ------------------------------------------------------------------ #
# Save a job
# ------------------------------------------------------------------ #

@saved_jobs_bp.post("")
@jwt_required()
def save_job():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    job_data = data.get("job", {})
    if not job_data or not job_data.get("title"):
        return jsonify({"error": "Thiếu thông tin tin tuyển dụng."}), 400

    job_id = data.get("jobId")
    
    # Check if job is already saved
    existing = SavedJob.query.filter_by(
        user_id=user_id,
        job_id=job_id
    ).first()
    
    if existing:
        # Update existing saved job
        existing.note = str(data.get("note", existing.note or "")).strip()
        existing.risk_score = float(data.get("riskScore", existing.risk_score) or 0)
        existing.trust_score = float(data.get("trustScore", existing.trust_score) or 0)
        existing.risk_level = str(data.get("riskLevel", existing.risk_level or "")).strip()
        existing.job_data = job_data
        db.session.commit()
        return jsonify(existing.to_dict()), 200
    
    # Create new saved job
    saved = SavedJob(
        user_id=user_id,
        job_id=job_id,
        note=str(data.get("note", "")).strip(),
        risk_score=float(data.get("riskScore", 0) or 0),
        trust_score=float(data.get("trustScore", 0) or 0),
        risk_level=str(data.get("riskLevel", "")).strip(),
    )
    saved.job_data = job_data
    db.session.add(saved)
    db.session.commit()
    return jsonify(saved.to_dict()), 201


# ------------------------------------------------------------------ #
# Update note
# ------------------------------------------------------------------ #

@saved_jobs_bp.patch("/<int:saved_id>")
@jwt_required()
def update_saved(saved_id: int):
    saved = _get_owned(saved_id)
    if not saved:
        return jsonify({"error": "Không tìm thấy."}), 404

    data = request.get_json(silent=True) or {}
    if "note" in data:
        saved.note = str(data["note"]).strip()
    db.session.commit()
    return jsonify(saved.to_dict())


# ------------------------------------------------------------------ #
# Delete (bỏ lưu)
# ------------------------------------------------------------------ #

@saved_jobs_bp.delete("/<int:saved_id>")
@jwt_required()
def delete_saved(saved_id: int):
    saved = _get_owned(saved_id)
    if not saved:
        return jsonify({"error": "Không tìm thấy."}), 404
    db.session.delete(saved)
    db.session.commit()
    return jsonify({"message": "Đã bỏ lưu."})


# ------------------------------------------------------------------ #
# Apply now — chuyển saved_job thành application
# ------------------------------------------------------------------ #

@saved_jobs_bp.post("/<int:saved_id>/apply")
@jwt_required()
def apply_from_saved(saved_id: int):
    """
    Tạo Application từ SavedJob, sau đó xóa SavedJob.
    Trả về Application mới tạo.
    """
    user_id = int(get_jwt_identity())
    saved = _get_owned(saved_id)
    if not saved:
        return jsonify({"error": "Không tìm thấy."}), 404

    data = request.get_json(silent=True) or {}

    app = Application(
        user_id=user_id,
        job_id=saved.job_id,
        status=ApplicationStatus.APPLIED,
        note=str(data.get("note", saved.note or "")).strip(),
        personal_rating=None,
        risk_score=saved.risk_score,
        trust_score=saved.trust_score,
        risk_level=saved.risk_level,
    )
    app.job_data = saved.job_data

    db.session.add(app)
    db.session.delete(saved)
    db.session.commit()
    return jsonify(app.to_dict()), 201


# ------------------------------------------------------------------ #
# Helper
# ------------------------------------------------------------------ #

def _get_owned(saved_id: int) -> SavedJob | None:
    user_id = int(get_jwt_identity())
    return SavedJob.query.filter_by(id=saved_id, user_id=user_id).first()
