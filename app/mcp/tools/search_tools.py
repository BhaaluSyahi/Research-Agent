"""
Search MCP tools: web_search, classify_request.
"""

from pydantic import BaseModel
from app.core.logging import get_logger
from app.repositories.tavily import TavilyRepository
from app.repositories.gemini_client import GeminiClientRepository

logger = get_logger(__name__)


class ClassificationOutput(BaseModel):
    topic_tags: list[str]
    geo_tags: list[str]
    primary_topic: str


class SearchTools:
    def __init__(self, tavily_repo: TavilyRepository, gemini_repo: GeminiClientRepository):
        self.tavily_repo = tavily_repo
        self.gemini_repo = gemini_repo

    async def web_search(
        self,
        query: str,
        max_results: int = 5,
        include_domains: list[str] | None = None,
    ) -> list[dict]:
        """
        MCP tool: execute a Tavily web search.
        Guardrails (length, injection) are handled by the dispatcher before this call.
        """
        results = await self.tavily_repo.search(
            query=query,
            max_results=max_results,
            include_domains=include_domains
        )
        
        # Blocked domains filter (Layer 2)
        from app.mcp.guardrails import _BLOCKED_DOMAINS
        filtered = [
            r.model_dump() for r in results 
            if not any(domain in r.url for domain in _BLOCKED_DOMAINS)
        ]
        return filtered

    async def classify_request(self, title: str, description: str) -> dict:
        """
        MCP tool: classify a help request into topic tags and extract geographic entities.
        """
        system_prompt = (
            "Classify the following help request into topic tags and extract geographic locations. "
            "Topics: floods, drought, healthcare, disaster, welfare, education, livelihood, environment."
        )
        
        user_message = f"<user_request>\nTitle: {title}\nDescription: {description}\n</user_request>"
        
        raw_response = await self.gemini_repo.chat_complete(
            system_prompt=system_prompt,
            user_message=user_message,
            response_format=ClassificationOutput
        )
        
        parsed = ClassificationOutput.model_validate_json(raw_response)
        return parsed.model_dump()
