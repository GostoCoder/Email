from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends

from core.dependencies import get_current_user
from core.supabase import SupabaseNotConfigured, fetch_table
from .models import AppModel, SAMPLE_APPS
from .schemas import AppSchema

router = APIRouter()


@router.get("", response_model=list[AppSchema])
async def list_apps(_: str = Depends(get_current_user)):
    try:
        rows = fetch_table(
            "apps",
            columns=
            "id,name,url,description,icon,category,is_active,created_at,updated_at",
        )
        apps: list[AppModel] = []
        for row in rows:
            apps.append(
                AppModel(
                    id=str(row.get("id")),
                    name=row.get("name", "Unnamed app"),
                    url=str(row.get("url")),
                    description=row.get("description", ""),
                    icon=row.get("icon", "🧩"),
                    category=row.get("category", "misc"),
                    is_active=bool(row.get("is_active", True)),
                    created_at=_to_datetime(row.get("created_at")),
                    updated_at=_to_datetime(row.get("updated_at")),
                )
            )
        if apps:
            return apps
    except SupabaseNotConfigured:
        pass
    except Exception:
        # fallback to sample data on any Supabase error
        pass

    return SAMPLE_APPS


def _to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now()
    return datetime.now()
