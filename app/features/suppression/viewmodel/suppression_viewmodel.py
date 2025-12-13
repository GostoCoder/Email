"""
ViewModel pour la gestion des désabonnements.
Sert d'intermédiaire entre les routes et le service.
"""

from typing import Dict, Any, Optional, List
from app.features.suppression.service.suppression_service import SuppressionService
from app.features.suppression.model.suppression_model import UnsubscribeRequest, UnsubscribeResult


class SuppressionViewModel:
    """ViewModel pour gérer la présentation des désabonnements."""
    
    def __init__(self):
        self.service = SuppressionService()
    
    def unsubscribe_command(
        self, 
        token: str, 
        reason: str = "",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Commande pour désabonner un email via token.
        
        Args:
            token: Le token de désabonnement
            reason: Raison optionnelle
            ip_address: IP de la requête (pour audit)
            user_agent: User-Agent du navigateur (pour audit)
            
        Returns:
            Dict avec success, message, email, etc.
        """
        request = UnsubscribeRequest(
            token=token,
            reason=reason if reason else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        result = self.service.process_unsubscribe(request)
        
        return {
            'success': result.success,
            'email': result.email,
            'message': result.message,
            'error': result.error,
            'already_unsubscribed': result.already_unsubscribed
        }
    
    def get_all_unsubscribed(self) -> Dict[str, Any]:
        """Récupère tous les emails désabonnés."""
        emails = self.service.get_all_unsubscribed()
        
        return {
            'success': True,
            'count': len(emails),
            'emails': sorted(list(emails))
        }
    
    def get_unsubscribe_logs(
        self,
        limit: int = 100,
        email: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les logs de désabonnements.
        
        Args:
            limit: Nombre max de logs
            email: Filtrer par email
            campaign_id: Filtrer par campagne
            
        Returns:
            Dict avec success et logs
        """
        logs = self.service.get_unsubscribe_logs(
            limit=limit,
            email=email,
            campaign_id=campaign_id
        )
        
        return {
            'success': True,
            'count': len(logs),
            'logs': logs
        }
    
    def add_unsubscribe_command(
        self, 
        email: str, 
        reason: str = "manual"
    ) -> Dict[str, Any]:
        """
        Commande pour ajouter manuellement un email à la liste de suppression.
        
        Args:
            email: L'email à désabonner
            reason: Raison du désabonnement
            
        Returns:
            Dict avec success et message
        """
        result = self.service.add_unsubscribe_manual(
            email=email,
            reason=reason,
            source='manual'
        )
        
        return {
            'success': result.success,
            'email': result.email,
            'message': result.message,
            'error': result.error,
            'already_unsubscribed': result.already_unsubscribed
        }
    
    def remove_unsubscribe_command(self, email: str) -> Dict[str, Any]:
        """Commande pour retirer un email de la liste de suppression."""
        success = self.service.remove_unsubscribe(email)
        
        return {
            'success': success,
            'email': email if success else None,
            'message': 'Email retiré de la liste de suppression' if success else 'Email non trouvé dans la liste'
        }
    
    def check_email_status(self, email: str) -> Dict[str, Any]:
        """
        Vérifie le statut de désabonnement d'un email.
        
        Args:
            email: L'email à vérifier
            
        Returns:
            Dict avec is_unsubscribed
        """
        is_unsubscribed = self.service.is_unsubscribed(email)
        
        return {
            'success': True,
            'email': email,
            'is_unsubscribed': is_unsubscribed
        }
    
    def generate_unsubscribe_url(
        self,
        email: str,
        contact_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Génère une URL de désabonnement pour un email.
        
        Args:
            email: L'email du contact
            contact_id: UUID du contact
            campaign_id: UUID de la campagne
            base_url: URL de base (optionnel)
            
        Returns:
            Dict avec l'URL générée
        """
        import os
        
        token = self.service.generate_unsubscribe_token(
            email=email,
            contact_id=contact_id,
            campaign_id=campaign_id
        )
        
        base = base_url or os.getenv('UNSUBSCRIBE_BASE_URL', 'http://localhost:5000')
        url = f"{base}/api/suppression/page/{token}"
        
        return {
            'success': True,
            'email': email,
            'token': token,
            'url': url
        }
