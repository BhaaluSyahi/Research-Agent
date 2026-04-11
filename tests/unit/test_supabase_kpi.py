"""Unit tests for SupabaseKpiRepository."""

from datetime import datetime
from uuid import uuid4

import pytest
from supabase import AsyncClient

from app.repositories.supabase_kpi import CrawlLogRecord, KpiRecord, SupabaseKpiRepository


@pytest.mark.asyncio
async def test_write_kpi(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseKpiRepository(mock_client)
    request_id = uuid4()

    kpi = KpiRecord(
        request_id=request_id,
        pipeline_started_at=datetime.now(),
        formal_matches_count=2,
        informal_matches_count=3,
        on_demand_triggered=False,
    )

    mock_table = mocker.MagicMock()
    mock_insert = mocker.MagicMock()
    
    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=[]))

    await repo.write_kpi(kpi)

    mock_table.insert.assert_called_once()
    args, _ = mock_table.insert.call_args
    payload = args[0]
    assert payload["request_id"] == str(request_id)
    assert payload["formal_matches_count"] == 2


@pytest.mark.asyncio
async def test_write_crawl_log(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseKpiRepository(mock_client)

    log = CrawlLogRecord(
        agent_name="floods_agent",
        run_type="scheduled",
        topic="floods",
        tavily_results_count=5,
        new_entries_count=2,
    )

    mock_table = mocker.MagicMock()
    mock_insert = mocker.MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=[]))

    await repo.write_crawl_log(log)

    mock_table.insert.assert_called_once()
    args, _ = mock_table.insert.call_args
    assert args[0]["agent_name"] == "floods_agent"
    assert args[0]["topic"] == "floods"
