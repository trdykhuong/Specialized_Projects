import json
from datetime import datetime, timezone
from extensions import db


class SavedJob(db.Model):
    """
    Tin tuyển dụng người dùng lưu lại để ứng tuyển sau.
    Khác với Application: chưa có hành động apply nào.
    """
    __tablename__ = "saved_jobs"
    __table_args__ = (
        db.UniqueConstraint("user_id", "job_id", name="uq_saved_user_job"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = db.Column(db.Integer, nullable=True, index=True)   # NULL nếu user tự nhập
    job_data_json = db.Column(db.Text, nullable=False, default="{}")

    # Ghi chú nhanh (tại sao muốn apply, deadline, v.v.)
    note = db.Column(db.Text, default="")

    # Điểm rủi ro snapshot
    risk_score = db.Column(db.Float, default=0.0)
    trust_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default="")

    saved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship("User", back_populates="saved_jobs")

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
        return {
            "id": self.id,
            "userId": self.user_id,
            "jobId": self.job_id,
            "job": {
                "title": jd.get("title", ""),
                "companyName": jd.get("companyName", ""),
                "salary": jd.get("salary", ""),
                "location": jd.get("location", ""),
            },
            "note": self.note or "",
            "riskScore": self.risk_score,
            "trustScore": self.trust_score,
            "riskLevel": self.risk_level,
            "savedAt": self.saved_at.isoformat() if self.saved_at else None,
        }
