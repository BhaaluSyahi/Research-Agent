"""Livelihood support topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class LivelihoodAgent(BaseSearchAgent):
    """Crawls for livelihood NGOs and farmer/artisan support content."""

    @property
    def topic(self) -> str:
        return "livelihood"

    @property
    def agent_name(self) -> str:
        return "livelihood_agent"
