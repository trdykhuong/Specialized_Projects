"""
blueprints/saved_jobs.py
Lưu tin tuyển dụng để ứng tuyển sau.
Blueprint chỉ: parse request → gọi service → trả response.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.application_service import ApplicationService

saved_jobs_bp = Blueprint("saved_jobs", __name__, url_prefix="/api/saved-jobs")


@saved_jobs_bp.get("")
@jwt_required()
def list_saved():
    result = ApplicationService.list_saved_jobs(
        user_id=int(get_jwt_identity()),
        page=max(int(request.args.get("page", 1)), 1),
        page_size=min(max(int(request.args.get("pageSize", 20)), 1), 100),
    )
    return jsonify(result)


@saved_jobs_bp.post("")
@jwt_required()
def save_job():
    data = request.get_json(silent=True) or {}
    saved, error = ApplicationService.save_job(int(get_jwt_identity()), data)
    if error:
        return jsonify({"error": error}), 409 if "đã được lưu" in error else 400
    return jsonify(saved.to_dict()), 201


@saved_jobs_bp.patch("/<int:saved_id>")
@jwt_required()
def update_saved(saved_id: int):
    saved = ApplicationService.get_saved_job(saved_id, int(get_jwt_identity()))
    if not saved:
        return jsonify({"error": "Không tìm thấy."}), 404
    updated = ApplicationService.update_saved_job(saved, request.get_json(silent=True) or {})
    return jsonify(updated.to_dict())


@saved_jobs_bp.delete("/<int:saved_id>")
@jwt_required()
def delete_saved(saved_id: int):
    saved = ApplicationService.get_saved_job(saved_id, int(get_jwt_identity()))
    if not saved:
        return jsonify({"error": "Không tìm thấy."}), 404
    ApplicationService.delete_saved_job(saved)
    return jsonify({"message": "Đã bỏ lưu."})


@saved_jobs_bp.post("/<int:saved_id>/apply")
@jwt_required()
def apply_from_saved(saved_id: int):
    saved = ApplicationService.get_saved_job(saved_id, int(get_jwt_identity()))
    if not saved:
        return jsonify({"error": "Không tìm thấy."}), 404

    data = request.get_json(silent=True) or {}
    app = ApplicationService.apply_from_saved(saved, extra_note=data.get("note", ""))
    return jsonify(app.to_dict()), 201
