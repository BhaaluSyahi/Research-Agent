"""
TavilyRepository — web search wrapper around the Tavily API.
Rate-limited globally across all agents (see guardrails).
"""

from tavily import AsyncTavilyClient

from app.repositories.base import BaseRepository


class TavilyResult:
    """Placeholder — full model will be defined in Phase 2."""


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
        # TODO: implement
        raise NotImplementedError
