from fastapi import Depends, Header, HTTPException, status

from core.config import Settings, get_settings


def get_current_user(
    x_forwarded_user: str | None = Header(default=None, convert_underscores=False),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Get current user from ForwardAuth header.
    In development mode, returns a default user.
    In production, raises 401 if missing.
    """
    # In development mode, allow unauthenticated access
    if settings.app_env == "development":
        return x_forwarded_user or "dev-user"
    
    if not x_forwarded_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing ForwardAuth user header",
        )
    return x_forwarded_user


def get_optional_user(
    x_forwarded_user: str | None = Header(default=None, convert_underscores=False),
) -> str | None:
    """
    Get current user optionally - for endpoints that work with or without auth.
    """
    return x_forwarded_user


def get_app_id(
    x_app_id: str | None = Header(default=None, convert_underscores=False),
) -> str | None:
    return x_app_id


def get_app_name(
    x_app_name: str | None = Header(default=None, convert_underscores=False),
) -> str | None:
    return x_app_name


def get_settings_dep(settings: Settings = Depends(get_settings)) -> Settings:
    return settings
