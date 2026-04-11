"""
On-demand enricher — fast-path crawler triggered when RAG results are insufficient.
Runs synchronously within the matching pipeline (blocks until fresh data is available).
"""

from app.core.logging import get_logger
from app.submodules.matching.schemas import InformalMatch, RequestRecord

logger = get_logger(__name__)


class OnDemandEnricher:
    """
    Triggered when is_sufficient() returns False.
    Steps:
      1. Build targeted Tavily search queries from the request
      2. Call web_search MCP tool
      3. For each result: call indexer.index()
      4. Re-run RAG search with fresh data
      5. Update matching_kpis: on_demand_triggered=True
    Uses SQS FIFO MessageGroupId for intent deduplication (see intent_lock.py).
    """

    async def enrich_and_search(self, request: RequestRecord) -> list[InformalMatch]:
        """Fetch fresh data for the request and return new informal matches."""
        # TODO: implement (Phase 7)
        raise NotImplementedError
