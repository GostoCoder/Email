"""
Modèle de la campagne d'emailing.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from app.core.shared.models.base_model import BaseModel
from app.core.shared.enums.status_enum import CampaignStatus


@dataclass
class Campaign(BaseModel):
    """Représente une campagne d'emailing."""
    name: str = ""
    subject: str = ""
    template_name: str = ""
    csv_file_path: str = ""
    status: CampaignStatus = CampaignStatus.DRAFT
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def progress(self) -> float:
        """Calcule le pourcentage de progression."""
        if self.total_recipients == 0:
            return 0.0
        return (self.sent_count + self.failed_count) / self.total_recipients * 100
    
    @property
    def success_rate(self) -> float:
        """Calcule le taux de succès."""
        total_processed = self.sent_count + self.failed_count
        if total_processed == 0:
            return 0.0
        return self.sent_count / total_processed * 100
