"""Unit tests for InformalMatcher."""

from datetime import datetime
from uuid import uuid4
import pytest
from app.submodules.matching.informal_matcher import InformalMatcher
from app.submodules.matching.schemas import RequestRecord
from app.repositories.supabase_informal import InformalEntry, InformalEntryEntities


@pytest.mark.asyncio
async def test_informal_matcher_success(mocker):
    # Mock repos
    mock_informal_repo = mocker.AsyncMock()
    mock_gemini_repo = mocker.AsyncMock()
    
    matcher = InformalMatcher(mock_informal_repo, mock_gemini_repo)
    
    # Setup test data
    request = RequestRecord(
        id=uuid4(),
        title="Help needed",
        description="We need flood relief supplies",
        location_type="location",
        issuer_type="organization",
        issuer_id=uuid4(),
        status="open",
        progress_percent=0,
        agent_research_status="in_progress",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    mock_gemini_repo.embed.return_value = [0.1] * 768
    
    mock_entries = [
        InformalEntry(
            id=uuid4(),
            content_hash="hash1",
            title="News 1",
            summary="Summary 1",
            source_url="https://news1.com",
            trust_score=0.9,
            entities=InformalEntryEntities(people=["Person A"], orgs=["Org X"]),
            topic_tags=["floods"],
            geo_tags=["kerala"],
            indexed_at=datetime.utcnow(),
            similarity=0.88
        )
    ]
    mock_informal_repo.search_similar.return_value = mock_entries
    
    # Run match
    matches = await matcher.match(request)
    
    # Assertions
    assert len(matches) == 1
    assert matches[0].title == "News 1"
    assert matches[0].cosine_score == 0.88
    assert matches[0].entities["people"] == ["Person A"]
    mock_gemini_repo.embed.assert_called_once_with(request.description)
    mock_informal_repo.search_similar.assert_called_once()
