"""
blueprints/auth.py
Đăng ký, đăng nhập, lấy / cập nhật profile, đổi mật khẩu.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ------------------------------------------------------------------ #
# Register
# ------------------------------------------------------------------ #

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    name = str(data.get("name", "")).strip()
    password = str(data.get("password", "")).strip()

    if not email or not name or not password:
        return jsonify({"error": "Vui lòng điền đầy đủ email, tên và mật khẩu."}), 400
    if len(password) < 8:
        return jsonify({"error": "Mật khẩu phải có ít nhất 8 ký tự."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email đã được sử dụng."}), 409

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"user": user.to_dict(include_preferences=True), "accessToken": token}), 201


# ------------------------------------------------------------------ #
# Login
# ------------------------------------------------------------------ #

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Email hoặc mật khẩu không đúng."}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"user": user.to_dict(include_preferences=True), "accessToken": token})


# ------------------------------------------------------------------ #
# Profile — lấy và cập nhật
# ------------------------------------------------------------------ #

@auth_bp.get("/profile")
@jwt_required()
def get_profile():
    user = _current_user()
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng."}), 404
    return jsonify(user.to_dict(include_preferences=True))


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    user = _current_user()
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng."}), 404

    data = request.get_json(silent=True) or {}

    if "name" in data and str(data["name"]).strip():
        user.name = str(data["name"]).strip()


    db.session.commit()
    return jsonify(user.to_dict(include_preferences=True))


# ------------------------------------------------------------------ #
# Change password
# ------------------------------------------------------------------ #

@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user = _current_user()
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng."}), 404

    data = request.get_json(silent=True) or {}
    old_pw = str(data.get("oldPassword", ""))
    new_pw = str(data.get("newPassword", ""))

    if not user.check_password(old_pw):
        return jsonify({"error": "Mật khẩu hiện tại không đúng."}), 400
    if len(new_pw) < 8:
        return jsonify({"error": "Mật khẩu mới phải có ít nhất 8 ký tự."}), 400

    user.set_password(new_pw)
    db.session.commit()
    return jsonify({"message": "Đổi mật khẩu thành công."})


# ------------------------------------------------------------------ #
# Helper
# ------------------------------------------------------------------ #

def _current_user() -> User | None:
    user_id = get_jwt_identity()
    return User.query.get(int(user_id)) if user_id else None
