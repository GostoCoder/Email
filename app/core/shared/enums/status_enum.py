"""
Énumération des statuts d'email.
"""

from enum import Enum


class EmailStatus(Enum):
    """Statuts possibles d'un email."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class CampaignStatus(Enum):
    """Statuts possibles d'une campagne."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
