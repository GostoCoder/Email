"""
Configuration principale de l'application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional


@dataclass
class SMTPConfig:
    """Configuration SMTP (optimisée pour Proton Mail)."""
    host: str
    port: int
    user: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    sender_name: Optional[str] = None
    reply_to: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        """Charge la configuration SMTP depuis les variables d'environnement."""
        load_dotenv()
        return cls(
            host=os.getenv('SMTP_HOST', 'smtp.protonmail.ch'),
            port=int(os.getenv('SMTP_PORT', '587')),
            user=os.getenv('SMTP_USER', ''),
            password=os.getenv('SMTP_PASSWORD', ''),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            use_ssl=os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
            sender_name=os.getenv('SMTP_SENDER_NAME', None),
            reply_to=os.getenv('SMTP_REPLY_TO', None)
        )


@dataclass
class SupabaseConfig:
    """Configuration Supabase."""
    url: str
    key: str
    
    @classmethod
    def from_env(cls):
        """Charge la configuration Supabase depuis les variables d'environnement."""
        load_dotenv()
        return cls(
            url=os.getenv('SUPABASE_URL', 'http://localhost:54321'),
            key=os.getenv('SUPABASE_KEY', '')
        )


@dataclass
class AppConfig:
    """Configuration globale de l'application."""
    smtp: SMTPConfig
    supabase: SupabaseConfig
    data_dir: Path
    templates_dir: Path
    upload_dir: Path
    max_file_size: int = 16 * 1024 * 1024  # 16MB
    
    @classmethod
    def from_env(cls):
        """Charge la configuration depuis les variables d'environnement."""
        load_dotenv()
        root_dir = Path(__file__).parent.parent.parent
        
        return cls(
            smtp=SMTPConfig.from_env(),
            supabase=SupabaseConfig.from_env(),
            data_dir=root_dir / 'data',
            templates_dir=root_dir / 'templates',
            upload_dir=root_dir / 'data' / 'uploads',
            max_file_size=int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))
        )
    
    def ensure_directories(self):
        """Crée les répertoires nécessaires."""
        self.data_dir.mkdir(exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


# Instance globale de configuration
config = AppConfig.from_env()
config.ensure_directories()
