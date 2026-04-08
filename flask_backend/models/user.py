import json
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Personalization preferences (dùng cho recommend_jobs)
    preferred_risk = db.Column(db.String(50), default="LOW,MEDIUM")
    keywords_json = db.Column(db.Text, default="[]")
    job_types_json = db.Column(db.Text, default="[]")

    # Relationships
    applications = db.relationship("Application", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    saved_jobs = db.relationship("SavedJob", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")

    # ------------------------------------------------------------------ #
    # Auth helpers
    # ------------------------------------------------------------------ #

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------ #
    # Preference helpers
    # ------------------------------------------------------------------ #

    @property
    def keywords(self) -> list[str]:
        try:
            return json.loads(self.keywords_json or "[]")
        except (ValueError, TypeError):
            return []

    @keywords.setter
    def keywords(self, value: list[str]) -> None:
        self.keywords_json = json.dumps(value, ensure_ascii=False)

    @property
    def job_types(self) -> list[str]:
        try:
            return json.loads(self.job_types_json or "[]")
        except (ValueError, TypeError):
            return []

    @job_types.setter
    def job_types(self, value: list[str]) -> None:
        self.job_types_json = json.dumps(value, ensure_ascii=False)

    @property
    def preferred_risk_levels(self) -> list[str]:
        raw = str(self.preferred_risk or "").strip()
        if not raw:
            return ["LOW", "MEDIUM"]
        valid = {"LOW", "MEDIUM", "HIGH"}
        return [item for item in (part.strip().upper() for part in raw.split(",")) if item in valid] or ["LOW", "MEDIUM"]


    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #

    def to_dict(self, include_preferences: bool = False) -> dict:
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
        if include_preferences:
            data["preferences"] = {
                "keywords": self.keywords,
                "jobTypes": self.job_types,
                "preferredRisk": self.preferred_risk_levels,
            }
        return data
