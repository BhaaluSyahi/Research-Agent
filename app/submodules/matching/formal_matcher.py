"""
Formal matching logic — queries Supabase for registered organizations and volunteers.
Scores and ranks results based on keywords, verification status, and geography.
"""

import math
from datetime import datetime
from typing import Optional

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
    1. Keyword overlap (30%)
    2. Proximity (40% if geo available)
    3. Trust/Verification (30% for orgs)
    """

    def __init__(self, formal_repo: SupabaseFormalRepository):
        self.formal_repo = formal_repo

    async def match(self, request: RequestRecord) -> FormalMatchResult:
        """
        Execute the formal matching pipeline for a given request.
        """
        logger.info("formal_matching_started", request_id=str(request.id))
        
        # 1. Fetch available entities
        orgs = await self.formal_repo.get_registered_organizations()
        volunteers = await self.formal_repo.get_active_volunteers()
        
        matches = []
        
        # 2. Score Organizations
        for org in orgs:
            score = self._score_organization(request, org)
            if score > 0.1:
                matches.append(
                    FormalMatch(
                        entity_type="organization",
                        entity_id=org.id,
                        name=org.name,
                        confidence=score,
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
                        confidence=score,
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
        """Compute match score for an organization (0.0 - 1.0)."""
        score = 0.0
        
        # Keyword overlap (30%)
        keyword_score = self._compute_keyword_overlap(
            request.title + " " + request.description,
            org.name + " " + (org.description or "")
        )
        score += keyword_score * 0.3
        
        # Trust (30%): Verified orgs get a boost
        if org.verified:
            score += 0.3
            
        # Proximity (40%)
        geo_score = self._compute_geo_score(request, org.id) # We don't have org lat/lng in schema, so 0 for now
        # Wait, organization schema doesn't have lat/lng?
        # Checked 03_SCHEMA: organizations table has no lat/lng. 
        # Only volunteer_profiles and requests have them.
        score += geo_score * 0.4
        
        return min(score, 1.0)

    def _score_volunteer(self, request: RequestRecord, vol: VolunteerProfileRecord) -> float:
        """Compute match score for a volunteer (0.0 - 1.0)."""
        score = 0.0
        
        # Keyword overlap (30%)
        keyword_score = self._compute_keyword_overlap(
            request.title + " " + request.description,
            vol.specialty or "" + " " + (vol.bio or "")
        )
        score += keyword_score * 0.3
        
        # Proximity (70% - since no 'verified' for individuals)
        geo_score = self._compute_geo_score(request, vol)
        score += geo_score * 0.7
        
        return min(score, 1.0)

    def _compute_keyword_overlap(self, text1: str, text2: str) -> float:
        """Simple Jaccard-ish similarity on cleaned tokens."""
        def get_tokens(t): return set(re.findall(r"\w+", t.lower()))
        s1, s2 = get_tokens(text1), get_tokens(text2)
        if not s1 or not s2: return 0.0
        intersection = s1.intersection(s2)
        # Weight important words (flood, rescue, etc.) if needed, but keeping it simple for now
        return len(intersection) / min(len(s1), 20) # Normalize by request tokens cap

    def _compute_geo_score(self, request: RequestRecord, entity: any) -> float:
        """Score based on Haversine distance (1.0 = same spot, 0.0 = far)."""
        if not request.latitude or not request.longitude:
            return 0.5 # Neutral if no request location
            
        if not hasattr(entity, "latitude") or not entity.latitude:
            return 0.5 # Neutral if no entity location
            
        try:
            r_lat, r_lng = float(request.latitude), float(request.longitude)
            e_lat, e_lng = float(entity.latitude), float(entity.longitude)
            
            # Simple Haversine (short version)
            dist_km = self._haversine(r_lat, r_lng, e_lat, e_lng)
            
            # 1.0 at 0km, 0.5 at 50km, 0.0 at 500km+
            if dist_km < 1: return 1.0
            score = 1.0 - (math.log10(dist_km + 1) / 3.0) # approx 0 at 1000km
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return 0.5

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371 # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def _get_match_reason(self, request: RequestRecord, entity: any) -> str:
        """Simple string explaining why it matched."""
        # This will be refined with LLM help in later phases, but for formal it's rule-based
        if isinstance(entity, OrganizationRecord):
            return f"Registered {entity.type} matched by keywords and verification status."
        return f"Volunteer matched by specialty/bio overlap and location."
