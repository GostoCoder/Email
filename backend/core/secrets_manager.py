"""
Secrets Validation & Security Configuration Module

Provides:
- Startup validation of critical secrets
- Secure secret handling utilities
- Environment-specific security settings
"""

import os
import sys
import logging
import secrets
from typing import List, Optional
from dataclasses import dataclass

from core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SecretValidationResult:
    """Result of secret validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class SecretValidationError(Exception):
    """Raised when critical secrets are missing or invalid"""
    pass


# Secrets that MUST be set in production
REQUIRED_PRODUCTION_SECRETS = [
    "jwt_secret",
    "supabase_url",
    "supabase_service_role_key",
]

# Secrets that should have strong values
STRONG_SECRET_REQUIREMENTS = {
    "jwt_secret": {
        "min_length": 32,
        "forbidden_values": ["change-me", "secret", "password", "123456"],
    },
    "supabase_service_role_key": {
        "min_length": 100,  # Supabase keys are long
        "forbidden_values": [],
    },
}

# Default/weak values that should be flagged
WEAK_DEFAULT_VALUES = [
    "change-me",
    "changeme",
    "password",
    "secret",
    "123456",
    "admin",
    "test",
    "development",
]


def validate_secret_strength(name: str, value: Optional[str]) -> List[str]:
    """Validate that a secret meets strength requirements"""
    errors = []
    
    if not value:
        return [f"{name}: Not set"]
    
    requirements = STRONG_SECRET_REQUIREMENTS.get(name, {})
    
    # Check minimum length
    min_length = requirements.get("min_length", 8)
    if len(value) < min_length:
        errors.append(f"{name}: Too short (min {min_length} chars)")
    
    # Check for forbidden values
    forbidden = requirements.get("forbidden_values", WEAK_DEFAULT_VALUES)
    if value.lower() in [v.lower() for v in forbidden]:
        errors.append(f"{name}: Using weak/default value")
    
    return errors


def validate_all_secrets(is_production: bool = False) -> SecretValidationResult:
    """
    Validate all secrets and return comprehensive result.
    
    Args:
        is_production: If True, enforce strict validation
    
    Returns:
        SecretValidationResult with validity status and messages
    """
    settings = get_settings()
    errors = []
    warnings = []
    
    # Check required secrets
    for secret_name in REQUIRED_PRODUCTION_SECRETS:
        value = getattr(settings, secret_name, None)
        
        if not value:
            if is_production:
                errors.append(f"Missing required secret: {secret_name}")
            else:
                warnings.append(f"Missing secret (OK in dev): {secret_name}")
    
    # Validate secret strength
    jwt_secret = settings.jwt_secret
    jwt_errors = validate_secret_strength("jwt_secret", jwt_secret)
    
    if is_production:
        errors.extend(jwt_errors)
    else:
        warnings.extend(jwt_errors)
    
    # Check for development defaults in production
    if is_production:
        if settings.app_env in ["development", "dev"]:
            errors.append("APP_ENV is set to development in production!")
        
        if "localhost" in str(settings.app_base_url):
            warnings.append("APP_BASE_URL contains localhost")
    
    # Validate email provider configuration
    email_provider = settings.email_provider
    provider_secrets = {
        "smtp": ["smtp_username", "smtp_password"],
    }
    
    required_for_provider = provider_secrets.get(email_provider, [])
    for secret_name in required_for_provider:
        value = getattr(settings, secret_name, None)
        if not value:
            warnings.append(f"Email provider '{email_provider}' requires {secret_name}")
    
    return SecretValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_secrets_on_startup():
    """
    Validate secrets at application startup.
    Raises exception in production if critical secrets are missing.
    """
    settings = get_settings()
    is_production = settings.app_env.lower() in ["production", "prod"]
    
    result = validate_all_secrets(is_production)
    
    # Log warnings
    for warning in result.warnings:
        logger.warning(f"⚠️  Security warning: {warning}")
    
    # Log errors
    for error in result.errors:
        logger.error(f"❌ Security error: {error}")
    
    # Fail in production if invalid
    if not result.is_valid and is_production:
        logger.critical("❌ Critical secrets validation failed! Cannot start in production mode.")
        raise SecretValidationError(
            f"Critical secrets validation failed: {'; '.join(result.errors)}"
        )
    
    if result.is_valid:
        logger.info("✅ Secrets validation passed")
    else:
        logger.warning("⚠️  Secrets validation passed with warnings (acceptable in development)")


def generate_secure_secret(length: int = 64) -> str:
    """Generate a cryptographically secure random secret"""
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """Generate a secure API key with prefix"""
    return f"ek_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()


def mask_secret(secret: str, show_chars: int = 4) -> str:
    """Mask a secret for safe logging"""
    if not secret or len(secret) <= show_chars * 2:
        return "***"
    return f"{secret[:show_chars]}...{secret[-show_chars:]}"


# Security headers configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none';"
    ),
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def get_security_headers(is_production: bool = True) -> dict:
    """Get security headers based on environment"""
    headers = SECURITY_HEADERS.copy()
    
    if not is_production:
        # Relax some headers for development
        headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "img-src 'self' data: https: http:; "
            "connect-src 'self' http: https: ws: wss:;"
        )
        # Remove HSTS in development
        del headers["Strict-Transport-Security"]
    
    return headers


class SecurityHeadersMiddleware:
    """Middleware to add security headers to responses"""
    
    def __init__(self, app, is_production: bool = True):
        self.app = app
        self.headers = get_security_headers(is_production)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for name, value in self.headers.items():
                    headers.append((name.lower().encode(), value.encode()))
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_with_headers)
