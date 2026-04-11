"""
Shared indexing pipeline: fetch → summarize → embed → upsert.
Used by both proactive search agents and the on-demand enricher.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentIndexer:
    """
    Processes raw article content into an informal_news_entries row.
    Steps:
      1. Strip HTML, truncate to 8000 chars, check for injection patterns
      2. SHA256 → content_hash → dedup check
      3. GPT-4o summarize + entity extract (via MCP summarize_and_extract tool)
      4. text-embedding-3-small embed (via MCP embed_text tool)
      5. Upsert to informal_news_entries with optimistic lock
    """

    async def index(
        self,
        raw_text: str,
        source_url: str,
        topic: str,
        indexed_by: str,
    ) -> bool:
        """
        Process and index one article.
        Returns True if a new entry was created, False if it was a duplicate.
        """
        # TODO: implement (Phase 9)
        raise NotImplementedError
