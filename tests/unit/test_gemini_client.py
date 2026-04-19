"""Unit tests for GeminiClientRepository."""

import pytest
from app.core.exceptions import EmbeddingError, ChatCompletionError
from app.repositories.gemini_client import GeminiClientRepository


@pytest.mark.asyncio
async def test_embed_success(mocker) -> None:
    mock_gemini_client = mocker.AsyncMock()
    repo = GeminiClientRepository(mock_gemini_client, "emb-model", "chat-model")
    
    # Mocking client.aio.models.embed_content().embeddings[0].values
    mock_embedding = [0.1] * 768
    mock_response = mocker.MagicMock()
    mock_embedding_obj = mocker.MagicMock()
    mock_embedding_obj.values = mock_embedding
    mock_response.embeddings = [mock_embedding_obj]
    
    # Use patch or direct assignment to mock the nested async call
    mock_gemini_client.aio.models.embed_content.return_value = mock_response

    result = await repo.embed("hello world")

    assert result == mock_embedding
    mock_gemini_client.aio.models.embed_content.assert_called_once()


@pytest.mark.asyncio
async def test_chat_complete_text(mocker) -> None:
    mock_gemini_client = mocker.AsyncMock()
    repo = GeminiClientRepository(mock_gemini_client, "emb-model", "chat-model")
    
    mock_response = mocker.MagicMock()
    mock_response.text = "Mocked response"
    mock_response.parsed = None
    mock_gemini_client.aio.models.generate_content.return_value = mock_response

    response = await repo.chat_complete("sys", "user")

    assert response == "Mocked response"
    mock_gemini_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_embed_error_wrapping(mocker) -> None:
    mock_gemini_client = mocker.AsyncMock()
    repo = GeminiClientRepository(mock_gemini_client, "emb-model", "chat-model")
    mock_gemini_client.aio.models.embed_content.side_effect = Exception("Rate limit")

    with pytest.raises(EmbeddingError):
        await repo.embed("text")
