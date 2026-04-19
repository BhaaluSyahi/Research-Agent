"""
GeminiClientRepository — embedding generation and chat completion via Google Gemini.
All LLM calls in the codebase go through this class.
"""

import asyncio
import json
import random
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
        self._semaphore = asyncio.Semaphore(2)  # Cap concurrent LLM calls

    async def _call_with_retry(self, func: Any, *args, **kwargs) -> Any:
        """Generic retry wrapper for Gemini calls to handle 429 RESOURCE_EXHAUSTED."""
        max_retries = 5
        base_delay = 10.0  # Start with 10s delay for 429s

        for attempt in range(max_retries):
            async with self._semaphore:
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    err_msg = str(exc).upper()
                    is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        # Exponential backoff: 10s, 20s, 40s, 80s... with jitter
                        delay = (base_delay * (2 ** attempt)) + (random.random() * 2)
                        logger.warning(
                            "gemini_rate_limited_retrying",
                            attempt=attempt + 1,
                            delay_seconds=round(delay, 2),
                            error=str(exc)
                        )
                        await asyncio.sleep(delay)
                        continue
                    
                    # If not a rate limit or we're out of retries, re-raise
                    raise

    async def embed(self, text: str) -> list[float]:
        """
        Generate a 768-dimensional embedding for the input text.
        Uses text-embedding-004 by default.
        """
        try:
            response = await self._call_with_retry(
                self.client.aio.models.embed_content,
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
            response = await self._call_with_retry(
                self.client.aio.models.generate_content,
                model=self.chat_model,
                contents=contents,
                config=genai_types.GenerateContentConfig(**config_kwargs),
            )

            if response_format is not None and issubclass(response_format, BaseModel):
                if response.parsed is not None:
                    content = response.parsed.model_dump_json()
                else:
                    content = response.text or "{}"
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


