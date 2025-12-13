"""
Modèle pour les statistiques du dashboard.
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
from app.core.shared.models.base_model import BaseModel


@dataclass
class DashboardStats(BaseModel):
    """Statistiques du dashboard."""
    total_campaigns: int = 0
    total_emails_sent: int = 0
    total_emails_failed: int = 0
    success_rate: float = 0.0
    recent_campaigns: List[Dict] = None
    
    def __post_init__(self):
        if self.recent_campaigns is None:
            self.recent_campaigns = []
    
    def calculate_success_rate(self):
        """Calcule le taux de succès global."""
        total = self.total_emails_sent + self.total_emails_failed
        if total > 0:
            self.success_rate = (self.total_emails_sent / total) * 100
