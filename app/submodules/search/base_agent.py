"""
Abstract base class for all topic crawler agents.
Each topic agent (floods, drought, etc.) is a thin subclass of BaseSearchAgent.
"""

from abc import ABC, abstractmethod

from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseSearchAgent(ABC):
    """
    Template for a proactive search agent.
    Lifecycle per run:
      1. Read search_strategy row for this topic
      2. For each search_query:
         a. Acquire SQS intent lock (MessageGroupId = topic#geo#year)
         b. Call Tavily search
         c. For each result: hash → dedup → summarize → embed → upsert (via indexer.py)
         d. Associate entry with topic in entry_topics
      3. Update search_strategy.last_run_at
      4. Write crawl_log
    """

    @property
    @abstractmethod
    def topic(self) -> str:
        """Topic slug matching search_strategy.topic and queue name suffix."""
        ...

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique agent identifier used in logs and crawl_logs.indexed_by."""
        ...

    async def run(self) -> None:
        """Execute one full crawl cycle for this topic."""
        # TODO: implement (Phase 9)
        raise NotImplementedError
