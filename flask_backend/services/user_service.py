"""
services/user_service.py
Business logic liên quan đến user: tạo tài khoản, xác thực, cập nhật profile.
Blueprints chỉ xử lý HTTP — mọi logic nằm ở đây.
"""
from __future__ import annotations
from extensions import db
from models import user as User


class UserService:

    # ------------------------------------------------------------------ #
    # Tạo tài khoản
    # ------------------------------------------------------------------ #

    @staticmethod
    def register(email: str, name: str, password: str) -> tuple[User, str | None]:
        """
        Tạo user mới.
        Trả về (user, error_message). Nếu error_message là None → thành công.
        """
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

    # ------------------------------------------------------------------ #
    # Xác thực
    # ------------------------------------------------------------------ #

    @staticmethod
    def authenticate(email: str, password: str) -> User | None:
        """Trả về User nếu đúng, None nếu sai."""
        user = User.query.filter_by(email=email.strip().lower()).first()
        if user and user.check_password(password):
            return user
        return None

    # ------------------------------------------------------------------ #
    # Cập nhật profile
    # ------------------------------------------------------------------ #

    # @staticmethod
    # def update_profile(user: User, data: dict) -> tuple[User, str | None]:
    #     """
    #     Cập nhật name và/hoặc preferences.
    #     data có thể chứa: name, preferences.keywords, preferences.jobTypes, preferences.preferredRisk
    #     """
    #     if "name" in data and str(data["name"]).strip():
    #         user.name = str(data["name"]).strip()

    #     prefs = data.get("preferences", {})
    #     if isinstance(prefs, dict):
    #         if "keywords" in prefs and isinstance(prefs["keywords"], list):
    #             user.keywords = [str(k).strip() for k in prefs["keywords"] if str(k).strip()]
    #         if "jobTypes" in prefs and isinstance(prefs["jobTypes"], list):
    #             user.job_types = [str(t).strip() for t in prefs["jobTypes"] if str(t).strip()]
    #         if "preferredRisk" in prefs and isinstance(prefs["preferredRisk"], list):
    #             valid = {"LOW", "MEDIUM", "HIGH"}
    #             user.preferred_risk = ",".join(r for r in prefs["preferredRisk"] if r in valid)

    #     db.session.commit()
    #     return user, None

    # ------------------------------------------------------------------ #
    # Đổi mật khẩu
    # ------------------------------------------------------------------ #

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> str | None:
        """Trả về None nếu thành công, error string nếu thất bại."""
        if not user.check_password(old_password):
            return "Mật khẩu hiện tại không đúng."
        if len(new_password) < 8:
            return "Mật khẩu mới phải có ít nhất 8 ký tự."
        user.set_password(new_password)
        db.session.commit()
        return None

    # ------------------------------------------------------------------ #
    # Lấy user
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email.strip().lower()).first()
