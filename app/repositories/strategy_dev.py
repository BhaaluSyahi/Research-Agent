"""
DevStrategyRepository — Mock strategy repository for dev-mode.
Provides hardcoded strategies instead of querying Supabase.
"""

from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger
from app.repositories.supabase_strategy import SupabaseStrategyRepository, SearchStrategy, SearchStrategyQuery

logger = get_logger(__name__)

MOCK_STRATEGIES = [
    SearchStrategy(
        id="mock-strat-001",
        topic="drought",
        display_name="Drought Resilience",
        search_queries=[
            SearchStrategyQuery(query="drought relief NGO India", weight=1.0),
            SearchStrategyQuery(query="water scarcity solutions rural India", weight=0.8)
        ],
        geo_focus=["Andhra Pradesh", "Rajasthan"],
        crawl_frequency_hours=12,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ),
    SearchStrategy(
        id="mock-strat-002",
        topic="healthcare",
        display_name="Rural Healthcare Search",
        search_queries=[
            SearchStrategyQuery(query="rural health camps Bihar", weight=1.0),
            SearchStrategyQuery(query="mobile medical units India", weight=0.7)
        ],
        geo_focus=["Bihar", "Uttar Pradesh"],
        crawl_frequency_hours=24,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
]

class DevStrategyRepository(SupabaseStrategyRepository):
    def __init__(self, *args, **kwargs) -> None:
        # No real client needed
        logger.info("dev_strategy_repository_initialized", topics=[s.topic for s in MOCK_STRATEGIES])

    async def get_strategy_for_topic(self, topic: str) -> SearchStrategy | None:
        """Return a mock strategy if topic matches."""
        for s in MOCK_STRATEGIES:
            if s.topic == topic:
                return s
        return None

    async def get_all_active_strategies(self) -> list[SearchStrategy]:
        """Return hardcoded mock strategies."""
        logger.info("dev_mode_providing_mock_strategies", count=len(MOCK_STRATEGIES))
        return list(MOCK_STRATEGIES)

    async def update_last_run(self, topic: str, articles_found: int, new_entries: int) -> None:
        """No-op for simulation."""
        logger.info("dev_strategy_update_skipped", topic=topic, found=articles_found, new=new_entries)
