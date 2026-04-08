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
    confirm_password = str(data.get("confirmPassword", "")).strip()

    if not email or not name or not password:
        return jsonify({"error": "Vui lòng điền đầy đủ email, tên và mật khẩu."}), 400
    if len(password) < 6:
        return jsonify({"error": "Mật khẩu phải có ít nhất 6 ký tự."}), 400
    if confirm_password and confirm_password != password:
        return jsonify({"error": "Xác nhận mật khẩu không khớp."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email đã được sử dụng."}), 409

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Đăng ký thành công. Vui lòng đăng nhập để tiếp tục.",
        "user": user.to_dict(include_preferences=True),
    }), 201


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

    if "name" in data:
        next_name = str(data["name"]).strip()
        if not next_name:
            return jsonify({"error": "Tên không được để trống."}), 400
        user.name = next_name

    preferences = data.get("preferences", {})
    if preferences and not isinstance(preferences, dict):
        return jsonify({"error": "Preferences không hợp lệ."}), 400

    if isinstance(preferences, dict):
        if "keywords" in preferences:
            if not isinstance(preferences["keywords"], list):
                return jsonify({"error": "Keywords phải là một danh sách."}), 400
            user.keywords = _clean_string_list(preferences["keywords"])

        if "jobTypes" in preferences:
            if not isinstance(preferences["jobTypes"], list):
                return jsonify({"error": "Job types phải là một danh sách."}), 400
            user.job_types = _clean_string_list(preferences["jobTypes"])

        if "preferredRisk" in preferences:
            preferred_risk = _clean_risk_levels(preferences["preferredRisk"])
            if not preferred_risk:
                return jsonify({"error": "Preferred risk không hợp lệ."}), 400
            user.preferred_risk = ",".join(preferred_risk)

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
    if len(new_pw) < 6:
        return jsonify({"error": "Mật khẩu mới phải có ít nhất 6 ký tự."}), 400

    user.set_password(new_pw)
    db.session.commit()
    return jsonify({"message": "Đổi mật khẩu thành công."})


# ------------------------------------------------------------------ #
# Helper
# ------------------------------------------------------------------ #

def _current_user() -> User | None:
    user_id = get_jwt_identity()
    return User.query.get(int(user_id)) if user_id else None


def _clean_string_list(values) -> list[str]:
    seen = set()
    cleaned = []
    for raw in values:
        value = str(raw).strip()
        key = value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    return cleaned


def _clean_risk_levels(values) -> list[str]:
    valid = {"LOW", "MEDIUM", "HIGH"}
    if not isinstance(values, list):
        return []
    result = []
    for raw in values:
        value = str(raw).strip().upper()
        if value in valid and value not in result:
            result.append(value)
    return result
