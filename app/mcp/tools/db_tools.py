"""
DB MCP tools: query_formal_organizations, search_informal_knowledge_base, write_recommendation.
All inputs are validated by guardrails before the underlying repository is called.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


async def query_formal_organizations(keywords: list[str], limit: int = 20) -> list[dict]:
    """
    MCP tool: query registered organizations from the formal DB.
    - limit silently capped at 20
    - keywords list capped at 10 items
    - Each keyword stripped of SQL special characters
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError


async def search_informal_knowledge_base(
    query_text: str,
    topic_tags: list[str] | None = None,
    geo_tags: list[str] | None = None,
    min_trust_score: float = 0.3,
    top_k: int = 20,
) -> list[dict]:
    """
    MCP tool: semantic search over the informal knowledge base.
    - min_trust_score floored at 0.3
    - top_k silently capped at 20
    - query_text truncated at 500 characters
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError


async def write_recommendation(
    request_id: str,
    formal_matches: list[dict],
    informal_matches: list[dict],
) -> bool:
    """
    MCP tool: write the final recommendation payload to requests.recommendations.
    Most sensitive tool — all guardrails run before execution.
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError
