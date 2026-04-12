"""
blueprints/auth.py
Đăng ký, đăng nhập, lấy / cập nhật profile, đổi mật khẩu.
Blueprint chỉ: parse request → gọi service → trả response.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.user_service import UserService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    user, error = UserService.register(
        email=data.get("email", ""),
        name=data.get("name", ""),
        password=data.get("password", ""),
    )
    if error:
        return jsonify({"error": error}), 400
    return jsonify({
        "message": "Đăng ký thành công. Vui lòng đăng nhập để tiếp tục.",
        "user": user.to_dict(),
    }), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user, error = UserService.authenticate(
        email=data.get("email", ""),
        password=data.get("password", ""),
    )
    if error:
        return jsonify({"error": error}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({"user": user.to_dict(), "accessToken": token})


@auth_bp.get("/profile")
@jwt_required()
def get_profile():
    user, error = UserService.get_by_id(int(get_jwt_identity()))
    if error:
        return jsonify({"error": error}), 404
    return jsonify(user.to_dict())


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    user, error = UserService.get_by_id(int(get_jwt_identity()))
    if error:
        return jsonify({"error": error}), 404

    data = request.get_json(silent=True) or {}
    updated, error = UserService.update_profile(user, data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(updated.to_dict())


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user, error = UserService.get_by_id(int(get_jwt_identity()))
    if error:
        return jsonify({"error": error}), 404

    data = request.get_json(silent=True) or {}
    error = UserService.change_password(
        user,
        old_password=data.get("oldPassword", ""),
        new_password=data.get("newPassword", ""),
    )
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Đổi mật khẩu thành công."})