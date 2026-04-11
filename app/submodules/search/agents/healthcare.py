"""Healthcare topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class HealthcareAgent(BaseSearchAgent):
    """Crawls for mobile health NGOs, rural healthcare camps, and medical volunteer content."""

    @property
    def topic(self) -> str:
        return "healthcare"

    @property
    def agent_name(self) -> str:
        return "healthcare_agent"
