"""Social welfare topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class WelfareAgent(BaseSearchAgent):
    """Crawls for community welfare NGOs and social support content."""

    @property
    def topic(self) -> str:
        return "welfare"

    @property
    def agent_name(self) -> str:
        return "welfare_agent"
