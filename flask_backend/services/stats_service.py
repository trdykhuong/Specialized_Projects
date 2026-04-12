from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from models.application import Application, ApplicationStatus
from models.saved_job import SavedJob

_STATUS_LABELS = {
    "saved":        "Chờ ứng tuyển",
    "applied":      "Đã ứng tuyển",
    "interviewing": "Đang phỏng vấn",
    "offered":      "Nhận được offer",
    "rejected":     "Bị từ chối"
}

_RISK_LABELS = {
    "LOW":    "Thấp",
    "MEDIUM": "Trung bình",
    "HIGH":   "Cao",
}


class StatsService:

    @staticmethod
    def personal_overview(user_id: int) -> dict:
        apps        = Application.query.filter_by(user_id=user_id).all()
        saved_count = SavedJob.query.filter_by(user_id=user_id).count()

        total        = len(apps)
        status_dist  = defaultdict(int)
        risk_dist    = defaultdict(int)
        trust_scores = []
        monthly      = defaultdict(int)

        for a in apps:
            status_dist[a.status.value if a.status else "unknown"] += 1
            if a.risk_level:
                risk_dist[a.risk_level] += 1
            if a.trust_score:
                trust_scores.append(a.trust_score)
            if a.applied_at:
                monthly[a.applied_at.strftime("%Y-%m")] += 1

        avg_trust    = round(sum(trust_scores) / len(trust_scores), 2) if trust_scores else 0
        offered      = status_dist.get(ApplicationStatus.OFFERED.value, 0)
        success_rate = round(offered / total * 100, 1) if total else 0

        return {
            "total":             total,
            "savedCount":        saved_count,
            "averageTrustScore": avg_trust,
            "successRate":       success_rate,
            "statusDistribution": [
                {"status": s, "label": _STATUS_LABELS.get(s, s), "count": c}
                for s, c in status_dist.items()
            ],
            "riskDistribution": [
                {"riskLevel": r, "label": _RISK_LABELS.get(r, r), "count": c}
                for r, c in risk_dist.items()
            ],
            "monthlyApplications": [
                {"month": k, "count": v}
                for k, v in sorted(monthly.items())
            ],
        }

    @staticmethod
    def risk_summary(user_id: int) -> dict:
        apps              = Application.query.filter_by(user_id=user_id).all()
        by_status         = defaultdict(list)
        high_risk_applied = 0

        for a in apps:
            key = a.status.value if a.status else "unknown"
            if a.trust_score:
                by_status[key].append(a.trust_score)
            if a.risk_level == "HIGH":
                high_risk_applied += 1

        avg_trust_by_status = {
            status: round(sum(scores) / len(scores), 2)
            for status, scores in by_status.items()
            if scores
        }
        return {
            "highRiskApplied":      high_risk_applied,
            "averageTrustByStatus": avg_trust_by_status,
        }

    @staticmethod
    def trend(user_id: int, months: int = 6) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
        apps   = (
            Application.query
            .filter_by(user_id=user_id)
            .filter(Application.applied_at >= cutoff)
            .all()
        )

        monthly_apply = defaultdict(int)
        monthly_offer = defaultdict(int)
        monthly_trust = defaultdict(list)

        for a in apps:
            if not a.applied_at:
                continue
            key = a.applied_at.strftime("%Y-%m")
            monthly_apply[key] += 1
            if a.status == ApplicationStatus.OFFERED:
                monthly_offer[key] += 1
            if a.trust_score:
                monthly_trust[key].append(a.trust_score)

        all_months = sorted(set(monthly_apply) | set(monthly_offer) | set(monthly_trust))
        return {
            "months": months,
            "trend": [
                {
                    "month":         m,
                    "applied":       monthly_apply.get(m, 0),
                    "offered":       monthly_offer.get(m, 0),
                    "avgTrustScore": round(sum(monthly_trust[m]) / len(monthly_trust[m]), 2)
                                     if monthly_trust.get(m) else 0,
                }
                for m in all_months
            ],
        }
