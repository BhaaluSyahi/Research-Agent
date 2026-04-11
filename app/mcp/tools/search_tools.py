"""
Search MCP tools: web_search, classify_request.
Tavily rate limits are enforced here before calling the repository.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


async def web_search(
    query: str,
    max_results: int = 5,
    include_domains: list[str] | None = None,
) -> list[dict]:
    """
    MCP tool: execute a Tavily web search.
    - query must be 3–200 characters
    - query must not contain injection patterns
    - blocked domains filtered from results
    - hard rate limit: 10 calls/minute across all agents (shared counter)
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError


async def classify_request(title: str, description: str) -> dict:
    """
    MCP tool: classify a help request into topic tags and extract geographic entities.
    Calls GPT-4o via the classify_request system prompt.
    Input is wrapped in <user_request> delimiters before sending to the LLM.
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError
