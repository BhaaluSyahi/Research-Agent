"""Unit tests for TavilyRepository."""

import pytest
from app.core.exceptions import TavilyError
from app.repositories.tavily import TavilyRepository


@pytest.mark.asyncio
async def test_search_success(mocker) -> None:
    mock_tavily_client = mocker.AsyncMock()
    repo = TavilyRepository(mock_tavily_client)
    
    mock_response = {
        "results": [
            {
                "url": "https://news.com/1",
                "title": "Title 1",
                "content": "Snippet 1",
                "score": 0.95
            }
        ]
    }
    mock_tavily_client.search.return_value = mock_response

    results = await repo.search("test query")

    assert len(results) == 1
    assert results[0].url == "https://news.com/1"
    assert results[0].score == 0.95
    mock_tavily_client.search.assert_called_once()


@pytest.mark.asyncio
async def test_tavily_error_wrapping(mocker) -> None:
    mock_tavily_client = mocker.AsyncMock()
    repo = TavilyRepository(mock_tavily_client)
    mock_tavily_client.search.side_effect = Exception("API Key Expired")

    with pytest.raises(TavilyError):
        await repo.search("query")
