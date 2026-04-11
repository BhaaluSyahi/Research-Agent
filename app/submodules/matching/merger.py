"""
Result merger — deduplicates and merges formal + informal match results.
Assigns final confidence scores and produces the RecommendationPayload.
"""

from app.submodules.matching.schemas import (
    FormalMatch,
    InformalMatch,
    RecommendationPayload,
    RequestRecord,
)


class ResultMerger:
    """
    Merges formal and informal results into the final recommendation payload.
    Deduplication: if the same entity appears in both formal and informal results,
    keep it in formal_matches and remove from informal_matches.
    Final confidence scores incorporate both the formal ranking and informal cosine score.
    """

    def merge(
        self,
        request: RequestRecord,
        formal: list[FormalMatch],
        informal: list[InformalMatch],
        on_demand_triggered: bool = False,
    ) -> RecommendationPayload:
        """Merge, deduplicate, and score the combined result set."""
        # TODO: implement (Phase 8)
        raise NotImplementedError
