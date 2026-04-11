"""Unit tests for SupabaseFormalRepository."""

from uuid import uuid4

import pytest
from supabase import AsyncClient

from app.repositories.supabase_formal import SupabaseFormalRepository


@pytest.mark.asyncio
async def test_get_registered_organizations(mocker) -> None:
    # Mock supabase client
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseFormalRepository(mock_client)

    # Mock response data
    mock_data = [
        {
            "id": str(uuid4()),
            "name": "NGO 1",
            "type": "ngo",
            "verified": True,
            "status": "registered",
            "created_by": str(uuid4()),
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
    ]

    # Mock the chained call: client.table().select().eq().execute()
    mock_table = mocker.MagicMock()
    mock_select = mocker.MagicMock()
    mock_eq = mocker.MagicMock()
    
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=mock_data))

    results = await repo.get_registered_organizations()

    assert len(results) == 1
    assert results[0].name == "NGO 1"
    mock_client.table.assert_called_once_with("organizations")


@pytest.mark.asyncio
async def test_get_request_by_id_found(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseFormalRepository(mock_client)
    request_id = uuid4()

    mock_data = {
        "id": str(request_id),
        "title": "Flood help",
        "description": "Need aid",
        "location_type": "location",
        "issuer_type": "volunteer",
        "issuer_id": str(uuid4()),
        "status": "open",
        "progress_percent": 0,
        "agent_research_status": "pending",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    mock_table = mocker.MagicMock()
    mock_select = mocker.MagicMock()
    mock_eq = mocker.MagicMock()
    mock_maybe_single = mocker.MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.maybe_single.return_value = mock_maybe_single
    mock_maybe_single.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=mock_data))

    result = await repo.get_request_by_id(request_id)

    assert result is not None
    assert result.id == request_id
    assert result.title == "Flood help"


@pytest.mark.asyncio
async def test_update_request_status(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseFormalRepository(mock_client)
    request_id = uuid4()

    mock_table = mocker.MagicMock()
    mock_update = mocker.MagicMock()
    mock_eq = mocker.MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq
    mock_eq.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=[]))

    await repo.update_request_status(request_id, "in_progress", {"some": "recommendation"})

    mock_table.update.assert_called_once_with(
        {"agent_research_status": "in_progress", "recommendations": {"some": "recommendation"}}
    )
    mock_eq.execute.assert_called_once()
