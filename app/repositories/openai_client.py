"""
OpenAIClientRepository — embedding generation and chat completion.
All OpenAI calls in the codebase go through this class.
"""

from openai import AsyncOpenAI

from app.repositories.base import BaseRepository


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
        # TODO: implement
        raise NotImplementedError

    async def chat_complete(
        self,
        system_prompt: str,
        user_message: str,
        response_format: type | None = None,
        temperature: float = 0.0,
    ) -> str:
        """
        Run a chat completion call.
        Returns the raw text content of the model response.
        If response_format is provided, parse and validate accordingly.
        """
        # TODO: implement
        raise NotImplementedError
