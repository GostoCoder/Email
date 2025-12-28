from __future__ import annotations

from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from core.config import get_settings


class SupabaseNotConfigured(RuntimeError):
    """Raised when Supabase env vars are missing."""


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SupabaseNotConfigured("Supabase URL or service role key missing")
    return create_client(str(settings.supabase_url), settings.supabase_service_role_key)


def fetch_table(table: str, columns: str = "*") -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = client.table(table).select(columns).execute()
    return response.data or []
