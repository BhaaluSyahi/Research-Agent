"""
Proactive Search Scheduler — coordinates the fleet of crawler agents.
Uses APScheduler to run topic-specific agents at varying intervals.
"""

import asyncio
from typing import Dict, Type

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logging import get_logger
from app.repositories.supabase_strategy import SupabaseStrategyRepository
from app.repositories.supabase_kpi import SupabaseKpiRepository, CrawlLogRecord
from app.submodules.search.indexer import ContentIndexer
from app.mcp.tools.search_tools import SearchTools

logger = get_logger(__name__)


class CrawlerAgent:
    """Base logic for a topic-specific crawler agent."""
    def __init__(
        self,
        topic: str,
        strategy_repo: SupabaseStrategyRepository,
        kpi_repo: SupabaseKpiRepository,
        search_tools: SearchTools,
        indexer: ContentIndexer
    ):
        self.topic = topic
        self.strategy_repo = strategy_repo
        self.kpi_repo = kpi_repo
        self.search_tools = search_tools
        self.indexer = indexer

    async def run(self):
        """Single run of the crawler agent."""
        logger.info("agent_run_started", topic=self.topic)
        start_time = asyncio.get_event_loop().time()
        new_entries = 0
        total_found = 0
        
        try:
            # 1. Get Strategy
            strategy = await self.strategy_repo.get_strategy_for_topic(self.topic)
            if not strategy or not strategy.is_active:
                logger.info("agent_skipped", topic=self.topic, reason="no_active_strategy")
                return

            # 2. Search for each query in strategy
            for query_obj in strategy.search_queries:
                results = await self.search_tools.web_search(
                    query=query_obj.query,
                    max_results=5
                )
                total_found += len(results)
                
                # 3. Index
                for res in results:
                    content = res.get("content", "")
                    if len(content) < 200: continue
                    
                    created = await self.indexer.index(
                        raw_text=content,
                        source_url=res["url"],
                        topic=self.topic,
                        indexed_by=f"agent_{self.topic}"
                    )
                    if created:
                        new_entries += 1

            # 4. Update Strategy Metadata
            await self.strategy_repo.update_last_run(
                topic=self.topic,
                articles_found=total_found,
                new_entries=new_entries
            )
            
            # 5. Log KPI
            log = CrawlLogRecord(
                agent_name=f"agent_{self.topic}",
                run_type="scheduled",
                topic=self.topic,
                tavily_results_count=total_found,
                new_entries_count=new_entries,
                execution_time_ms=int((asyncio.get_event_loop().time() - start_time) * 1000)
            )
            await self.kpi_repo.write_crawl_log(log)
            
            logger.info("agent_run_complete", topic=self.topic, new=new_entries, total=total_found)

        except Exception as e:
            logger.error("agent_run_failed", topic=self.topic, error=str(e))


class SearchScheduler:
    def __init__(
        self,
        strategy_repo: SupabaseStrategyRepository,
        kpi_repo: SupabaseKpiRepository,
        search_tools: SearchTools,
        indexer: ContentIndexer
    ):
        self.scheduler = AsyncIOScheduler()
        self.strategy_repo = strategy_repo
        self.kpi_repo = kpi_repo
        self.search_tools = search_tools
        self.indexer = indexer
        self.agents: Dict[str, CrawlerAgent] = {}

    def register_topic(self, topic: str, interval_hours: float = 1.0):
        """Register a crawler agent for a specific topic."""
        agent = CrawlerAgent(
            topic=topic,
            strategy_repo=self.strategy_repo,
            kpi_repo=self.kpi_repo,
            search_tools=self.search_tools,
            indexer=self.indexer
        )
        self.agents[topic] = agent
        
        self.scheduler.add_job(
            agent.run,
            trigger=IntervalTrigger(hours=interval_hours),
            id=f"crawl_{topic}",
            name=f"Crawl agent for {topic}",
            replace_existing=True
        )
        logger.info("agent_scheduled", topic=topic, interval_hours=interval_hours)

    async def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("search_scheduler_started")

    async def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("search_scheduler_stopped")
