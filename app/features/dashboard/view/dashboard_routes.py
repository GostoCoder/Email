"""
Routes Flask pour le dashboard.
"""

from flask import Blueprint, jsonify
from app.features.dashboard.viewmodel.dashboard_viewmodel import DashboardViewModel

dashboard_bp = Blueprint('dashboard', __name__)
dashboard_vm = DashboardViewModel()


@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """Récupère les statistiques du dashboard."""
    data = dashboard_vm.get_dashboard_data()
    return jsonify(data), 200
