"""
Shared indexing pipeline: fetch → summarize → embed → upsert.
Used by both proactive search agents and the on-demand enricher.
"""

import hashlib
from app.core.logging import get_logger
from app.repositories.supabase_informal import SupabaseInformalRepository, InformalEntryCreate, InformalEntryEntities
from app.mcp.tools.embedding_tools import EmbeddingTools
from app.mcp.guardrails import strip_and_truncate_article

logger = get_logger(__name__)


class ContentIndexer:
    """
    Processes raw article content into an informal_news_entries row.
    """

    def __init__(
        self, 
        informal_repo: SupabaseInformalRepository,
        embedding_tools: EmbeddingTools
    ):
        self.informal_repo = informal_repo
        self.embedding_tools = embedding_tools

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
        # 1. Sanitize
        clean_text = strip_and_truncate_article(raw_text)
        if len(clean_text) < 200:
            return False
            
        # 2. Content Hash DEDUP
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        existing = await self.informal_repo.get_by_content_hash(content_hash)
        if existing:
            # Associate existing entry with new topic if not already done
            await self.informal_repo.add_topic_association(
                entry_id=existing.id,
                topic=topic,
                relevance_score=1.0, # Default high for manual crawl
                added_by=indexed_by
            )
            return False

        # 3. Summarize & Extract (using MCP tool logic)
        extracted = await self.embedding_tools.summarize_and_extract(clean_text, source_url)
        
        # 4. Embed
        embedding = await self.embedding_tools.embed_text(extracted["summary"])
        
        # 5. Build Create model
        entry_create = InformalEntryCreate(
            content_hash=content_hash,
            title=extracted.get("title"),
            summary=extracted["summary"],
            raw_snippet=clean_text[:1000],
            source_url=source_url,
            source_domain=source_url.split("/")[2] if "/" in source_url else None,
            trust_score=0.8, # Default for search-sourced
            entities=InformalEntryEntities(**extracted.get("entities", {})),
            topic_tags=extracted.get("topic_tags", []),
            geo_tags=extracted.get("geo_tags", []),
            embedding=embedding,
            indexed_by=indexed_by
        )
        
        # 6. Upsert
        entry = await self.informal_repo.upsert_entry(entry_create)
        
        # 7. Associate Topic
        await self.informal_repo.add_topic_association(
            entry_id=entry.id,
            topic=topic,
            relevance_score=1.0,
            added_by=indexed_by
        )
        
        return True
