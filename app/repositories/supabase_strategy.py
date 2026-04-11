"""
SupabaseStrategyRepository — READ access to search_strategy table.
Written by the future Strategy Module; this service only reads and updates last_run_at.
"""

from supabase import AsyncClient

from app.repositories.base import BaseRepository


class SearchStrategy:
    """Placeholder — full model will be defined in Phase 2."""


class SupabaseStrategyRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def get_strategy_for_topic(self, topic: str) -> SearchStrategy | None:
        """Return the search strategy row for the given topic slug, or None."""
        # TODO: implement
        raise NotImplementedError

    async def get_all_active_strategies(self) -> list[SearchStrategy]:
        """Return all active strategy rows (is_active=True)."""
        # TODO: implement
        raise NotImplementedError

    async def update_last_run(
        self,
        topic: str,
        articles_found: int,
        new_entries: int,
    ) -> None:
        """Update last_run_at, last_run_articles_found, last_run_new_entries for a topic."""
        # TODO: implement
        raise NotImplementedError
