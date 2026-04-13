"""
Informal matching via RAG (Retrieval Augmented Generation).
Embeds the request and queries pgvector in Supabase.
"""

from typing import Optional
from app.core.logging import get_logger
from app.repositories.supabase_informal import SupabaseInformalRepository, SearchFilters
from app.repositories.openai_client import OpenAIClientRepository
from app.submodules.matching.schemas import InformalMatch, RequestRecord

logger = get_logger(__name__)

class InformalMatcher:
    def __init__(
        self, 
        informal_repo: SupabaseInformalRepository,
        openai_repo: OpenAIClientRepository
    ):
        self.informal_repo = informal_repo
        self.openai_repo = openai_repo

    async def match(
        self, 
        request: RequestRecord, 
        topic_tags: list[str] | None = None,
        geo_tags: list[str] | None = None
    ) -> list[InformalMatch]:
        """
        1. Embed the request description
        2. Query pgvector for similar informal entries
        3. Convert to InformalMatch objects
        """
        logger.info("informal_matching_started", request_id=str(request.id))
        
        # 1. Embed
        embedding = await self.openai_repo.embed(request.description)
        
        # 2. Search
        filters = SearchFilters(
            topic_tags=topic_tags or [],
            geo_tags=geo_tags or [],
            min_trust_score=0.3, # default floor
            top_k=20
        )
        
        results = await self.informal_repo.search_similar(embedding, filters)
        
        # 3. Transform
        matches = []
        for entry in results:
            # Note: relevance_reason is not generated here — it will be generated 
            # by the LLM in the pipeline orchestration phase if this entry is selected.
            # For this layer, we just return the raw matches.
            matches.append(
                InformalMatch(
                    entry_id=entry.id,
                    title=entry.title,
                    summary=entry.summary,
                    source_url=entry.source_url,
                    trust_score=entry.trust_score or 0.0,
                    cosine_score=entry.similarity,
                    relevance_reason="Matched via semantic similarity search.",
                    topic_tags=entry.topic_tags,
                    geo_tags=entry.geo_tags,
                    entities=entry.entities.model_dump() if entry.entities else None
                )
            )
            
        logger.info(
            "informal_matching_complete", 
            request_id=str(request.id), 
            matches_count=len(matches)
        )
        return matches
