import asyncio
from typing import Dict, Type

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logging import get_logger
from app.repositories.supabase_strategy import SupabaseStrategyRepository
from app.repositories.supabase_kpi import SupabaseKpiRepository
from app.repositories.sqs import SQSRepository
from app.submodules.search.indexer import ContentIndexer
from app.mcp.tools.search_tools import SearchTools
from app.submodules.search.base_agent import BaseSearchAgent

# Import all agents
from app.submodules.search.agents.floods import FloodsAgent
from app.submodules.search.agents.drought import DroughtAgent
from app.submodules.search.agents.healthcare import HealthcareAgent
from app.submodules.search.agents.disaster import DisasterAgent
from app.submodules.search.agents.welfare import WelfareAgent
from app.submodules.search.agents.education import EducationAgent
from app.submodules.search.agents.livelihood import LivelihoodAgent
from app.submodules.search.agents.environment import EnvironmentAgent
from app.submodules.search.agents.regional import RegionalSouthAgent, RegionalNortheastAgent

logger = get_logger(__name__)


AGENT_MAP: Dict[str, Type[BaseSearchAgent]] = {
    "floods": FloodsAgent,
    "drought": DroughtAgent,
    "healthcare": HealthcareAgent,
    "disaster": DisasterAgent,
    "welfare": WelfareAgent,
    "education": EducationAgent,
    "livelihood": LivelihoodAgent,
    "environment": EnvironmentAgent,
    "regional_south": RegionalSouthAgent,
    "regional_northeast": RegionalNortheastAgent,
}


class SearchScheduler:
    def __init__(
        self,
        strategy_repo: SupabaseStrategyRepository,
        kpi_repo: SupabaseKpiRepository,
        sqs_repo: SQSRepository,
        search_tools: SearchTools,
        indexer: ContentIndexer
    ):
        self.scheduler = AsyncIOScheduler()
        self.strategy_repo = strategy_repo
        self.kpi_repo = kpi_repo
        self.sqs_repo = sqs_repo
        self.search_tools = search_tools
        self.indexer = indexer
        self.agents: Dict[str, BaseSearchAgent] = {}

    def _get_agent(self, topic: str) -> BaseSearchAgent | None:
        """Instantiate the correct agent for the topic."""
        agent_class = AGENT_MAP.get(topic)
        if not agent_class:
            logger.warning("no_agent_class_found", topic=topic)
            return None
            
        return agent_class(
            strategy_repo=self.strategy_repo,
            kpi_repo=self.kpi_repo,
            sqs_repo=self.sqs_repo,
            search_tools=self.search_tools,
            indexer=self.indexer
        )

    async def schedule_all_active(self):
        """Fetch all active strategies and register jobs for them."""
        strategies = await self.strategy_repo.get_all_active_strategies()
        for strategy in strategies:
            if strategy.topic in self.agents:
                continue
                
            agent = self._get_agent(strategy.topic)
            if agent:
                self.agents[strategy.topic] = agent
                self.scheduler.add_job(
                    agent.run,
                    trigger=IntervalTrigger(hours=strategy.crawl_frequency_hours),
                    id=f"crawl_{strategy.topic}",
                    name=f"Crawl agent for {strategy.topic}",
                    replace_existing=True
                )
                logger.info("agent_scheduled", topic=strategy.topic, interval_hours=strategy.crawl_frequency_hours)

    async def start(self):
        """Start the scheduler and initial enrollment."""
        await self.schedule_all_active()
        self.scheduler.start()
        logger.info("search_scheduler_started", active_agents=list(self.agents.keys()))

    async def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("search_scheduler_stopped")
