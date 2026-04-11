"""Unit tests for SupabaseInformalRepository."""

from datetime import datetime
from uuid import uuid4

import pytest
from supabase import AsyncClient

from app.core.exceptions import OptimisticLockError
from app.repositories.supabase_informal import InformalEntryCreate, SupabaseInformalRepository


@pytest.mark.asyncio
async def test_get_by_content_hash_found(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseInformalRepository(mock_client)
    content_hash = "abc-123"

    mock_data = {
        "id": str(uuid4()),
        "content_hash": content_hash,
        "summary": "Some news summary",
        "source_url": "https://example.com",
        "indexed_at": "2024-01-01T00:00:00Z",
        "version": 1,
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

    entry = await repo.get_by_content_hash(content_hash)

    assert entry is not None
    assert entry.content_hash == content_hash
    assert entry.version == 1


@pytest.mark.asyncio
async def test_upsert_entry_optimistic_lock_fail(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseInformalRepository(mock_client)
    
    content_hash = "abc-123"
    # Existing entry in DB has version 2
    mock_data = {
        "id": str(uuid4()),
        "content_hash": content_hash,
        "summary": "Old",
        "source_url": "https://ex.com",
        "indexed_at": "2024-01-01T00:00:00Z",
        "version": 2,
    }

    # Mock get_by_content_hash internally
    mocker.patch.object(repo, 'get_by_content_hash', return_value=mocker.MagicMock(version=2, content_hash=content_hash))

    new_entry = InformalEntryCreate(
        content_hash=content_hash,
        summary="New",
        source_url="https://ex.com",
        embedding=[0.1] * 1536,
        indexed_by="test",
        version=1  # Version mismatch!
    )

    with pytest.raises(OptimisticLockError):
        await repo.upsert_entry(new_entry)


@pytest.mark.asyncio
async def test_search_similar(mocker) -> None:
    mock_client = mocker.AsyncMock(spec=AsyncClient)
    repo = SupabaseInformalRepository(mock_client)
    
    embedding = [0.1] * 1536
    mock_data = [
        {
            "id": str(uuid4()),
            "content_hash": "hash1",
            "summary": "Result 1",
            "source_url": "https://res.com",
            "indexed_at": "2024-01-01T00:00:00Z",
            "version": 1,
        }
    ]

    mock_rpc = mocker.MagicMock()
    mock_client.rpc.return_value = mock_rpc
    mock_rpc.execute = mocker.AsyncMock(return_value=mocker.MagicMock(data=mock_data))

    from app.repositories.supabase_informal import SearchFilters
    filters = SearchFilters(top_k=5)
    
    results = await repo.search_similar(embedding, filters)

    assert len(results) == 1
    assert results[0].content_hash == "hash1"
    mock_client.rpc.assert_called_once()
