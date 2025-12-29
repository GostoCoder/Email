from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="app-starter")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    allowed_origins: List[AnyHttpUrl] = Field(default_factory=list)
    log_level: str = Field(default="INFO")

    supabase_url: AnyHttpUrl | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    jwt_secret: str = Field(default="change-me", min_length=8)
    redis_url: str | None = None

    # Email service configuration (SMTP only)
    email_provider: str = Field(default="smtp")
    
    # SMTP Configuration (for Gmail ou autre serveur SMTP)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = Field(default=True)
    
    # Email sending limits
    email_batch_size: int = Field(default=100)
    email_rate_limit_per_second: int = Field(default=10)
    email_max_retry_attempts: int = Field(default=3)
    
    # Application URLs
    app_base_url: str = Field(default="http://localhost:3000")
    api_base_url: str = Field(default="http://localhost:8000")
    
    # Celery configuration
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
