"""
Formal matching logic — queries Supabase for registered organizations and volunteers.
Scores and ranks results based on keywords, verification status, and geography.
"""

import math
import re
from datetime import datetime
from typing import Any, List

from app.core.logging import get_logger
from app.repositories.supabase_formal import SupabaseFormalRepository
from app.submodules.matching.schemas import (
    FormalMatch,
    FormalMatchResult,
    OrganizationRecord,
    RequestRecord,
    VolunteerProfileRecord,
)

logger = get_logger(__name__)


class FormalMatcher:
    """
    Implements the formal matching layer.
    Scores entities (orgs/volunteers) based on:
    1. Keyword overlap
    2. Proximity (if available)
    3. Trust/Verification (for organizations)
    """

    def __init__(self, formal_repo: SupabaseFormalRepository):
        self.formal_repo = formal_repo

    async def match(self, request: RequestRecord) -> FormalMatchResult:
        """
        Execute the formal matching pipeline for a given request.
        """
        logger.info("formal_matching_started", request_id=str(request.id))
        
        # 1. Fetch available entities
        try:
            orgs = await self.formal_repo.get_registered_organizations()
            volunteers = await self.formal_repo.get_active_volunteers()
        except Exception as e:
            logger.error("entity_fetch_failed", error=str(e), request_id=str(request.id))
            raise

        matches: List[FormalMatch] = []
        
        # 2. Score Organizations
        for org in orgs:
            score = self._score_organization(request, org)
            if score > 0.1:
                matches.append(
                    FormalMatch(
                        entity_type="organization",
                        entity_id=org.id,
                        name=org.name,
                        confidence=round(score, 3),
                        reason=self._get_match_reason(request, org),
                        verified=org.verified
                    )
                )

        # 3. Score Volunteers
        for vol in volunteers:
            score = self._score_volunteer(request, vol)
            if score > 0.1:
                matches.append(
                    FormalMatch(
                        entity_type="volunteer",
                        entity_id=vol.id,
                        name=vol.name,
                        confidence=round(score, 3),
                        reason=self._get_match_reason(request, vol),
                        verified=False
                    )
                )

        # 4. Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)
        
        # Cap at top 10
        top_matches = matches[:10]
        
        logger.info(
            "formal_matching_complete", 
            request_id=str(request.id), 
            matches_count=len(top_matches)
        )
        
        return FormalMatchResult(
            request_id=request.id,
            matches=top_matches,
            scored_at=datetime.now()
        )

    def _score_organization(self, request: RequestRecord, org: OrganizationRecord) -> float:
        """
        Compute match score for an organization (0.0 - 1.0).
        Weighting:
          - Keyword Overlap: 50%
          - Verification: 50%
        (Note: Organizations lack coordinates in current schema)
        """
        score = 0.0
        
        # Keyword overlap (50%)
        # Combine title and description for request, name and description for org
        req_text = f"{request.title} {request.description}"
        org_text = f"{org.name} {org.description or ''}"
        keyword_score = self._compute_keyword_overlap(req_text, org_text)
        score += keyword_score * 0.5
        
        # Verification (50%)
        if org.verified:
            score += 0.5
            
        return min(score, 1.0)

    def _score_volunteer(self, request: RequestRecord, vol: VolunteerProfileRecord) -> float:
        """
        Compute match score for a volunteer (0.0 - 1.0).
        Weighting:
          - Keyword Overlap: 40%
          - Proximity: 60%
        """
        score = 0.0
        
        # Keyword overlap (40%)
        req_text = f"{request.title} {request.description}"
        vol_text = f"{vol.name} {vol.specialty or ''} {vol.bio or ''}"
        keyword_score = self._compute_keyword_overlap(req_text, vol_text)
        score += keyword_score * 0.4
        
        # Proximity (60%)
        geo_score = self._compute_geo_score(request, vol)
        score += geo_score * 0.6
        
        return min(score, 1.0)

    def _compute_keyword_overlap(self, text1: str, text2: str) -> float:
        """Jaccard-like similarity on word tokens."""
        def get_tokens(t): 
            return set(re.findall(r"\w+", t.lower()))
            
        s1, s2 = get_tokens(text1), get_tokens(text2)
        if not s1 or not s2: 
            return 0.0
            
        intersection = s1.intersection(s2)
        # Normalize by the smaller set or a fixed representative length to avoid over-rewarding brevity
        # Using a capped length for request ensures we don't need a huge intersection for long descriptions
        return len(intersection) / min(len(s1), 15)

    def _compute_geo_score(self, request: RequestRecord, entity: Any) -> float:
        """Score based on Haversine distance (1.0 = near, 0.0 = far)."""
        if not request.latitude or not request.longitude:
            return 0.5 # Neutral if no request location
            
        if not hasattr(entity, "latitude") or not getattr(entity, "latitude"):
            return 0.5 # Neutral if no entity location
            
        try:
            r_lat, r_lng = float(request.latitude), float(request.longitude)
            e_lat, e_lng = float(entity.latitude), float(entity.longitude)
            
            dist_km = self._haversine(r_lat, r_lng, e_lat, e_lng)
            
            # Decay score based on distance
            # 1.0 at 0km, ~0.5 at 50km, ~0.0 at 500km
            if dist_km < 1: 
                return 1.0
            score = 1.0 - (math.log10(dist_km + 1) / 2.7) # log10(500) is approx 2.7
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.5

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute distance in km between two points."""
        R = 6371 # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _get_match_reason(self, request: RequestRecord, entity: Any) -> str:
        """Generate a brief explanation for the match."""
        if isinstance(entity, OrganizationRecord):
            reason_parts = [f"Registered {entity.type}"]
            if entity.verified:
                reason_parts.append("verified for trust")
            return " — ".join(reason_parts) + "."
        
        return "Volunteer profile matched by specialty and locality."
