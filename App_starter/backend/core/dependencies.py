from fastapi import Depends, Header, HTTPException, status

from core.config import Settings, get_settings


def get_current_user(
    x_forwarded_user: str | None = Header(default=None, convert_underscores=False),
) -> str:
    if not x_forwarded_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing ForwardAuth user header",
        )
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
