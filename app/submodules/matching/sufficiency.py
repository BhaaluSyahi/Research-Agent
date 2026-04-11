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
    - At least 2 distinct entities (people or orgs) across the matches
    """
    # 1. Check result count
    if len(matches) < settings.rag_sufficiency_min_results:
        return False
        
    # 2. Check top score (matches are assumed to be sorted by cosine_score descending)
    # If not sorted, we should find the max
    top_score = max([m.cosine_score for m in matches]) if matches else 0.0
    
    if top_score < settings.rag_sufficiency_min_score:
        return False
        
    # 3. Check for at least 2 distinct entities across all matches
    # We look at 'people' and 'orgs' in the entities dict
    distinct_entities = set()
    for m in matches:
        if m.entities:
            people = m.entities.get("people", [])
            orgs = m.entities.get("orgs", [])
            for person in people:
                distinct_entities.add(person.lower())
            for org in orgs:
                distinct_entities.add(org.lower())
                
    if len(distinct_entities) < 2:
        return False
        
    return True
