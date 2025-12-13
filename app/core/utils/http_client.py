"""
Client HTTP pour les requêtes réseau.
"""

import requests
from typing import Optional, Dict, Any
from app.core.utils.logger import app_logger


class HTTPClient:
    """Client HTTP réutilisable."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Effectue une requête GET."""
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            app_logger.error(f"Erreur GET {url}: {e}")
            raise
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Effectue une requête POST."""
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            app_logger.error(f"Erreur POST {url}: {e}")
            raise
