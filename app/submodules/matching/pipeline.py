"""
Matching pipeline orchestrator.
Sequence: formal → informal (RAG) → on-demand enrichment (if needed) → merge → write.
"""

from app.submodules.matching.schemas import RequestRecord, RecommendationPayload


class MatchingPipeline:
    """
    Orchestrates the full matching pipeline for a single help request.
    Injected with repository instances and the MCP tool interface.
    """

    async def run(self, request: RequestRecord) -> RecommendationPayload:
        """
        Execute the full pipeline and return the final recommendation payload.
        Writes results to requests.recommendations via the write_recommendation MCP tool.
        Updates matching_kpis after completion.
        """
        # TODO: implement (Phase 8)
        raise NotImplementedError
