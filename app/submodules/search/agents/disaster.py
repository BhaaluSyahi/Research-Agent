"""Disaster relief topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class DisasterAgent(BaseSearchAgent):
    """Crawls for general disaster response NGOs and emergency relief operations."""

    @property
    def topic(self) -> str:
        return "disaster"

    @property
    def agent_name(self) -> str:
        return "disaster_agent"
