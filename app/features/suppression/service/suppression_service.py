"""
Service de gestion des désabonnements.
Implémente la logique complète de désinscription avec:
- Mise à jour des contacts
- Ajout à la liste de suppression
- Mise à jour des campaign_contacts
- Incrémentation des statistiques de campagne
- Logging des désabonnements pour audit
"""

import os
from typing import List, Set, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
from app.features.suppression.model.suppression_model import (
    Unsubscribe, 
    UnsubscribeLog, 
    UnsubscribeRequest,
    UnsubscribeResult
)
from app.core.shared.services.token_service import TokenService
from app.core.shared.services.database_service import get_db
from app.core.config.settings import config
from app.core.utils.logger import app_logger


class SuppressionService:
    """Service pour gérer les désabonnements via Supabase."""
    
    def __init__(self):
        self.db = get_db()
        self.token_service = TokenService(os.getenv('SECRET_KEY', 'default-secret-key'))
    
    def process_unsubscribe(self, request: UnsubscribeRequest) -> UnsubscribeResult:
        """
        Traite une demande de désabonnement complète.
        
        Cette méthode:
        1. Valide le token
        2. Met à jour le contact (is_unsubscribed=true, is_active=false)
        3. Ajoute à la liste de suppressions
        4. Met à jour le statut dans campaign_contacts
        5. Incrémente unsubscribed_count dans la campagne
        6. Log l'événement pour audit
        
        Args:
            request: La requête de désabonnement
            
        Returns:
            UnsubscribeResult avec le statut de l'opération
        """
        # Valider le token et extraire les données
        is_valid, token_data = self.token_service.validate_unsubscribe_token(request.token)
        
        # Si le nouveau format échoue, essayer l'ancien format
        if not is_valid:
            is_valid, email = self.token_service.validate_token(request.token)
            if is_valid and email:
                token_data = {'email': email}
            else:
                return UnsubscribeResult(
                    success=False,
                    error="Token invalide ou expiré",
                    message="Le lien de désabonnement n'est plus valide."
                )
        
        email = token_data.get('email', '').lower().strip()
        contact_id = token_data.get('contact_id') or request.contact_id
        campaign_id = token_data.get('campaign_id') or request.campaign_id
        
        if not email:
            return UnsubscribeResult(
                success=False,
                error="Email manquant dans le token",
                message="Impossible de traiter la demande."
            )
        
        # Vérifier si déjà désabonné
        if self.is_unsubscribed(email):
            return UnsubscribeResult(
                success=True,
                email=email,
                message="Vous êtes déjà désabonné·e de notre liste de diffusion.",
                already_unsubscribed=True
            )
        
        try:
            # 1. Mettre à jour le contact
            self._update_contact(email, contact_id)
            
            # 2. Ajouter à la liste de suppression
            self._add_to_suppressions(email)
            
            # 3. Mettre à jour campaign_contacts si on a un campaign_id
            if campaign_id and contact_id:
                self._update_campaign_contact(campaign_id, contact_id)
                
                # 4. Incrémenter le compteur de la campagne
                self._increment_campaign_unsubscribe_count(campaign_id)
            
            # 5. Logger le désabonnement pour audit
            self._log_unsubscribe(
                email=email,
                contact_id=contact_id,
                campaign_id=campaign_id,
                source='email',
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                reason=request.reason
            )
            
            app_logger.info(f"Désabonnement réussi pour {email}")
            
            return UnsubscribeResult(
                success=True,
                email=email,
                message="Vous avez été désabonné·e avec succès. Vous ne recevrez plus nos communications."
            )
            
        except Exception as e:
            app_logger.error(f"Erreur lors du désabonnement de {email}: {e}")
            return UnsubscribeResult(
                success=False,
                email=email,
                error=str(e),
                message="Une erreur est survenue. Veuillez réessayer ou nous contacter."
            )
    
    def _update_contact(self, email: str, contact_id: Optional[str] = None):
        """Met à jour le contact comme désabonné."""
        try:
            update_data = {
                'is_unsubscribed': True,
                'is_active': False,
                'unsubscribed_at': datetime.now().isoformat()
            }
            
            if contact_id:
                self.db.update('contacts', update_data, {'id': contact_id})
            else:
                # Rechercher par email
                contacts = self.db.select('contacts', filters={'email': email})
                if contacts:
                    self.db.update('contacts', update_data, {'email': email})
                    
        except Exception as e:
            app_logger.warning(f"Erreur mise à jour contact {email}: {e}")
    
    def _add_to_suppressions(self, email: str):
        """Ajoute l'email à la liste de suppression."""
        try:
            # Vérifier si déjà présent
            existing = self.db.select('suppressions', filters={'email': email})
            if not existing:
                self.db.insert('suppressions', {
                    'email': email,
                    'reason': 'unsubscribed'
                })
        except Exception as e:
            app_logger.error(f"Erreur ajout suppression {email}: {e}")
            raise
    
    def _update_campaign_contact(self, campaign_id: str, contact_id: str):
        """Met à jour le statut dans campaign_contacts."""
        try:
            self.db.update(
                'campaign_contacts',
                {
                    'status': 'unsubscribed',
                    'updated_at': datetime.now().isoformat()
                },
                {
                    'campaign_id': campaign_id,
                    'contact_id': contact_id
                }
            )
            
            # Ajouter un événement
            campaign_contacts = self.db.select(
                'campaign_contacts',
                filters={
                    'campaign_id': campaign_id,
                    'contact_id': contact_id
                }
            )
            
            if campaign_contacts:
                self.db.insert('email_events', {
                    'campaign_contact_id': campaign_contacts[0]['id'],
                    'event_type': 'unsubscribed'
                })
                
        except Exception as e:
            app_logger.warning(f"Erreur mise à jour campaign_contact: {e}")
    
    def _increment_campaign_unsubscribe_count(self, campaign_id: str):
        """Incrémente le compteur de désabonnements de la campagne."""
        try:
            # Récupérer le compteur actuel
            campaigns = self.db.select('campaigns', filters={'id': campaign_id})
            if campaigns:
                current_count = campaigns[0].get('unsubscribed_count', 0) or 0
                self.db.update(
                    'campaigns',
                    {'unsubscribed_count': current_count + 1},
                    {'id': campaign_id}
                )
        except Exception as e:
            app_logger.warning(f"Erreur incrémentation compteur campagne: {e}")
    
    def _log_unsubscribe(
        self,
        email: str,
        contact_id: Optional[str],
        campaign_id: Optional[str],
        source: str = 'email',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log le désabonnement pour audit."""
        try:
            log_data = {
                'email': email,
                'source': source
            }
            
            if contact_id:
                log_data['contact_id'] = contact_id
            if campaign_id:
                log_data['campaign_id'] = campaign_id
            if ip_address:
                log_data['ip_address'] = ip_address
            if user_agent:
                log_data['user_agent'] = user_agent[:500] if user_agent else None
            if reason:
                log_data['reason'] = reason
            
            self.db.insert('unsubscribe_logs', log_data)
            
        except Exception as e:
            # Ne pas faire échouer le désabonnement si le log échoue
            app_logger.warning(f"Erreur log désabonnement: {e}")
    
    def add_unsubscribe(self, email: str, reason: str = "unsubscribed") -> Unsubscribe:
        """Ajoute un email à la liste de suppression (méthode legacy)."""
        email = email.strip().lower()
        
        if not self.is_unsubscribed(email):
            try:
                self.db.insert('suppressions', {
                    'email': email,
                    'reason': reason
                })
                app_logger.info(f"Email {email} ajouté à la liste de suppression")
                
                # Marquer le contact comme désabonné s'il existe
                self._update_contact(email)
                
                # Logger manuellement
                self._log_unsubscribe(
                    email=email,
                    contact_id=None,
                    campaign_id=None,
                    source='manual'
                )
                    
            except Exception as e:
                app_logger.error(f"Erreur ajout suppression: {e}")
                raise
        
        return Unsubscribe(email=email, reason=reason)
    
    def add_unsubscribe_manual(
        self, 
        email: str, 
        reason: str = "manual",
        source: str = "manual"
    ) -> UnsubscribeResult:
        """
        Ajoute manuellement un email à la liste de suppression (admin).
        
        Args:
            email: L'email à désabonner
            reason: Raison du désabonnement
            source: Source (manual, import, api)
            
        Returns:
            UnsubscribeResult
        """
        email = email.strip().lower()
        
        if self.is_unsubscribed(email):
            return UnsubscribeResult(
                success=True,
                email=email,
                message="Email déjà dans la liste de suppression",
                already_unsubscribed=True
            )
        
        try:
            # Trouver le contact_id si le contact existe
            contact_id = None
            contacts = self.db.select('contacts', filters={'email': email})
            if contacts:
                contact_id = contacts[0]['id']
            
            # Ajouter à la suppression
            self._add_to_suppressions(email)
            
            # Mettre à jour le contact
            self._update_contact(email, contact_id)
            
            # Logger
            self._log_unsubscribe(
                email=email,
                contact_id=contact_id,
                campaign_id=None,
                source=source,
                reason=reason
            )
            
            return UnsubscribeResult(
                success=True,
                email=email,
                message=f"Email {email} ajouté à la liste de suppression"
            )
            
        except Exception as e:
            app_logger.error(f"Erreur ajout manuel: {e}")
            return UnsubscribeResult(
                success=False,
                email=email,
                error=str(e),
                message="Erreur lors de l'ajout"
            )
    
    def is_unsubscribed(self, email: str) -> bool:
        """Vérifie si un email est désabonné."""
        email = email.strip().lower()
        try:
            result = self.db.select('suppressions', filters={'email': email})
            return len(result) > 0
        except Exception as e:
            app_logger.error(f"Erreur vérification suppression: {e}")
            return False
    
    def get_all_unsubscribed(self) -> Set[str]:
        """Récupère tous les emails désabonnés depuis Supabase."""
        try:
            result = self.db.select('suppressions', columns='email')
            return {item['email'] for item in result}
        except Exception as e:
            app_logger.error(f"Erreur lecture liste suppression: {e}")
            return set()
    
    def get_unsubscribe_logs(
        self, 
        limit: int = 100,
        email: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les logs de désabonnements.
        
        Args:
            limit: Nombre maximum de logs à retourner
            email: Filtrer par email
            campaign_id: Filtrer par campagne
            
        Returns:
            Liste des logs
        """
        try:
            query = self.db.client.table('unsubscribe_logs').select('*')
            
            if email:
                query = query.eq('email', email.lower())
            if campaign_id:
                query = query.eq('campaign_id', campaign_id)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            app_logger.error(f"Erreur lecture logs: {e}")
            return []
    
    def remove_unsubscribe(self, email: str) -> bool:
        """Retire un email de la liste de suppression."""
        email = email.strip().lower()
        
        try:
            if self.is_unsubscribed(email):
                self.db.delete('suppressions', {'email': email})
                
                # Remettre le contact comme actif s'il existe
                try:
                    contacts = self.db.select('contacts', filters={'email': email})
                    if contacts:
                        self.db.update(
                            'contacts',
                            {
                                'is_unsubscribed': False,
                                'is_active': True,
                                'unsubscribed_at': None
                            },
                            {'email': email}
                        )
                except Exception as e:
                    app_logger.warning(f"Contact non trouvé pour {email}: {e}")
                
                app_logger.info(f"Email {email} retiré de la liste de suppression")
                return True
        except Exception as e:
            app_logger.error(f"Erreur retrait suppression: {e}")
            return False
        
        return False
    
    def validate_unsubscribe_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Valide un token de désabonnement (méthode legacy)."""
        return self.token_service.validate_token(token)
    
    def generate_unsubscribe_token(
        self,
        email: str,
        contact_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        expiry_days: int = 30
    ) -> str:
        """
        Génère un token de désabonnement.
        
        Args:
            email: L'email du contact
            contact_id: UUID du contact
            campaign_id: UUID de la campagne
            expiry_days: Validité en jours
            
        Returns:
            Le token généré
        """
        return self.token_service.generate_unsubscribe_token(
            email=email,
            contact_id=contact_id,
            campaign_id=campaign_id,
            expiry_days=expiry_days
        )


# Instance globale pour faciliter l'import
_suppression_service = None

def get_suppression_service() -> SuppressionService:
    """Retourne l'instance singleton du service de suppression."""
    global _suppression_service
    if _suppression_service is None:
        _suppression_service = SuppressionService()
    return _suppression_service
