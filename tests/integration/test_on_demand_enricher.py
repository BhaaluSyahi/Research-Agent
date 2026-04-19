"""Integration test for OnDemandEnricher."""

from uuid import uuid4
from datetime import datetime
import pytest
from app.submodules.search.on_demand import OnDemandEnricher
from app.submodules.matching.schemas import RequestRecord


@pytest.mark.asyncio
async def test_on_demand_enricher_integration(mocker):
    # Mock dependencies
    mock_search_tools = mocker.AsyncMock()
    mock_indexer = mocker.AsyncMock()
    
    # Mocking an async context manager
    mock_lock_ctx = mocker.AsyncMock()
    mock_lock_ctx.__aenter__.return_value = True
    
    mock_intent_lock = mocker.MagicMock()
    mock_intent_lock.acquire.return_value = mock_lock_ctx
    
    enricher = OnDemandEnricher(mock_search_tools, mock_indexer, mock_intent_lock)
    
    request = RequestRecord(
        id=uuid4(),
        title="Recent Kerala floods",
        description="Need information about rescue ops in Wayanad.",
        location_type="location",
        issuer_type="organization",
        issuer_id=uuid4(),
        status="open",
        progress_percent=0,
        agent_research_status="in_progress",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Setup mocks
    mock_search_tools.classify_request.return_value = {
        "primary_topic": "floods",
        "geo_tags": ["Wayanad", "Kerala"]
    }
    mock_search_tools.web_search.return_value = [
        {"url": "https://news.com/1", "content": "Recent news about Wayanad floods..."},
        {"url": "https://news.com/2", "content": "Rescue operations update..."}
    ]
    mock_indexer.index.return_value = True # New article created
    
    # Run
    new_articles = await enricher.enrich_and_retry(request, "floods")
    
    # Assertions
    assert new_articles == 2
    mock_intent_lock.acquire.assert_called_once()
    assert mock_search_tools.web_search.called
    assert mock_indexer.index.call_count == 2
    
    # Check that it skips if lock is False
    mock_lock_ctx.__aenter__.return_value = False
    
    new_articles_skip = await enricher.enrich_and_retry(request, "floods")
    assert new_articles_skip == 0
