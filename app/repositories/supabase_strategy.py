"""
SupabaseStrategyRepository — READ access to search_strategy table.
Written by the future Strategy Module; this service only reads and updates last_run_at.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from supabase import AsyncClient

from app.core.exceptions import RepositoryError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class SearchStrategyQuery(BaseModel):
    """A single search query entry within a strategy's search_queries list."""
    query: str
    weight: float = 1.0


class SearchStrategy(BaseModel):
    """Pydantic model for the search_strategy table."""
    id: str
    topic: str
    display_name: Optional[str] = None
    search_queries: list[SearchStrategyQuery]
    geo_focus: list[str] = []
    crawl_frequency_hours: int = 6
    priority: int = 5
    is_active: bool = True
    last_run_at: Optional[datetime] = None
    last_run_articles_found: Optional[int] = None
    last_run_new_entries: Optional[int] = None
    updated_by: str = "system"
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SupabaseStrategyRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def get_strategy_for_topic(self, topic: str) -> SearchStrategy | None:
        """Return the search strategy row for the given topic slug, or None."""
        try:
            response = (
                await self.client.table("search_strategy")
                .select("*")
                .eq("topic", topic)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )
            if response.data is None:
                return None
            return SearchStrategy.model_validate(response.data)
        except Exception as exc:
            logger.error(
                "get_strategy_for_topic_failed",
                module="repositories",
                operation="get_strategy_for_topic",
                topic=topic,
                error=str(exc),
            )
            raise RepositoryError(f"Failed to fetch strategy for topic '{topic}': {exc}") from exc

    async def get_all_active_strategies(self) -> list[SearchStrategy]:
        """Return all active strategy rows (is_active=True)."""
        try:
            response = (
                await self.client.table("search_strategy")
                .select("*")
                .eq("is_active", True)
                .execute()
            )
            return [SearchStrategy.model_validate(row) for row in response.data]
        except Exception as exc:
            logger.error(
                "get_all_active_strategies_failed",
                module="repositories",
                operation="get_all_active_strategies",
                error=str(exc),
            )
            raise RepositoryError(f"Failed to fetch active strategies: {exc}") from exc

    async def update_last_run(
        self,
        topic: str,
        articles_found: int,
        new_entries: int,
    ) -> None:
        """Update last_run_at, last_run_articles_found, last_run_new_entries for a topic."""
        payload = {
            "last_run_at": datetime.now(tz=timezone.utc).isoformat(),
            "last_run_articles_found": articles_found,
            "last_run_new_entries": new_entries,
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        try:
            await (
                self.client.table("search_strategy")
                .update(payload)
                .eq("topic", topic)
                .execute()
            )
            logger.info(
                "strategy_last_run_updated",
                module="repositories",
                operation="update_last_run",
                topic=topic,
                articles_found=articles_found,
                new_entries=new_entries,
            )
        except Exception as exc:
            logger.error(
                "update_last_run_failed",
                module="repositories",
                operation="update_last_run",
                topic=topic,
                error=str(exc),
            )
            raise RepositoryError(f"Failed to update last_run for topic '{topic}': {exc}") from exc
