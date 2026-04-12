"""
blueprints/stats.py
Thống kê cá nhân.
Blueprint chỉ: parse request → gọi service → trả response.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.stats_service import StatsService

stats_bp = Blueprint("statistics", __name__, url_prefix="/api/statistics")


@stats_bp.get("/overview")
@jwt_required()
def personal_overview():
    return jsonify(StatsService.personal_overview(int(get_jwt_identity())))


@stats_bp.get("/risk-summary")
@jwt_required()
def risk_summary():
    return jsonify(StatsService.risk_summary(int(get_jwt_identity())))


@stats_bp.get("/trend")
@jwt_required()
def trend():
    months = min(max(int(request.args.get("months", 6)), 1), 24)
    return jsonify(StatsService.trend(int(get_jwt_identity()), months=months))
