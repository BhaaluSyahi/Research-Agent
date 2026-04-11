"""
SupabaseKpiRepository — WRITE access to matching_kpis and crawl_logs tables.
Append-only: rows are inserted, never updated.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from supabase import AsyncClient

from app.core.exceptions import RepositoryError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class KpiRecord(BaseModel):
    """Pydantic model for inserting a row into matching_kpis."""
    request_id: UUID
    pipeline_started_at: datetime
    pipeline_completed_at: Optional[datetime] = None
    formal_matches_count: int = 0
    informal_matches_count: int = 0
    on_demand_triggered: bool = False
    on_demand_articles_added: int = 0
    rag_top_score: Optional[float] = None
    rag_results_count: int = 0
    sufficiency_met: Optional[bool] = None
    total_latency_ms: Optional[int] = None
    topics_classified: list[str] = []
    geo_extracted: list[str] = []
    error_occurred: bool = False
    error_message: Optional[str] = None


class CrawlLogRecord(BaseModel):
    """Pydantic model for inserting a row into crawl_logs."""
    agent_name: str
    run_type: str                        # 'scheduled' | 'on_demand'
    topic: str
    search_query: Optional[str] = None
    tavily_results_count: Optional[int] = None
    new_entries_count: Optional[int] = None
    skipped_count: Optional[int] = None
    failed_count: Optional[int] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class SupabaseKpiRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def write_kpi(self, kpi: KpiRecord) -> None:
        """Insert a new row into matching_kpis."""
        payload = kpi.model_dump(mode="json")
        # Convert UUID to string for Supabase
        payload["request_id"] = str(kpi.request_id)

        try:
            await self.client.table("matching_kpis").insert(payload).execute()
            logger.info(
                "kpi_written",
                module="repositories",
                operation="write_kpi",
                request_id=str(kpi.request_id),
                on_demand_triggered=kpi.on_demand_triggered,
                error_occurred=kpi.error_occurred,
            )
        except Exception as exc:
            logger.error(
                "write_kpi_failed",
                module="repositories",
                operation="write_kpi",
                request_id=str(kpi.request_id),
                error=str(exc),
            )
            raise RepositoryError(f"Failed to write KPI for request {kpi.request_id}: {exc}") from exc

    async def write_crawl_log(self, log: CrawlLogRecord) -> None:
        """Insert a new row into crawl_logs."""
        payload = log.model_dump(mode="json")

        try:
            await self.client.table("crawl_logs").insert(payload).execute()
            logger.info(
                "crawl_log_written",
                module="repositories",
                operation="write_crawl_log",
                agent_name=log.agent_name,
                topic=log.topic,
                run_type=log.run_type,
            )
        except Exception as exc:
            logger.error(
                "write_crawl_log_failed",
                module="repositories",
                operation="write_crawl_log",
                agent_name=log.agent_name,
                error=str(exc),
            )
            raise RepositoryError(f"Failed to write crawl log for agent {log.agent_name}: {exc}") from exc
