"""
Modèle de base pour tous les modèles de l'application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BaseModel:
    """Classe de base pour tous les modèles."""
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_timestamp(self):
        """Met à jour le timestamp de modification."""
        self.updated_at = datetime.now()
