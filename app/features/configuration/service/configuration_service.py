"""
Service de gestion de la configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from app.features.configuration.model.configuration_model import AppConfiguration
from app.core.utils.logger import app_logger


class ConfigurationService:
    """Service pour gérer la configuration."""
    
    def __init__(self):
        self.env_file = Path.cwd() / '.env'
        load_dotenv(self.env_file)
    
    def get_configuration(self) -> AppConfiguration:
        """Récupère la configuration actuelle."""
        return AppConfiguration(
            smtp_host=os.getenv('SMTP_HOST', ''),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_user=os.getenv('SMTP_USER', ''),
            smtp_password=os.getenv('SMTP_PASSWORD', ''),
            smtp_use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            sender_name=os.getenv('SENDER_NAME', ''),
            sender_email=os.getenv('SENDER_EMAIL', ''),
            unsubscribe_base_url=os.getenv('UNSUBSCRIBE_BASE_URL', 'http://localhost:5000'),
            rate_limit=os.getenv('RATE_LIMIT', '20'),
            max_retries=os.getenv('MAX_RETRIES', '3'),
            num_workers=os.getenv('NUM_WORKERS', '4'),
            debug_mode=os.getenv('DEBUG_MODE', 'false'),
            test_email=os.getenv('TEST_EMAIL', '')
        )
    
    def update_configuration(self, config: AppConfiguration) -> bool:
        """Met à jour la configuration."""
        try:
            # S'assurer que le fichier .env existe
            if not self.env_file.exists():
                self.env_file.touch()
            
            # Mettre à jour les valeurs
            set_key(self.env_file, 'SMTP_HOST', config.smtp_host)
            set_key(self.env_file, 'SMTP_PORT', str(config.smtp_port))
            set_key(self.env_file, 'SMTP_USER', config.smtp_user)
            if config.smtp_password:  # Ne pas écraser si vide
                set_key(self.env_file, 'SMTP_PASSWORD', config.smtp_password)
            set_key(self.env_file, 'SMTP_USE_TLS', 'true' if config.smtp_use_tls else 'false')
            set_key(self.env_file, 'SENDER_NAME', config.sender_name)
            set_key(self.env_file, 'SENDER_EMAIL', config.sender_email)
            set_key(self.env_file, 'UNSUBSCRIBE_BASE_URL', config.unsubscribe_base_url)
            set_key(self.env_file, 'RATE_LIMIT', config.rate_limit)
            set_key(self.env_file, 'MAX_RETRIES', config.max_retries)
            set_key(self.env_file, 'NUM_WORKERS', config.num_workers)
            set_key(self.env_file, 'DEBUG_MODE', config.debug_mode)
            set_key(self.env_file, 'TEST_EMAIL', config.test_email)
            
            # Recharger les variables d'environnement
            load_dotenv(self.env_file, override=True)
            
            app_logger.info("Configuration mise à jour")
            return True
            
        except Exception as e:
            app_logger.error(f"Erreur mise à jour configuration: {e}")
            return False
    
    def test_smtp_connection(self, config: AppConfiguration) -> bool:
        """Teste la connexion SMTP."""
        import smtplib
        
        try:
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as server:
                if config.smtp_use_tls:
                    server.starttls()
                server.login(config.smtp_user, config.smtp_password)
            return True
        except Exception as e:
            app_logger.error(f"Erreur test SMTP: {e}")
            return False
