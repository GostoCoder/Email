"""
Modèle pour représenter un email.
"""

from dataclasses import dataclass
from typing import Optional, List
from app.core.shared.models.base_model import BaseModel


@dataclass
class Email(BaseModel):
    """Représente un email."""
    to: str
    subject: str
    body_html: str
    body_text: str
    from_email: str
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
