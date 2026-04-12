"""
blueprints/dashboard.py
Tổng quan hệ thống (public) + tổng quan cá nhân (JWT).
Blueprint chỉ: parse request → gọi service → trả response.
"""
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.stats_service import StatsService

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _predictor():
    return current_app.config["PREDICTOR"]


@dashboard_bp.get("/overview")
def system_overview():
    return jsonify(_predictor().get_dashboard_overview())


@dashboard_bp.get("/personal")
@jwt_required()
def personal_dashboard():
    personal = StatsService.personal_overview(int(get_jwt_identity()))
    return jsonify({"personal": personal})
