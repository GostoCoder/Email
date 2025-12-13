"""
ViewModel pour la campagne.
"""

from typing import Dict, Any, Optional
from app.features.campaign.model.campaign_model import Campaign
from app.features.campaign.service.campaign_service import CampaignService
from app.core.shared.enums.status_enum import CampaignStatus


class CampaignViewModel:
    """ViewModel pour gérer la logique de présentation des campagnes."""
    
    def __init__(self):
        self.service = CampaignService()
        self.current_campaign: Optional[Campaign] = None
    
    def create_campaign_command(
        self, 
        name: str, 
        subject: str, 
        template_name: str, 
        csv_file_path: str
    ) -> Dict[str, Any]:
        """Commande pour créer une campagne."""
        try:
            self.current_campaign = self.service.create_campaign(
                name, subject, template_name, csv_file_path
            )
            return {
                'success': True,
                'campaign': self._serialize_campaign(self.current_campaign)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_campaign_command(self) -> Dict[str, Any]:
        """Commande pour démarrer l'envoi d'une campagne."""
        if not self.current_campaign:
            return {
                'success': False,
                'error': 'Aucune campagne active'
            }
        
        result = self.service.send_campaign(self.current_campaign)
        return {
            'success': result['status'] == CampaignStatus.COMPLETED.value,
            'stats': result
        }
    
    def get_campaign_status(self) -> Dict[str, Any]:
        """Récupère le statut de la campagne actuelle."""
        if not self.current_campaign:
            return {
                'active': False
            }
        
        return {
            'active': True,
            'campaign': self._serialize_campaign(self.current_campaign),
            'progress': self.current_campaign.progress,
            'success_rate': self.current_campaign.success_rate
        }
    
    def _serialize_campaign(self, campaign: Campaign) -> Dict[str, Any]:
        """Sérialise une campagne pour la vue."""
        return {
            'id': campaign.id,
            'name': campaign.name,
            'subject': campaign.subject,
            'template_name': campaign.template_name,
            'status': campaign.status.value,
            'total_recipients': campaign.total_recipients,
            'sent_count': campaign.sent_count,
            'failed_count': campaign.failed_count,
            'progress': campaign.progress,
            'success_rate': campaign.success_rate,
            'started_at': campaign.started_at.isoformat() if campaign.started_at else None,
            'completed_at': campaign.completed_at.isoformat() if campaign.completed_at else None
        }
