"""
Embedding MCP tools: embed_text, summarize_and_extract.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


async def embed_text(text: str) -> list[float]:
    """
    MCP tool: generate a 1536-dimensional embedding via text-embedding-3-small.
    text is truncated at 8000 characters before sending.
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError


async def summarize_and_extract(raw_text: str, source_url: str) -> dict:
    """
    MCP tool: summarize article text and extract entities using GPT-4o.
    Input truncated at 8000 characters.
    Output validated: summary < 500 chars, event_date parseable, topic_tags in known set.
    Returns: {summary, title, entities, topic_tags, geo_tags, event_date}
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError
