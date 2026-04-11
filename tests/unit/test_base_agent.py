import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from app.submodules.search.base_agent import BaseSearchAgent
from app.repositories.supabase_strategy import SearchStrategy, SearchStrategyQuery
from app.repositories.supabase_kpi import CrawlLogRecord

class MockAgent(BaseSearchAgent):
    @property
    def topic(self) -> str:
        return "test_topic"

    @property
    def agent_name(self) -> str:
        return "test_agent"

@pytest.fixture
def mock_repos():
    return {
        "strategy_repo": AsyncMock(),
        "kpi_repo": AsyncMock(),
        "sqs_repo": AsyncMock(),
        "search_tools": AsyncMock(),
        "indexer": AsyncMock()
    }

@pytest.mark.asyncio
async def test_base_agent_run_success(mock_repos):
    # Setup mock strategy
    strategy = SearchStrategy(
        id="test-id",
        topic="test_topic",
        search_queries=[SearchStrategyQuery(query="test query", weight=1.0)],
        is_active=True,
        geo_focus=["kerala"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_repos["strategy_repo"].get_strategy_for_topic.return_value = strategy
    mock_repos["search_tools"].web_search.return_value = [{"url": "http://test.com", "content": "long enough content for indexing"}]
    mock_repos["indexer"].index.return_value = True

    with patch("app.submodules.search.base_agent.IntentLock") as MockLock:
        mock_lock_instance = MockLock.return_value
        mock_lock_instance.acquire = AsyncMock()
        
        agent = MockAgent(**mock_repos)
        await agent.run()

        # Verify lifecycle
        mock_repos["strategy_repo"].get_strategy_for_topic.assert_called_with("test_topic")
        mock_lock_instance.acquire.assert_called()
        mock_repos["search_tools"].web_search.assert_called()
        mock_repos["indexer"].index.assert_called()
        mock_repos["strategy_repo"].update_last_run.assert_called()
        mock_repos["kpi_repo"].write_crawl_log.assert_called()

@pytest.mark.asyncio
async def test_base_agent_run_no_strategy(mock_repos):
    mock_repos["strategy_repo"].get_strategy_for_topic.return_value = None
    
    agent = MockAgent(**mock_repos)
    await agent.run()
    
    mock_repos["search_tools"].web_search.assert_not_called()
    mock_repos["kpi_repo"].write_crawl_log.assert_not_called()
