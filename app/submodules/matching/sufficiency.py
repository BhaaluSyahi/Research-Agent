"""
Sufficiency checker — decides whether RAG results meet the threshold to skip on-demand enrichment.

Thresholds (from config.py):
  - rag_sufficiency_min_results: minimum number of results (default 3)
  - rag_sufficiency_min_score: minimum cosine score for qualifying results (default 0.75)
  - At least 2 distinct entities must be represented in qualifying results
"""

from app.submodules.matching.schemas import InformalMatch


def is_sufficient(results: list[InformalMatch], min_results: int, min_score: float) -> bool:
    """
    Return True if informal RAG results meet the sufficiency criteria, False otherwise.
    Criteria:
      - At least min_results results with cosine_score >= min_score
      - At least 2 distinct source entities (by source_url domain)
    """
    # TODO: implement (Phase 6)
    raise NotImplementedError
