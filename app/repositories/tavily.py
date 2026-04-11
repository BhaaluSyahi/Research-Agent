"""
TavilyRepository — web search wrapper around the Tavily API.
Rate-limited globally across all agents (see guardrails).
"""

from typing import Optional

from pydantic import BaseModel
from tavily import AsyncTavilyClient

from app.core.exceptions import TavilyError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class TavilyResult(BaseModel):
    """A single result returned by the Tavily search API."""
    url: str
    title: Optional[str] = None
    content: str                # Cleaned article snippet
    score: float = 0.0          # Tavily relevance score (0–1)
    raw_content: Optional[str] = None  # Full raw content if requested


class TavilyRepository(BaseRepository):
    def __init__(self, client: AsyncTavilyClient) -> None:
        self.client = client

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> list[TavilyResult]:
        """
        Execute a Tavily web search and return typed results.
        Caller is responsible for rate-limit accounting before calling.
        """
        kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "include_raw_content": False,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains
        if exclude_domains:
            kwargs["exclude_domains"] = exclude_domains

        try:
            response = await self.client.search(**kwargs)
            results = response.get("results", [])
            typed_results = [
                TavilyResult(
                    url=r.get("url", ""),
                    title=r.get("title"),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                    raw_content=r.get("raw_content"),
                )
                for r in results
            ]
            logger.info(
                "tavily_search_complete",
                module="repositories",
                operation="search",
                query=query[:100],
                results_count=len(typed_results),
            )
            return typed_results
        except Exception as exc:
            logger.error(
                "tavily_search_failed",
                module="repositories",
                operation="search",
                query=query[:100],
                error=str(exc),
            )
            raise TavilyError(f"Tavily search failed for query '{query[:80]}': {exc}") from exc
