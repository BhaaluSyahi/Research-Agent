"""
SupabaseKpiRepository — WRITE access to matching_kpis and crawl_logs tables.
Append-only: rows are inserted, never updated.
"""

from supabase import AsyncClient

from app.repositories.base import BaseRepository


class KpiRecord:
    """Placeholder — full model will be defined in Phase 2."""


class CrawlLogRecord:
    """Placeholder — full model will be defined in Phase 2."""


class SupabaseKpiRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def write_kpi(self, kpi: KpiRecord) -> None:
        """Insert a new row into matching_kpis."""
        # TODO: implement
        raise NotImplementedError

    async def write_crawl_log(self, log: CrawlLogRecord) -> None:
        """Insert a new row into crawl_logs."""
        # TODO: implement
        raise NotImplementedError
