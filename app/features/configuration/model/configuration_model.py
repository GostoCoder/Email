"""
Modèle de configuration.
"""

from dataclasses import dataclass
from app.core.shared.models.base_model import BaseModel


@dataclass
class AppConfiguration(BaseModel):
    """Configuration de l'application."""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    sender_name: str = ""
    sender_email: str = ""
    unsubscribe_base_url: str = "http://localhost:5000"
    rate_limit: str = "20"
    max_retries: str = "3"
    num_workers: str = "4"
    debug_mode: str = "false"
    test_email: str = ""
