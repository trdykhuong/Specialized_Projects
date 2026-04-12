"""
blueprints/applications.py
CRUD theo dõi ứng tuyển.
Blueprint chỉ: parse request → gọi service → trả response.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.application_service import ApplicationService

applications_bp = Blueprint("applications", __name__, url_prefix="/api/applications")


@applications_bp.get("")
@jwt_required()
def list_applications():
    user_id = int(get_jwt_identity())
    result = ApplicationService.list_applications(
        user_id=user_id,
        status_filter=request.args.get("status", ""),
        page=max(int(request.args.get("page", 1)), 1),
        page_size=min(max(int(request.args.get("pageSize", 20)), 1), 100),
    )
    return jsonify(result)


@applications_bp.post("")
@jwt_required()
def create_application():
    data = request.get_json(silent=True) or {}
    app, error = ApplicationService.create_application(int(get_jwt_identity()), data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(app.to_dict()), 201


@applications_bp.get("/<int:app_id>")
@jwt_required()
def get_application(app_id: int):
    app = ApplicationService.get_application(app_id, int(get_jwt_identity()))
    if not app:
        return jsonify({"error": "Không tìm thấy."}), 404
    return jsonify(app.to_dict())


@applications_bp.patch("/<int:app_id>")
@jwt_required()
def update_application(app_id: int):
    app = ApplicationService.get_application(app_id, int(get_jwt_identity()))
    if not app:
        return jsonify({"error": "Không tìm thấy."}), 404

    data = request.get_json(silent=True) or {}
    updated, error = ApplicationService.update_application(app, data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(updated.to_dict())


@applications_bp.delete("/<int:app_id>")
@jwt_required()
def delete_application(app_id: int):
    app = ApplicationService.get_application(app_id, int(get_jwt_identity()))
    if not app:
        return jsonify({"error": "Không tìm thấy."}), 404
    ApplicationService.delete_application(app)
    return jsonify({"message": "Đã xóa."})
