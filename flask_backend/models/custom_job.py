import json
from datetime import datetime, timezone

from extensions import db


class CustomJob(db.Model):
    __tablename__ = "custom_jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_data_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

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
        data = self.job_data
        return {
            "id": self.id,
            "jobId": self.id,
            "title": data.get("title", ""),
            "jobTitle": data.get("title", ""),
            "companyName": data.get("companyName", ""),
            "nameCompany": data.get("companyName", ""),
            "companyOverview": data.get("companyOverview", ""),
            "companySize": data.get("companySize", ""),
            "companyAddress": data.get("companyAddress", ""),
            "description": data.get("description", ""),
            "requirements": data.get("requirements", ""),
            "benefits": data.get("benefits", ""),
            "jobAddress": data.get("address", ""),
            "address": data.get("address", ""),
            "location": data.get("address", ""),
            "jobType": data.get("jobType", ""),
            "gender": data.get("gender", ""),
            "candidates": data.get("candidates", 0),
            "numberCadidate": data.get("candidates", 0),
            "careerLevel": data.get("careerLevel", ""),
            "experience": data.get("experience", ""),
            "yearsOfExperience": data.get("experience", ""),
            "salary": data.get("salary", ""),
            "submissionDeadline": data.get("submissionDeadline", ""),
            "industry": data.get("industry", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "source": "custom",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
