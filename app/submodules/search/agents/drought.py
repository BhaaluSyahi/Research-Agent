"""Drought topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class DroughtAgent(BaseSearchAgent):
    """Crawls for drought response NGOs, water scarcity relief, and village support content."""

    @property
    def topic(self) -> str:
        return "drought"

    @property
    def agent_name(self) -> str:
        return "drought_agent"
