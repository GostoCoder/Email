"""
Service pour récupérer les statistiques du dashboard.
"""

from typing import Dict, Any, List
from app.features.dashboard.model.dashboard_model import DashboardStats
from app.core.shared.services.database_service import get_db
from app.core.utils.logger import app_logger


class DashboardService:
    """Service pour gérer les données du dashboard."""
    
    def __init__(self):
        self.db = get_db()
    
    def get_statistics(self) -> DashboardStats:
        """Récupère les statistiques générales depuis la base de données."""
        try:
            # Récupérer les statistiques agrégées des campagnes
            campaign_stats = self._get_campaign_statistics()
            
            # Récupérer les campagnes récentes
            recent_campaigns = self._get_recent_campaigns()
            
            # Construire l'objet DashboardStats
            stats = DashboardStats(
                total_campaigns=campaign_stats.get('total_campaigns', 0),
                total_emails_sent=campaign_stats.get('total_sent', 0),
                total_emails_failed=campaign_stats.get('total_failed', 0),
                recent_campaigns=recent_campaigns
            )
            
            stats.calculate_success_rate()
            return stats
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            # Retourner des stats vides en cas d'erreur
            return DashboardStats()
    
    def _get_campaign_statistics(self) -> Dict[str, int]:
        """Récupère les statistiques agrégées depuis la table campaigns."""
        try:
            # Utiliser l'API Supabase pour récupérer toutes les campagnes
            result = self.db.client.table('campaigns').select('sent_count, bounced_count').execute()
            
            if result.data:
                total_campaigns = len(result.data)
                total_sent = sum(row.get('sent_count', 0) or 0 for row in result.data)
                total_failed = sum(row.get('bounced_count', 0) or 0 for row in result.data)
                
                return {
                    'total_campaigns': total_campaigns,
                    'total_sent': total_sent,
                    'total_failed': total_failed
                }
            
            return {'total_campaigns': 0, 'total_sent': 0, 'total_failed': 0}
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la récupération des stats de campagne: {e}")
            return {'total_campaigns': 0, 'total_sent': 0, 'total_failed': 0}
    
    def _get_recent_campaigns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Récupère les campagnes récentes."""
        try:
            result = self.db.client.table('campaigns').select(
                'id, name, status, total_recipients, sent_count, created_at, completed_at'
            ).order('created_at', desc=True).limit(limit).execute()
            
            campaigns = []
            for row in result.data:
                campaigns.append({
                    'id': str(row.get('id', '')),
                    'name': row.get('name', ''),
                    'status': row.get('status', ''),
                    'total_recipients': row.get('total_recipients', 0),
                    'sent_count': row.get('sent_count', 0),
                    'created_at': str(row.get('created_at', '')) if row.get('created_at') else None,
                    'completed_at': str(row.get('completed_at', '')) if row.get('completed_at') else None
                })
            
            return campaigns
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la récupération des campagnes récentes: {e}")
            return []
    
    def update_stats(self, campaign_result: Dict[str, Any]):
        """
        Met à jour les statistiques d'une campagne dans la base de données.
        Cette méthode est appelée après l'exécution d'une campagne.
        """
        try:
            campaign_id = campaign_result.get('campaign_id')
            if not campaign_id:
                app_logger.error("campaign_id manquant dans campaign_result")
                return
            
            # Récupérer les valeurs actuelles
            current = self.db.client.table('campaigns').select('sent_count, bounced_count').eq('id', campaign_id).execute()
            
            if current.data:
                current_sent = current.data[0].get('sent_count', 0) or 0
                current_bounced = current.data[0].get('bounced_count', 0) or 0
                
                # Mettre à jour avec les nouvelles valeurs
                self.db.client.table('campaigns').update({
                    'sent_count': current_sent + campaign_result.get('sent', 0),
                    'bounced_count': current_bounced + campaign_result.get('failed', 0),
                    'updated_at': 'NOW()'
                }).eq('id', campaign_id).execute()
                
                app_logger.info(f"Statistiques mises à jour pour la campagne {campaign_id}")
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la mise à jour des stats: {e}")
