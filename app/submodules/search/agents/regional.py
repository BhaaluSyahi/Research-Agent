"""Regional (South + Northeast India) topic agents."""

from app.submodules.search.base_agent import BaseSearchAgent


class RegionalSouthAgent(BaseSearchAgent):
    """Crawls broadly for NGO/volunteer activity in South India (Kerala, Karnataka, Tamil Nadu)."""

    @property
    def topic(self) -> str:
        return "regional_south"

    @property
    def agent_name(self) -> str:
        return "regional_south_agent"


class RegionalNortheastAgent(BaseSearchAgent):
    """Crawls broadly for NGO/volunteer activity in Northeast India (Assam, Meghalaya, Manipur)."""

    @property
    def topic(self) -> str:
        return "regional_northeast"

    @property
    def agent_name(self) -> str:
        return "regional_northeast_agent"
