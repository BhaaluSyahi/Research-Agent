"""
OpenAIClientRepository — embedding generation and chat completion.
All OpenAI calls in the codebase go through this class.
"""

import json
from typing import Any, Optional, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.exceptions import ChatCompletionError, EmbeddingError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIClientRepository(BaseRepository):
    def __init__(self, client: AsyncOpenAI, embedding_model: str, chat_model: str) -> None:
        self.client = client
        self.embedding_model = embedding_model
        self.chat_model = chat_model

    async def embed(self, text: str) -> list[float]:
        """
        Generate a 1536-dimensional embedding for the input text.
        Uses text-embedding-3-small by default.
        """
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.embedding_model,
            )
            embedding = response.data[0].embedding
            logger.info(
                "embedding_generated",
                module="repositories",
                operation="embed",
                model=self.embedding_model,
                dimensions=len(embedding),
            )
            return embedding
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
        Run a chat completion call.
        Returns the raw text content of the model response.
        If response_format is a Pydantic model subclass, uses structured outputs
        (client.beta.chat.completions.parse) and returns the JSON string of the parsed model.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        try:
            if response_format is not None and issubclass(response_format, BaseModel):
                # Structured output — parse into Pydantic model
                parsed = await self.client.beta.chat.completions.parse(
                    model=self.chat_model,
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format,
                )
                result_model = parsed.choices[0].message.parsed
                content = result_model.model_dump_json() if result_model is not None else "{}"
            else:
                completion = await self.client.chat.completions.create(
                    model=self.chat_model,
                    messages=messages,
                    temperature=temperature,
                )
                content = completion.choices[0].message.content or ""

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
