"""
services/application_service.py
CRUD và business logic cho việc theo dõi ứng tuyển (Application)
và tin lưu để ứng tuyển sau (SavedJob).
"""
from __future__ import annotations
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.application import ApplicationStatus, Application
from models.saved_job import SavedJob


class ApplicationService:

    # ================================================================== #
    # Application — theo dõi ứng tuyển
    # ================================================================== #

    @staticmethod
    def list_applications(
        user_id: int,
        status_filter: str = "",
        page: int = 1,
        page_size: int = 20,
    ):
        """Trả về dict phân trang chứa danh sách application của user."""
        query = Application.query.filter_by(user_id=user_id)
        if status_filter and status_filter in {s.value for s in ApplicationStatus}:
            query = query.filter_by(status=ApplicationStatus(status_filter))

        query     = query.order_by(Application.applied_at.desc())
        paginated = query.paginate(page=page, per_page=page_size, error_out=False)

        return {
            "items":       [a.to_dict() for a in paginated.items],
            "total":       paginated.total,
            "page":        page,
            "pageSize":    page_size,
            "totalPages":  paginated.pages,
            "hasNext":     paginated.has_next,
            "hasPrevious": paginated.has_prev,
        }

    @staticmethod
    def create_application(user_id: int, data: dict) -> tuple[Application | None, str | None]:
        """
        Tạo một bản ghi ứng tuyển mới.
        data: { job, jobId?, status?, note?, personalRating?, riskScore?, trustScore?, riskLevel? }
        """
        job_data = data.get("job", {})
        if not job_data or not job_data.get("title"):
            return None, "Thiếu thông tin tin tuyển dụng (job.title bắt buộc)."

        status_val = data.get("status", ApplicationStatus.APPLIED.value)
        if status_val not in {s.value for s in ApplicationStatus}:
            return None, f"Trạng thái không hợp lệ."

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
        return app, None

    @staticmethod
    def get_application(app_id: int, user_id: int) -> Application | None:
        return Application.query.filter_by(id=app_id, user_id=user_id).first()

    @staticmethod
    def update_application(app: Application, data: dict) -> tuple[Application | None, str | None]:
        if "status" in data:
            if data["status"] not in {s.value for s in ApplicationStatus}:
                return None, "Trạng thái không hợp lệ."
            app.status = ApplicationStatus(data["status"])
        if "note" in data:
            app.note = str(data["note"]).strip()
        if "personalRating" in data:
            app.personal_rating = _parse_rating(data["personalRating"])
        db.session.commit()
        return app, None

    @staticmethod
    def delete_application(app: Application) -> None:
        db.session.delete(app)
        db.session.commit()

    # ================================================================== #
    # SavedJob — lưu để ứng tuyển sau
    # ================================================================== #

    @staticmethod
    def list_saved_jobs(user_id: int, page: int = 1, page_size: int = 20):
        paginated = (
            SavedJob.query
            .filter_by(user_id=user_id)
            .order_by(SavedJob.saved_at.desc())
            .paginate(page=page, per_page=page_size, error_out=False)
        )
        return {
            "items":       [s.to_dict() for s in paginated.items],
            "total":       paginated.total,
            "page":        page,
            "pageSize":    page_size,
            "totalPages":  paginated.pages,
            "hasNext":     paginated.has_next,
            "hasPrevious": paginated.has_prev,
        }

    @staticmethod
    def save_job(user_id: int, data: dict) -> tuple[SavedJob | None, str | None]:
        job_data = data.get("job", {})
        if not job_data or not job_data.get("title"):
            return None, "Thiếu thông tin tin tuyển dụng."

        saved = SavedJob(
            user_id=user_id,
            job_id=data.get("jobId"),
            note=str(data.get("note", "")).strip(),
            risk_score=float(data.get("riskScore", 0) or 0),
            trust_score=float(data.get("trustScore", 0) or 0),
            risk_level=str(data.get("riskLevel", "")).strip(),
        )
        saved.job_data = job_data

        try:
            db.session.add(saved)
            db.session.commit()
            return saved, None
        except IntegrityError:
            db.session.rollback()
            return None, "Tin này đã được lưu trước đó."

    @staticmethod
    def get_saved_job(saved_id: int, user_id: int) -> SavedJob | None:
        return SavedJob.query.filter_by(id=saved_id, user_id=user_id).first()

    @staticmethod
    def update_saved_job(saved: SavedJob, data: dict) -> SavedJob:
        if "note" in data:
            saved.note = str(data["note"]).strip()
        db.session.commit()
        return saved

    @staticmethod
    def delete_saved_job(saved: SavedJob) -> None:
        db.session.delete(saved)
        db.session.commit()

    @staticmethod
    def apply_from_saved(saved: SavedJob, extra_note: str = "") -> Application:
        """
        Chuyển SavedJob → Application (status = APPLIED), xóa SavedJob.
        """
        app = Application(
            user_id=saved.user_id,
            job_id=saved.job_id,
            status=ApplicationStatus.APPLIED,
            note=extra_note or saved.note or "",
            risk_score=saved.risk_score,
            trust_score=saved.trust_score,
            risk_level=saved.risk_level,
        )
        app.job_data = saved.job_data
        db.session.add(app)
        db.session.delete(saved)
        db.session.commit()
        return app


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _parse_rating(value) -> int | None:
    if value is None:
        return None
    try:
        r = int(value)
        return r if 1 <= r <= 5 else None
    except (ValueError, TypeError):
        return None
