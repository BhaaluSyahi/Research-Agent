from abc import ABC, abstractmethod
import asyncio
from datetime import datetime

from app.core.logging import get_logger
from app.config import settings
from app.repositories.supabase_strategy import SupabaseStrategyRepository
from app.repositories.supabase_kpi import SupabaseKpiRepository, CrawlLogRecord
from app.repositories.sqs import SQSRepository
from app.submodules.search.indexer import ContentIndexer
from app.submodules.search.intent_lock import IntentLock
from app.mcp.tools.search_tools import SearchTools

logger = get_logger(__name__)


class BaseSearchAgent(ABC):
    """
    Template for a proactive search agent.
    Lifecycle per run:
      1. Read search_strategy row for this topic
      2. For each search_query:
         a. Acquire SQS intent lock (MessageGroupId = topic#geo#year)
         b. Call Tavily search
         c. For each result: hash → dedup → summarize → embed → upsert (via indexer.py)
         d. Associate entry with topic in entry_topics
      3. Update search_strategy.last_run_at
      4. Write crawl_log
    """

    def __init__(
        self,
        strategy_repo: SupabaseStrategyRepository,
        kpi_repo: SupabaseKpiRepository,
        sqs_repo: SQSRepository,
        search_tools: SearchTools,
        indexer: ContentIndexer
    ):
        self.strategy_repo = strategy_repo
        self.kpi_repo = kpi_repo
        self.sqs_repo = sqs_repo
        self.search_tools = search_tools
        self.indexer = indexer
        self.intent_lock = IntentLock(sqs_repo)

    @property
    @abstractmethod
    def topic(self) -> str:
        """Topic slug matching search_strategy.topic and queue name suffix."""
        ...

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique agent identifier used in logs and crawl_logs.indexed_by."""
        ...

    async def run(self) -> None:
        """Execute one full crawl cycle for this topic."""
        logger.info("agent_run_started", agent=self.agent_name, topic=self.topic)
        start_time = asyncio.get_event_loop().time()
        
        total_found: int = 0
        new_entries: int = 0
        failed_count: int = 0
        skipped_count: int = 0
        
        llm_calls = 0
        tavily_calls = 0
        
        try:
            # 1. Fetch Strategy
            strategy = await self.strategy_repo.get_strategy_for_topic(self.topic)
            if not strategy or not strategy.is_active:
                logger.info("agent_skipped", topic=self.topic, reason="no_active_strategy")
                return

            # 2. Intent Lock (MessageGroupId = topic#geo#year)
            geo = strategy.geo_focus[0] if strategy.geo_focus else "india"
            year = datetime.utcnow().year
            message_group_id = f"{self.topic}#{geo}#{year}"
            
            async with self.intent_lock.acquire(message_group_id) as locked:
                if not locked:
                    logger.info("agent_lock_failed", topic=self.topic, group_id=message_group_id)
                    return

                # 3. Search for each query in strategy
                queries = strategy.search_queries[:settings.max_tavily_calls_per_crawl_run]
                for query_obj in queries:
                    if tavily_calls >= settings.max_tavily_calls_per_crawl_run:
                        logger.warning("agent_tavily_limit_reached", topic=self.topic)
                        break
                        
                    try:
                        results = await self.search_tools.web_search(
                            query=query_obj.query,
                            max_results=settings.crawler_max_articles_per_run
                        )
                        tavily_calls += 1
                        total_found += len(results)
                        
                        # 4. Index
                        for res in results:
                            if new_entries >= settings.max_articles_per_crawl_run:
                                logger.warning("agent_article_limit_reached", topic=self.topic)
                                break
                            if llm_calls >= settings.max_llm_calls_per_crawl_run:
                                logger.warning("agent_llm_limit_reached", topic=self.topic)
                                break
                                
                            content = res.get("content", "")
                            if len(content) < 200: 
                                skipped_count += 1
                                continue
                            
                            try:
                                created = await self.indexer.index(
                                    raw_text=content,
                                    source_url=res["url"],
                                    topic=self.topic,
                                    indexed_by=self.agent_name
                                )
                                llm_calls += 1 
                                
                                if created:
                                    new_entries += 1
                            except Exception as e:
                                logger.error("index_failed", url=res.get("url"), error=str(e))
                                failed_count += 1
                    except Exception as e:
                        logger.error("search_failed", query=query_obj.query, error=str(e))
                        failed_count += 1

            # 3. Update Strategy Metadata
            await self.strategy_repo.update_last_run(
                topic=self.topic,
                articles_found=total_found,
                new_entries=new_entries
            )
            
            # 4. Write Crawl Log
            duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            log = CrawlLogRecord(
                agent_name=self.agent_name,
                run_type="scheduled",
                topic=self.topic,
                tavily_results_count=total_found,
                new_entries_count=new_entries,
                failed_count=failed_count,
                duration_ms=duration_ms
            )
            await self.kpi_repo.write_crawl_log(log)
            
            logger.info(
                "agent_run_complete", 
                agent=self.agent_name, 
                topic=self.topic, 
                new=new_entries, 
                total=total_found,
                duration_ms=duration_ms
            )

        except Exception as e:
            logger.error("agent_run_critical_failure", agent=self.agent_name, topic=self.topic, error=str(e))
            # Even on failure, try to log it
            try:
                duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                log = CrawlLogRecord(
                    agent_name=self.agent_name,
                    run_type="scheduled",
                    topic=self.topic,
                    error=str(e),
                    duration_ms=duration_ms
                )
                await self.kpi_repo.write_crawl_log(log)
            except:
                pass
