"""Unit tests for OpenAIClientRepository."""

import pytest
from app.core.exceptions import EmbeddingError, ChatCompletionError
from app.repositories.openai_client import OpenAIClientRepository


@pytest.mark.asyncio
async def test_embed_success(mocker) -> None:
    mock_openai_client = mocker.AsyncMock()
    repo = OpenAIClientRepository(mock_openai_client, "emb-model", "chat-model")
    
    # Mocking client.embeddings.create().data[0].embedding
    mock_embedding = [0.1] * 1536
    mock_openai_client.embeddings.create.return_value = mocker.MagicMock(
        data=[mocker.MagicMock(embedding=mock_embedding)]
    )

    result = await repo.embed("hello world")

    assert result == mock_embedding
    mock_openai_client.embeddings.create.assert_called_once_with(
        input="hello world", model="emb-model"
    )


@pytest.mark.asyncio
async def test_chat_complete_text(mocker) -> None:
    mock_openai_client = mocker.AsyncMock()
    repo = OpenAIClientRepository(mock_openai_client, "emb-model", "chat-model")
    
    mock_completion = mocker.MagicMock()
    mock_completion.choices = [mocker.MagicMock(message=mocker.MagicMock(content="Mocked response"))]
    mock_openai_client.chat.completions.create.return_value = mock_completion

    response = await repo.chat_complete("sys", "user")

    assert response == "Mocked response"
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_embed_error_wrapping(mocker) -> None:
    mock_openai_client = mocker.AsyncMock()
    repo = OpenAIClientRepository(mock_openai_client, "emb-model", "chat-model")
    mock_openai_client.embeddings.create.side_effect = Exception("Rate limit")

    with pytest.raises(EmbeddingError):
        await repo.embed("text")
