"""Integration tests for formal_matcher.py — Phase 5."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.submodules.matching.formal_matcher import FormalMatcher
from app.submodules.matching.schemas import (
    OrganizationRecord,
    RequestRecord,
    VolunteerProfileRecord,
)


@pytest.fixture
def mock_formal_repo():
    return MagicMock()


@pytest.fixture
def formal_matcher(mock_formal_repo):
    return FormalMatcher(mock_formal_repo)


@pytest.mark.asyncio
async def test_formal_match_ranking(formal_matcher, mock_formal_repo):
    """Verify that verified organizations and keyword-rich volunteers rank higher."""
    
    # 1. Setup Request
    request = RequestRecord(
        id=uuid4(),
        title="Flood Relief in Kerala",
        description="Looking for NGOs that can provide boat rescue and food packets in Kerala floods.",
        location_type="location",
        latitude="10.8505",
        longitude="76.2711",
        issuer_type="volunteer",
        issuer_id=uuid4(),
        status="open",
        progress_percent=0,
        agent_research_status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 2. Setup Mock Data
    verified_ngo = OrganizationRecord(
        id=uuid4(),
        name="Kerala Relief NGO",
        type="ngo",
        description="Experienced in flood rescue and boat supply in Kerala.",
        verified=True,
        status="registered",
        created_by=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    unverified_ngo = OrganizationRecord(
        id=uuid4(),
        name="General Help Kerala",
        type="ngo",
        description="General social welfare services, flood relief in Kerala region.",
        verified=False,
        status="registered",
        created_by=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    nearby_volunteer = VolunteerProfileRecord(
        id=uuid4(),
        user_id=uuid4(),
        name="Local Rescue Expert",
        latitude="10.8500", # Very close
        longitude="76.2700",
        specialty="Flood rescue technician with boat license",
        bio="I live in Kerala and help with flood relief.",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    far_volunteer = VolunteerProfileRecord(
        id=uuid4(),
        user_id=uuid4(),
        name="Far Away Helper",
        latitude="28.6139", # Delhi
        longitude="77.2090",
        specialty="Data entry",
        bio="Available for remote work only.",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_formal_repo.get_registered_organizations = AsyncMock(return_value=[verified_ngo, unverified_ngo])
    mock_formal_repo.get_active_volunteers = AsyncMock(return_value=[nearby_volunteer, far_volunteer])

    # 3. Execute
    result = await formal_matcher.match(request)

    # 4. Assertions
    assert len(result.matches) > 0
    
    # Verified NGO with keywords should be #1 or high
    # Nearby volunteer with keywords should be #1 or high
    # Delhi volunteer should be low
    
    matches = {m.name: m for m in result.matches}
    assert "Kerala Relief NGO" in matches
    assert "Local Rescue Expert" in matches
    
    # Kerala Relief NGO (Verified=0.5 + keywords ~0.3-0.4) should beat General Help Kerala (Verified=0 + keywords ~0.1)
    assert matches["Kerala Relief NGO"].confidence > matches["General Help Kerala"].confidence
    
    # Local Rescue Expert (Geo ~1.0*0.6=0.6 + keywords ~0.3-0.4*0.4=0.15) approx 0.75
    # Far Away Helper (Geo ~0 + keywords 0) approx 0
    assert matches["Local Rescue Expert"].confidence > matches["Far Away Helper"].confidence if "Far Away Helper" in matches else True

    # Check top match
    top_match = result.matches[0]
    assert top_match.name in ["Kerala Relief NGO", "Local Rescue Expert"]
