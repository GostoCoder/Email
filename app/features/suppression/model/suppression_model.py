"""
Modèles pour les désabonnements.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from app.core.shared.models.base_model import BaseModel


@dataclass
class Unsubscribe(BaseModel):
    """Représente un désabonnement dans la liste de suppression."""
    email: str = ""
    reason: str = "unsubscribed"
    unsubscribed_at: datetime = None
    
    def __post_init__(self):
        if self.unsubscribed_at is None:
            self.unsubscribed_at = datetime.now()


@dataclass
class UnsubscribeLog(BaseModel):
    """Log d'un désabonnement pour audit et support."""
    email: str = ""
    contact_id: Optional[str] = None
    campaign_id: Optional[str] = None
    source: str = "email"  # email, manual, api, import
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UnsubscribeRequest:
    """Données d'une requête de désabonnement."""
    token: str
    email: Optional[str] = None
    contact_id: Optional[str] = None
    campaign_id: Optional[str] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UnsubscribeResult:
    """Résultat d'une opération de désabonnement."""
    success: bool
    email: Optional[str] = None
    message: str = ""
    error: Optional[str] = None
    already_unsubscribed: bool = False
