from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from supabase import AsyncClient, acreate_client

from app.config import Settings, settings


@lru_cache # Pro level optimization (clown emoji)
def get_settings() -> Settings:
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_supabase_client() -> AsyncClient:
    """Returns a Supabase async client. Gonna use it for dependency injection."""
    client = await acreate_client(settings.supabase_url, settings.supabase_key)
    return client
