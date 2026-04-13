"""
DB MCP tools: query_formal_organizations, search_informal_knowledge_base, write_recommendation.
"""

import re
from uuid import UUID
from app.core.logging import get_logger
from app.repositories.supabase_formal import SupabaseFormalRepository
from app.repositories.supabase_informal import SupabaseInformalRepository, SearchFilters

logger = get_logger(__name__)


class DBTools:
    def __init__(
        self, 
        formal_repo: SupabaseFormalRepository, 
        informal_repo: SupabaseInformalRepository
    ):
        self.formal_repo = formal_repo
        self.informal_repo = informal_repo

    async def query_formal_organizations(self, keywords: list[str], limit: int = 20) -> list[dict]:
        """
        MCP tool: query registered organizations.
        """
        # Guardrail: clip limits
        limit = min(limit, 20)
        keywords = keywords[:10]
        
        # Clean keywords of SQL-ish characters
        clean_keywords = [re.sub(r"[^a-zA-Z0-9\s]", "", k) for k in keywords]
        
        all_orgs = await self.formal_repo.get_registered_organizations()
        
        # Simple keyword filter (will try to replace it by DB-side full text search in future)
        matches = []
        for org in all_orgs:
            content = f"{org.name} {org.description or ''}".lower()
            if any(k.lower() in content for k in clean_keywords):
                matches.append(org.model_dump(mode="json"))
                if len(matches) >= limit:
                    break
        
        return matches

    async def search_informal_knowledge_base(
        self,
        query_embedding: list[float],
        topic_tags: list[str] | None = None,
        geo_tags: list[str] | None = None,
        min_trust_score: float = 0.3,
        top_k: int = 20,
    ) -> list[dict]:
        """
        MCP tool: semantic search over the informal knowledge base.
        """
        # Guardrails: floor/cap
        min_trust_score = max(min_trust_score, 0.3)
        top_k = min(top_k, 20)
        
        filters = SearchFilters(
            topic_tags=topic_tags or [],
            geo_tags=geo_tags or [],
            min_trust_score=min_trust_score,
            top_k=top_k
        )
        
        entries = await self.informal_repo.search_similar(query_embedding, filters)
        return [e.model_dump(mode="json") for e in entries]

    async def write_recommendation(
        self,
        request_id: str,
        formal_matches: list[dict],
        informal_matches: list[dict],
    ) -> bool:
        """
        MCP tool: write the final recommendation payload to requests.recommendations.
        """
        # Final payload structure
        recommendations = {
            "formal_matches": formal_matches,
            "informal_matches": informal_matches,
            "pipeline_version": "1.0"
        }
        
        await self.formal_repo.update_request_status(
            request_id=UUID(request_id),
            agent_research_status="complete",
            recommendations=recommendations
        )
        return True
