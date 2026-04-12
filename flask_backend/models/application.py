import json
import enum
from datetime import datetime, timezone
from extensions import db


class ApplicationStatus(str, enum.Enum):
    SAVED = "saved"                 # Đã lưu, chưa ứng tuyển (từ saved_jobs chuyển qua)
    APPLIED = "applied"             # Đã ứng tuyển
    INTERVIEWING = "interviewing"   # Đang phỏng vấn
    OFFERED = "offered"             # Đã nhận offer
    REJECTED = "rejected"           # Bị từ chối
    WITHDRAWN = "withdrawn"         # Tự rút đơn


class Application(db.Model):
    """
    Theo dõi từng lần ứng tuyển của người dùng.
    job_data lưu snapshot JSON của tin tuyển dụng tại thời điểm apply
    để không phụ thuộc vào dataset có còn hay không.
    """
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # job_id nếu lấy từ dataset, NULL nếu user tự nhập
    job_id = db.Column(db.Integer, nullable=True, index=True)
    # Snapshot toàn bộ thông tin job (title, company, salary, v.v.)
    job_data_json = db.Column(db.Text, nullable=False, default="{}")

    # Trạng thái ứng tuyển
    status = db.Column(db.Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.APPLIED)

    # Thông tin đánh giá cá nhân
    note = db.Column(db.Text, default="")           # Ghi chú tự do
    personal_rating = db.Column(db.Integer, nullable=True)  # 1–5 sao

    # Điểm rủi ro tại thời điểm apply (lưu để thống kê)
    risk_score = db.Column(db.Float, default=0.0)
    trust_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default="")

    # Timestamps
    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = db.relationship("User", back_populates="applications")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @property
    def job_data(self) -> dict:
        try:
            return json.loads(self.job_data_json or "{}")
        except (ValueError, TypeError):
            return {}

    @job_data.setter
    def job_data(self, value: dict) -> None:
        self.job_data_json = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict:
        jd = self.job_data
        display_status = _display_status(self.status)
        return {
            "id": self.id,
            "userId": self.user_id,
            "jobId": self.job_id,
            "job": {
                "title": jd.get("title", ""),
                "jobTitle": jd.get("jobTitle", jd.get("title", "")),
                "companyName": jd.get("companyName", ""),
                "nameCompany": jd.get("nameCompany", jd.get("companyName", "")),
                "companyOverview": jd.get("companyOverview", ""),
                "companySize": jd.get("companySize", ""),
                "companyAddress": jd.get("companyAddress", ""),
                "description": jd.get("description", ""),
                "requirements": jd.get("requirements", ""),
                "benefits": jd.get("benefits", ""),
                "salary": jd.get("salary", ""),
                "location": jd.get("location", ""),
                "address": jd.get("address", jd.get("location", "")),
                "jobAddress": jd.get("jobAddress", jd.get("address", jd.get("location", ""))),
                "email": jd.get("email", ""),
                "phone": jd.get("phone", ""),
                "jobType": jd.get("jobType", ""),
                "gender": jd.get("gender", ""),
                "candidates": jd.get("candidates", jd.get("numberCadidate", "")),
                "numberCadidate": jd.get("numberCadidate", jd.get("candidates", "")),
                "careerLevel": jd.get("careerLevel", ""),
                "experience": jd.get("experience", jd.get("yearsOfExperience", "")),
                "yearsOfExperience": jd.get("yearsOfExperience", jd.get("experience", "")),
                "submissionDeadline": jd.get("submissionDeadline", ""),
                "industry": jd.get("industry", ""),
            },
            "status": display_status,
            "statusLabel": _STATUS_LABELS.get(display_status, ""),
            "note": self.note or "",
            "personalRating": self.personal_rating,
            "riskScore": self.risk_score,
            "trustScore": self.trust_score,
            "riskLevel": self.risk_level,
            "appliedAt": self.applied_at.isoformat() if self.applied_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


_STATUS_LABELS = {
    "saved": "Chờ ứng tuyển",
    "applied": "Đã ứng tuyển",
    "interviewing": "Đang phỏng vấn",
    "offered": "Nhận được offer",
    "rejected": "Bị từ chối",
    "withdrawn": "Đã rút đơn",
}


def _display_status(status: ApplicationStatus | None) -> str | None:
    if not status:
        return None
    if status == ApplicationStatus.SAVED:
        return ApplicationStatus.APPLIED.value
    return status.value
