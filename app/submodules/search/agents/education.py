"""Education access topic agent."""

from app.submodules.search.base_agent import BaseSearchAgent


class EducationAgent(BaseSearchAgent):
    """Crawls for education NGOs and access-to-education initiatives in tribal/rural areas."""

    @property
    def topic(self) -> str:
        return "education"

    @property
    def agent_name(self) -> str:
        return "education_agent"
