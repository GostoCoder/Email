"""
Modèle pour les templates d'emails.
"""

from dataclasses import dataclass
from typing import Optional
from app.core.shared.models.base_model import BaseModel


@dataclass
class EmailTemplate(BaseModel):
    """Représente un template d'email."""
    name: str = ""
    subject: str = ""
    html_content: str = ""
    text_content: str = ""
    preview_text: Optional[str] = None
    category: str = "general"
