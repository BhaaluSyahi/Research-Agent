"""Floods topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class FloodsAgent(BaseSearchAgent):
    """Crawls for flood relief NGOs, rescue operations, and community response content."""

    @property
    def topic(self) -> str:
        return "floods"

    @property
    def agent_name(self) -> str:
        return "floods_agent"
