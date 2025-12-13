"""
ViewModel pour la configuration.
"""

from typing import Dict, Any
from app.features.configuration.service.configuration_service import ConfigurationService
from app.features.configuration.model.configuration_model import AppConfiguration


class ConfigurationViewModel:
    """ViewModel pour gérer la présentation de la configuration."""
    
    def __init__(self):
        self.service = ConfigurationService()
    
    def get_configuration_data(self) -> Dict[str, Any]:
        """Récupère les données de configuration."""
        config = self.service.get_configuration()
        
        return {
            'success': True,
            'smtp_host': config.smtp_host,
            'smtp_port': str(config.smtp_port),
            'smtp_user': config.smtp_user,
            'smtp_pass': '',  # Ne pas renvoyer le mot de passe pour des raisons de sécurité
            'sender_name': config.sender_name,
            'sender_email': config.sender_email,
            'rate_limit': config.rate_limit,
            'max_retries': config.max_retries,
            'num_workers': config.num_workers,
            'debug_mode': config.debug_mode,
            'test_email': config.test_email,
            'unsubscribe_base_url': config.unsubscribe_base_url
        }
    
    def update_configuration_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Commande pour mettre à jour la configuration."""
        # Gérer smtp_pass ou smtp_password
        smtp_password = data.get('smtp_password') or data.get('smtp_pass', '')
        
        config = AppConfiguration(
            smtp_host=data.get('smtp_host', ''),
            smtp_port=int(data.get('smtp_port', 587)),
            smtp_user=data.get('smtp_user', ''),
            smtp_password=smtp_password,
            smtp_use_tls=data.get('smtp_use_tls', True),
            sender_name=data.get('sender_name', ''),
            sender_email=data.get('sender_email', ''),
            unsubscribe_base_url=data.get('unsubscribe_base_url', 'http://localhost:5000'),
            rate_limit=data.get('rate_limit', '20'),
            max_retries=data.get('max_retries', '3'),
            num_workers=data.get('num_workers', '4'),
            debug_mode=data.get('debug_mode', 'false'),
            test_email=data.get('test_email', '')
        )
        
        success = self.service.update_configuration(config)
        
        return {
            'success': success,
            'message': 'Configuration mise à jour' if success else 'Erreur mise à jour'
        }
    
    def test_smtp_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Commande pour tester la connexion SMTP."""
        # Gérer smtp_pass ou smtp_password
        smtp_password = data.get('smtp_password') or data.get('smtp_pass', '')
        
        config = AppConfiguration(
            smtp_host=data.get('smtp_host', ''),
            smtp_port=int(data.get('smtp_port', 587)),
            smtp_user=data.get('smtp_user', ''),
            smtp_password=smtp_password,
            smtp_use_tls=data.get('smtp_use_tls', True)
        )
        
        success = self.service.test_smtp_connection(config)
        
        return {
            'success': success,
            'message': 'Connexion SMTP réussie' if success else 'Échec connexion SMTP'
        }
