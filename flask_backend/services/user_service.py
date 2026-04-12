"""
services/user_service.py
Business logic liên quan đến user.
Tất cả logic nằm ở đây — blueprint không chứa bất kỳ business logic nào.
"""
from __future__ import annotations
from extensions import db
from models.user import User


class UserService:

    @staticmethod
    def register(email: str, name: str, password: str) -> tuple[User | None, str | None]:
        email = email.strip().lower()
        name  = name.strip()

        if not email or not name or not password:
            return None, "Vui lòng điền đầy đủ email, tên và mật khẩu."
        if len(password) < 8:
            return None, "Mật khẩu phải có ít nhất 8 ký tự."
        if User.query.filter_by(email=email).first():
            return None, "Email đã được sử dụng."

        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user, None

    @staticmethod
    def authenticate(email: str, password: str) -> tuple[User | None, str | None]:
        """Trả về (user, None) nếu đúng, (None, error) nếu sai."""
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user or not user.check_password(password.strip()):
            return None, "Email hoặc mật khẩu không đúng."
        return user, None

    @staticmethod
    def get_by_id(user_id: int) -> tuple[User | None, str | None]:
        user = User.query.get(user_id)
        if not user:
            return None, "Không tìm thấy người dùng."
        return user, None

    @staticmethod
    def get_by_email(email: str) -> tuple[User | None, str | None]:
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            return None, "Không tìm thấy người dùng."
        return user, None

    @staticmethod
    def update_profile(user: User, data: dict) -> tuple[User | None, str | None]:
        if "name" in data:
            name = str(data["name"]).strip()
            if not name:
                return None, "Tên không được để trống."
            user.name = name

        db.session.commit()
        return user, None

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> str | None:
        """Trả về None nếu thành công, error string nếu thất bại."""
        if not user.check_password(old_password):
            return "Mật khẩu hiện tại không đúng."
        if len(new_password) < 6:
            return "Mật khẩu mới phải có ít nhất 6 ký tự."
        user.set_password(new_password)
        db.session.commit()
        return None