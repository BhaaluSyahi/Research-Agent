"""
GeminiClientRepository — embedding generation and chat completion via Google Gemini.
All LLM calls in the codebase go through this class.

Previously OpenAIClientRepository; re-implemented on top of google-genai SDK.
The class is aliased as OpenAIClientRepository so existing imports need zero changes.
"""

import json
from typing import Any, Optional, Type, TypeVar

from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel

from app.core.exceptions import ChatCompletionError, EmbeddingError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiClientRepository(BaseRepository):
    def __init__(self, client: genai.Client, embedding_model: str, chat_model: str) -> None:
        self.client = client
        self.embedding_model = embedding_model
        self.chat_model = chat_model

    async def embed(self, text: str) -> list[float]:
        """
        Generate a 768-dimensional embedding for the input text.
        Uses text-embedding-004 by default.
        """
        try:
            response = await self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=genai_types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )
            # response.embeddings is a list of ContentEmbedding objects
            embedding = response.embeddings[0].values
            logger.info(
                "embedding_generated",
                module="repositories",
                operation="embed",
                model=self.embedding_model,
                dimensions=len(embedding),
            )
            return list(embedding)
        except Exception as exc:
            logger.error(
                "embedding_failed",
                module="repositories",
                operation="embed",
                model=self.embedding_model,
                error=str(exc),
            )
            raise EmbeddingError(f"Embedding generation failed: {exc}") from exc

    async def chat_complete(
        self,
        system_prompt: str,
        user_message: str,
        response_format: Optional[Type[T]] = None,
        temperature: float = 0.0,
    ) -> str:
        """
        Run a chat completion call via Gemini.
        Returns the raw text content of the model response.

        If response_format is a Pydantic model subclass, uses structured output
        (response_schema + response_mime_type='application/json') and returns
        the JSON string of the parsed model so callers can do model_validate_json().
        """
        contents = [
            genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)],
            )
        ]

        config_kwargs: dict[str, Any] = {
            "system_instruction": system_prompt,
            "temperature": temperature,
        }

        if response_format is not None and issubclass(response_format, BaseModel):
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_format

        try:
            response = await self.client.aio.models.generate_content(
                model=self.chat_model,
                contents=contents,
                config=genai_types.GenerateContentConfig(**config_kwargs),
            )

            if response_format is not None and issubclass(response_format, BaseModel):
                # SDK populates .parsed when response_schema is a Pydantic model
                if response.parsed is not None:
                    content = response.parsed.model_dump_json()
                else:
                    # Fallback: parse the raw text ourselves
                    content = response.text or "{}"
                    # Validate it parses — let caller handle bad JSON
            else:
                content = response.text or ""

            logger.info(
                "chat_completion_done",
                module="repositories",
                operation="chat_complete",
                model=self.chat_model,
                structured=response_format is not None,
            )
            return content

        except Exception as exc:
            logger.error(
                "chat_completion_failed",
                module="repositories",
                operation="chat_complete",
                model=self.chat_model,
                error=str(exc),
            )
            raise ChatCompletionError(f"Chat completion failed: {exc}") from exc


# Alias — all existing imports of OpenAIClientRepository continue to work unchanged.
OpenAIClientRepository = GeminiClientRepository
