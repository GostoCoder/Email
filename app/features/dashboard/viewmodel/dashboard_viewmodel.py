"""
ViewModel pour le dashboard.
"""

from typing import Dict, Any
from app.features.dashboard.service.dashboard_service import DashboardService


class DashboardViewModel:
    """ViewModel pour gérer la présentation du dashboard."""
    
    def __init__(self):
        self.service = DashboardService()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Récupère toutes les données du dashboard."""
        stats = self.service.get_statistics()
        
        return {
            'total_campaigns': stats.total_campaigns,
            'total_emails_sent': stats.total_emails_sent,
            'total_emails_failed': stats.total_emails_failed,
            'success_rate': round(stats.success_rate, 2),
            'recent_campaigns': stats.recent_campaigns
        }
