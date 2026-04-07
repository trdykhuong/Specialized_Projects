"""
blueprints/applications.py
CRUD theo dõi ứng tuyển: lưu, cập nhật trạng thái, ghi chú, xóa.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.application import Application, ApplicationStatus

applications_bp = Blueprint("applications", __name__, url_prefix="/api/applications")

VALID_STATUSES = {s.value for s in ApplicationStatus}


# ------------------------------------------------------------------ #
# List — danh sách ứng tuyển của user hiện tại
# ------------------------------------------------------------------ #

@applications_bp.get("")
@jwt_required()
def list_applications():
    user_id = int(get_jwt_identity())
    status_filter = request.args.get("status", "")
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("pageSize", 20)), 1), 100)

    query = Application.query.filter_by(user_id=user_id)
    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter_by(status=ApplicationStatus(status_filter))

    query = query.order_by(Application.applied_at.desc())
    paginated = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        "items": [a.to_dict() for a in paginated.items],
        "total": paginated.total,
        "page": page,
        "pageSize": page_size,
        "totalPages": paginated.pages,
        "hasNext": paginated.has_next,
        "hasPrevious": paginated.has_prev,
    })


# ------------------------------------------------------------------ #
# Create — lưu một lần ứng tuyển mới
# ------------------------------------------------------------------ #

@applications_bp.post("")
@jwt_required()
def create_application():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    job_data = data.get("job", {})
    if not job_data or not job_data.get("title"):
        return jsonify({"error": "Thiếu thông tin tin tuyển dụng (job.title bắt buộc)."}), 400

    status_val = data.get("status", ApplicationStatus.APPLIED.value)
    if status_val not in VALID_STATUSES:
        return jsonify({"error": f"Trạng thái không hợp lệ. Các giá trị hợp lệ: {', '.join(VALID_STATUSES)}"}), 400

    app = Application(
        user_id=user_id,
        job_id=data.get("jobId"),
        status=ApplicationStatus(status_val),
        note=str(data.get("note", "")).strip(),
        personal_rating=_parse_rating(data.get("personalRating")),
        risk_score=float(data.get("riskScore", 0) or 0),
        trust_score=float(data.get("trustScore", 0) or 0),
        risk_level=str(data.get("riskLevel", "")).strip(),
    )
    app.job_data = job_data
    db.session.add(app)
    db.session.commit()
    return jsonify(app.to_dict()), 201


# ------------------------------------------------------------------ #
# Get single
# ------------------------------------------------------------------ #

@applications_bp.get("/<int:app_id>")
@jwt_required()
def get_application(app_id: int):
    app = _get_owned(app_id)
    if not app:
        return jsonify({"error": "Không tìm thấy."}), 404
    return jsonify(app.to_dict())


# ------------------------------------------------------------------ #
# Update — cập nhật trạng thái, ghi chú, đánh giá
# ------------------------------------------------------------------ #

@applications_bp.patch("/<int:app_id>")
@jwt_required()
def update_application(app_id: int):
    app = _get_owned(app_id)
    if not app:
        return jsonify({"error": "Không tìm thấy."}), 404

    data = request.get_json(silent=True) or {}

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return jsonify({"error": "Trạng thái không hợp lệ."}), 400
        app.status = ApplicationStatus(data["status"])

    if "note" in data:
        app.note = str(data["note"]).strip()

    if "personalRating" in data:
        app.personal_rating = _parse_rating(data["personalRating"])

    db.session.commit()
    return jsonify(app.to_dict())


# ------------------------------------------------------------------ #
# Delete
# ------------------------------------------------------------------ #

@applications_bp.delete("/<int:app_id>")
@jwt_required()
def delete_application(app_id: int):
    app = _get_owned(app_id)
    if not app:
        return jsonify({"error": "Không tìm thấy."}), 404
    db.session.delete(app)
    db.session.commit()
    return jsonify({"message": "Đã xóa."})


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _get_owned(app_id: int) -> Application | None:
    user_id = int(get_jwt_identity())
    return Application.query.filter_by(id=app_id, user_id=user_id).first()


def _parse_rating(value) -> int | None:
    if value is None:
        return None
    try:
        r = int(value)
        return r if 1 <= r <= 5 else None
    except (ValueError, TypeError):
        return None
