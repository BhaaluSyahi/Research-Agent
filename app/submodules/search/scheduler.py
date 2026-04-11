"""
APScheduler setup for the proactive search fleet.
Reads crawl_frequency_hours from search_strategy table at startup and schedules each agent.
Intervals can be reconfigured without restarting by re-reading the strategy table.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


class CrawlerScheduler:
    """
    Manages APScheduler jobs for all topic agents.
    Each job interval is sourced from search_strategy.crawl_frequency_hours — not hardcoded.
    """

    async def start(self) -> None:
        """Configure scheduler jobs from strategy table and start the scheduler."""
        # TODO: implement (Phase 9)
        raise NotImplementedError

    async def stop(self) -> None:
        """Shut down the scheduler gracefully."""
        # TODO: implement (Phase 9)
        raise NotImplementedError
