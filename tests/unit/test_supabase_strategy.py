"""Unit tests for SupabaseStrategyRepository."""

from datetime import datetime

import pytest
from supabase import AsyncClient

from app.repositories.supabase_strategy import SupabaseStrategyRepository


@pytest.mark.asyncio
async def test_get_strategy_for_topic_found(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseStrategyRepository(mock_client)

    mock_data = {
        "id": "strat-id",
        "topic": "floods",
        "search_queries": [{"query": "flood test", "weight": 1.0}],
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    mock_table = mocker.MagicMock()
    mock_select = mocker.MagicMock()
    mock_eq_1 = mocker.MagicMock()
    mock_eq_2 = mocker.MagicMock()
    mock_maybe_single = mocker.MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq_1
    mock_eq_1.eq.return_value = mock_eq_2
    mock_eq_2.maybe_single.return_value = mock_maybe_single
    mock_maybe_single.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=mock_data))

    strategy = await repo.get_strategy_for_topic("floods")

    assert strategy is not None
    assert strategy.topic == "floods"
    assert len(strategy.search_queries) == 1
    assert strategy.search_queries[0].query == "flood test"


@pytest.mark.asyncio
async def test_update_last_run(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseStrategyRepository(mock_client)

    mock_table = mocker.MagicMock()
    mock_update = mocker.MagicMock()
    mock_eq = mocker.MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq
    mock_eq.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=[]))

    await repo.update_last_run("floods", 10, 5)

    mock_table.update.assert_called_once()
    args, _ = mock_table.update.call_args
    payload = args[0]
    assert payload["last_run_articles_found"] == 10
    assert payload["last_run_new_entries"] == 5
    assert "last_run_at" in payload
