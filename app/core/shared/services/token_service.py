"""
Service de gestion des tokens de désinscription.
Supporte les tokens simples (email) et enrichis (avec contact_id et campaign_id).
"""

import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from urllib.parse import quote, unquote


class TokenService:
    """Service pour gérer les tokens sécurisés de désinscription."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_token(self, email: str, expiry_days: int = 30) -> str:
        """
        Génère un token sécurisé simple pour un email.
        
        Args:
            email: L'adresse email
            expiry_days: Nombre de jours de validité
            
        Returns:
            Le token généré
        """
        timestamp = int((datetime.now() + timedelta(days=expiry_days)).timestamp())
        message = f"{email}:{timestamp}".encode('utf-8')
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        return f"{email}:{timestamp}:{signature}"
    
    def generate_unsubscribe_token(
        self, 
        email: str, 
        contact_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        expiry_days: int = 30
    ) -> str:
        """
        Génère un token enrichi de désinscription contenant email, contact_id et campaign_id.
        
        Args:
            email: L'adresse email du destinataire
            contact_id: L'UUID du contact dans la base
            campaign_id: L'UUID de la campagne (pour tracking)
            expiry_days: Nombre de jours de validité (défaut: 30)
            
        Returns:
            Le token encodé en base64 URL-safe
        """
        timestamp = int((datetime.now() + timedelta(days=expiry_days)).timestamp())
        
        # Construire le payload
        payload = {
            'email': email,
            'exp': timestamp
        }
        
        if contact_id:
            payload['contact_id'] = contact_id
        if campaign_id:
            payload['campaign_id'] = campaign_id
        
        # Encoder le payload en JSON puis en base64
        payload_json = json.dumps(payload, separators=(',', ':'))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
        
        # Créer la signature
        signature = hmac.new(
            self.secret_key, 
            payload_b64.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()[:32]  # Tronquer pour un token plus court
        
        return f"{payload_b64}.{signature}"
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Valide un token (simple ou enrichi) et retourne l'email associé.
        
        Args:
            token: Le token à valider
            
        Returns:
            Tuple (valide, email)
        """
        # Essayer d'abord le nouveau format enrichi
        is_valid, data = self.validate_unsubscribe_token(token)
        if is_valid and data:
            return True, data.get('email')
        
        # Fallback sur l'ancien format simple
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False, None
            
            email, timestamp_str, signature = parts
            timestamp = int(timestamp_str)
            
            # Vérifier l'expiration
            if datetime.now().timestamp() > timestamp:
                return False, None
            
            # Vérifier la signature
            message = f"{email}:{timestamp}".encode('utf-8')
            expected_signature = hmac.new(
                self.secret_key, message, hashlib.sha256
            ).hexdigest()
            
            if signature != expected_signature:
                return False, None
            
            return True, email
            
        except (ValueError, IndexError):
            return False, None
    
    def validate_unsubscribe_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Valide un token enrichi et retourne toutes les données qu'il contient.
        
        Args:
            token: Le token à valider (format: payload_b64.signature)
            
        Returns:
            Tuple (valide, dict avec email, contact_id, campaign_id si présents)
        """
        try:
            # Séparer payload et signature
            if '.' not in token:
                return False, None
            
            parts = token.split('.')
            if len(parts) != 2:
                return False, None
            
            payload_b64, signature = parts
            
            # Vérifier la signature
            expected_signature = hmac.new(
                self.secret_key, 
                payload_b64.encode('utf-8'), 
                hashlib.sha256
            ).hexdigest()[:32]
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, None
            
            # Décoder le payload (ajouter le padding base64 si nécessaire)
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            
            payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
            payload = json.loads(payload_json)
            
            # Vérifier l'expiration
            exp = payload.get('exp', 0)
            if datetime.now().timestamp() > exp:
                return False, None
            
            return True, payload
            
        except (ValueError, json.JSONDecodeError, Exception):
            return False, None
