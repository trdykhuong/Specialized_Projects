"""
blueprints/dashboard.py
Tổng quan hệ thống (public) + tổng quan cá nhân (yêu cầu JWT).
"""
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _predictor():
    return current_app.config["PREDICTOR"]


# ------------------------------------------------------------------ #
# Tổng quan hệ thống — giữ nguyên từ code gốc, chỉ chuyển sang blueprint
# ------------------------------------------------------------------ #

# @dashboard_bp.get("/overview")
# def system_overview():
#     """
#     Thống kê toàn bộ dataset: tổng job, phân bố rủi ro,
#     top công ty, top lý do nghi ngờ.
#     """
#     return jsonify(_predictor().get_dashboard_overview())


# ------------------------------------------------------------------ #
# Tổng quan cá nhân — kết hợp system stats + personal stats
# ------------------------------------------------------------------ #

@dashboard_bp.get("/personal")
@jwt_required()
def personal_dashboard():
    """
    Trả về một dict gộp:
    - system:   tổng quan dataset (giống /overview)
    - personal: thống kê ứng tuyển cá nhân của user hiện tại
    """
    from models import Application, SavedJob, ApplicationStatus
    from collections import defaultdict

    user_id = int(get_jwt_identity())

    # --- Personal stats --- #
    apps = Application.query.filter_by(user_id=user_id).all()
    saved_count = SavedJob.query.filter_by(user_id=user_id).count()

    total = len(apps)
    status_dist: dict[str, int] = defaultdict(int)
    risk_dist:   dict[str, int] = defaultdict(int)
    trust_scores: list[float]   = []
    monthly: dict[str, int]     = defaultdict(int)

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

    personal = {
        "totalApplications": total,
        "savedJobsCount": saved_count,
        "averageTrustScore": avg_trust,
        "successRate": success_rate,
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

    return jsonify({
        "personal": personal,
    })


# ------------------------------------------------------------------ #
# Labels
# ------------------------------------------------------------------ #

_STATUS_LABELS = {
    "saved": "Chờ ứng tuyển",
    "applied": "Đã ứng tuyển",
    "interviewing": "Đang phỏng vấn",
    "offered": "Nhận được offer",
    "rejected": "Bị từ chối",
    "withdrawn": "Đã rút đơn",
}

_RISK_LABELS = {
    "LOW": "Thấp",
    "MEDIUM": "Trung bình",
    "HIGH": "Cao",
}
