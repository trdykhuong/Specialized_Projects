"""
blueprints/stats.py
Thống kê cá nhân của người dùng dựa trên dữ liệu applications và saved_jobs.
"""
from collections import defaultdict
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from extensions import db
from models.application import Application, ApplicationStatus
from models.saved_job import SavedJob
stats_bp = Blueprint("statistics", __name__, url_prefix="/api/statistics")


@stats_bp.get("/overview")
@jwt_required()
def personal_overview():
    """
    Tổng quan thống kê cá nhân:
    - Tổng số lần apply
    - Phân bố trạng thái
    - Phân bố mức rủi ro của các tin đã apply
    - Điểm trust trung bình
    - Số tin đang chờ (saved_jobs)
    - Tiến trình theo tháng (apply mới mỗi tháng)
    """
    user_id = int(get_jwt_identity())

    apps = Application.query.filter_by(user_id=user_id).all()
    saved_count = SavedJob.query.filter_by(user_id=user_id).count()

    total = len(apps)
    status_dist: dict[str, int] = defaultdict(int)
    monthly: dict[str, int] = defaultdict(int)

    for a in apps:
        status_key = _normalize_status(a.status.value if a.status else "unknown")
        status_dist[status_key] += 1
        if a.applied_at:
            month_key = a.applied_at.strftime("%Y-%m")
            monthly[month_key] += 1

    # Tỷ lệ thành công (offered / total)
    offered = status_dist.get(ApplicationStatus.OFFERED.value, 0)
    success_rate = round(offered / total * 100, 1) if total else 0

    # Sắp xếp monthly theo thứ tự thời gian
    sorted_monthly = [
        {"month": k, "count": v}
        for k, v in sorted(monthly.items())
    ]

    return jsonify({
        "total": total,
        "savedCount": saved_count,
        "successRate": success_rate,
        "statusDistribution": [
            {
                "status": status,
                "label": _STATUS_LABELS.get(status, status),
                "count": count,
            }
            for status, count in status_dist.items()
        ],
        "monthlyApplications": sorted_monthly,
    })


@stats_bp.get("/risk-summary")
@jwt_required()
def risk_summary():
    """
    Phân tích rủi ro trong lịch sử apply của user:
    - Bao nhiêu tin rủi ro cao mà vẫn apply
    - Điểm trust trung bình theo từng trạng thái
    """
    user_id = int(get_jwt_identity())
    apps = Application.query.filter_by(user_id=user_id).all()

    by_status: dict[str, list[float]] = defaultdict(list)
    high_risk_applied = 0

    for a in apps:
        status_key = _normalize_status(a.status.value if a.status else "unknown")
        if a.trust_score:
            by_status[status_key].append(a.trust_score)
        if a.risk_level == "HIGH":
            high_risk_applied += 1

    avg_trust_by_status = {
        status: round(sum(scores) / len(scores), 2)
        for status, scores in by_status.items()
        if scores
    }

    return jsonify({
        "highRiskApplied": high_risk_applied,
        "averageTrustByStatus": avg_trust_by_status,
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


def _normalize_status(status: str) -> str:
    return "applied" if status == "saved" else status
