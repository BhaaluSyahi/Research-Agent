"""
Logic to decide if RAG results are "sufficient" to resolve the request.
If not sufficient, the On-Demand Enricher should be triggered.
"""

from app.config import settings
from app.submodules.matching.schemas import InformalMatch


def is_rag_sufficient(matches: list[InformalMatch]) -> bool:
    """
    Sufficiency criteria (from 06_GUARDRAILS.md):
    - At least 3 results
    - Top score > 0.75
    - At least 2 distinct entities (TODO: entity extraction check)
    """
    if len(matches) < settings.rag_sufficiency_min_results:
        return False
        
    # Check top score (assuming matches are sorted by confidence)
    # Note: In the matcher, we put 0.0 as placeholder for cosine_score. 
    # In production, the RPC returns the score.
    # We'll use trust_score or actual similarity score once wired.
    
    # For now, use the threshold from settings
    highest_score = max([m.trust_score for m in matches]) if matches else 0.0
    
    if highest_score < settings.rag_sufficiency_min_score:
        return False
        
    return True
