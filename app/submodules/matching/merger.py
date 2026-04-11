"""
Merges formal and informal match results, deduplicates, and produces the final RecommendationPayload.
"""

from datetime import datetime
from app.submodules.matching.schemas import (
    FormalMatch,
    InformalMatch,
    RecommendationPayload,
    RequestRecord
)


class ResultMerger:
    """
    Combines formal and informal results.
    Deduplication logic:
    If an informal entry mentions an organization ID that's already in formal matches,
    it can potentially boost the formal match score or add more context.
    (Simple version for now: return both but capped).
    """

    def merge(
        self, 
        request: RequestRecord, 
        formal: list[FormalMatch], 
        informal: list[InformalMatch],
        on_demand_triggered: bool = False
    ) -> RecommendationPayload:
        """
        Produce the final recommendation payload.
        """
        # Deduplication (Simple): 
        # Check if any informal source URL is already mentioned in formal reasons? 
        # (Future scope: LLM-based entity resolution)
        
        return RecommendationPayload(
            request_id=request.id,
            formal_matches=formal[:10],
            informal_matches=informal[:10],
            on_demand_triggered=on_demand_triggered,
            generated_at=datetime.now(),
            pipeline_version="1.0"
        )
