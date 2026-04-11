"""
Informal matcher — RAG layer using pgvector semantic similarity.
Embeds the request, applies metadata pre-filters, runs similarity search, reranks.
"""

from app.submodules.matching.schemas import InformalMatch, RequestRecord


class InformalMatcher:
    """
    RAG-based informal knowledge retrieval.
    Steps:
      1. Classify request into topic tags + extract geography (LLM via MCP tool)
      2. Embed request description (text-embedding-3-small)
      3. pgvector similarity search with topic + geo pre-filter
      4. Rerank top-K results (cross-encoder or Cohere reranker)
    """

    async def match(self, request: RequestRecord) -> list[InformalMatch]:
        """Return ranked informal matches from the knowledge base."""
        # TODO: implement (Phase 6)
        raise NotImplementedError
