"""
Embedding MCP tools: embed_text, summarize_and_extract.
"""

from typing import Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.mcp.guardrails import validate_llm_output
from app.repositories.openai_client import OpenAIClientRepository

logger = get_logger(__name__)


class EntitiesSchema(BaseModel):
    people: list[str] = []
    orgs: list[str] = []
    locations: list[str] = []
    events: list[str] = []


class SummarizeExtractOutput(BaseModel):
    title: str
    summary: str = Field(description="2-4 sentence summary")
    entities: EntitiesSchema
    topic_tags: list[str]
    geo_tags: list[str]
    event_date: Optional[str] = None


class EmbeddingTools:
    def __init__(self, openai_repo: OpenAIClientRepository):
        self.openai_repo = openai_repo

    async def embed_text(self, text: str) -> list[float]:
        """
        MCP tool: generate a 1536-dimensional embedding.
        Truncates input at 8000 characters.
        """
        truncated = text[:8000]
        return await self.openai_repo.embed(truncated)

    async def summarize_and_extract(self, raw_text: str, source_url: str) -> dict:
        """
        MCP tool: summarize article text and extract entities using GPT-4o.
        Input truncated at 8000 characters.
        Returns: {summary, title, entities, topic_tags, geo_tags, event_date}
        """
        truncated = raw_text[:8000]
        
        # System prompt path (loaded by caller or from config)
        # For simplicity in this tool, we assume the system prompt is passed or known.
        # In this implementation, we use a standard prompt template.
        system_prompt = (
            "You are an expert information extractor. Extract structured data from the provided article text. "
            "Summary must be 2-4 sentences. topic_tags must be from: floods, drought, healthcare, disaster, welfare, "
            "education, livelihood, environment. geo_tags should be normalized location names."
        )
        
        user_message = f"Source URL: {source_url}\n\nContent:\n{truncated}"
        
        raw_response = await self.openai_repo.chat_complete(
            system_prompt=system_prompt,
            user_message=user_message,
            response_format=SummarizeExtractOutput
        )
        
        # validate_llm_output already returns the model instance if successful
        parsed = SummarizeExtractOutput.model_validate_json(raw_response)
        return parsed.model_dump()
