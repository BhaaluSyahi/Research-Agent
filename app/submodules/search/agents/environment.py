"""Environment conservation topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class EnvironmentAgent(BaseSearchAgent):
    """Crawls for environment conservation NGOs and ecological relief content."""

    @property
    def topic(self) -> str:
        return "environment"

    @property
    def agent_name(self) -> str:
        return "environment_agent"
