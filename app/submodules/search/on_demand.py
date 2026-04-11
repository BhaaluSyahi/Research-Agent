"""
On-demand enrichment logic — builds queries, searches Tavily, indexes results, and retries RAG.
Triggered when the initial RAG results are insufficient.
"""

from datetime import datetime
from app.core.logging import get_logger
from app.mcp.tools.search_tools import SearchTools
from app.submodules.search.indexer import ContentIndexer
from app.submodules.search.intent_lock import IntentLock, IntentLockError
from app.submodules.matching.schemas import RequestRecord

logger = get_logger(__name__)


class OnDemandEnricher:
    """
    Fast-path crawler that runs synchronously as part of the matching pipeline.
    """

    def __init__(
        self, 
        search_tools: SearchTools,
        indexer: ContentIndexer,
        intent_lock: IntentLock
    ):
        self.search_tools = search_tools
        self.indexer = indexer
        self.intent_lock = intent_lock

    async def enrich_and_retry(
        self, 
        request: RequestRecord,
        topic: str
    ) -> int:
        """
        1. Classify request for better topic/geo context
        2. Attempt to acquire intent lock
        3. Build optimized search queries
        4. Run Tavily search
        5. Index results via ContentIndexer
        6. Return count of new articles added
        """
        logger.info("on_demand_enrichment_started", request_id=str(request.id), topic=topic)
        
        # 1. Classify for better search accuracy
        try:
            classification = await self.search_tools.classify_request(
                title=request.title, 
                description=request.description
            )
            geo = classification.get("geo_tags", ["India"])[0]
            year = datetime.now().year
        except Exception as e:
            logger.warning("classification_failed_falling_back", error=str(e))
            geo = "India"
            year = datetime.now().year

        # 2. Intent Lock (topic#geo#year)
        message_group_id = f"{topic}#{geo}#{year}"
        
        async with self.intent_lock.acquire(message_group_id) as locked:
            if not locked:
                logger.info("intent_already_claimed_skipping_search", group_id=message_group_id)
                return 0

            # 3. Optimized query generation
            query = f"NGO volunteer rescue help {topic} in {geo} {request.title}"
            
            from app.config import settings
            llm_calls = 0
            tavily_calls = 0
            new_count = 0
            
            # 4. Search
            if tavily_calls >= settings.max_tavily_calls_per_request:
                return 0
                
            try:
                results = await self.search_tools.web_search(query=query, max_results=5)
                tavily_calls += 1
            except Exception as e:
                logger.error("web_search_failed", error=str(e))
                return 0
            
            # 5. Index
            for res in results:
                if new_count >= settings.max_llm_calls_per_request: # Summarization limit
                    break
                    
                try:
                    created = await self.indexer.index(
                        raw_text=res.get("content", ""),
                        source_url=res["url"],
                        topic=topic,
                        indexed_by="on_demand_enricher"
                    )
                    llm_calls += 1
                    if created:
                        new_count += 1
                except Exception as e:
                    logger.warning("article_indexing_failed", url=res.get("url"), error=str(e))
                    
            logger.info(
                "on_demand_enrichment_complete", 
                request_id=str(request.id), 
                new_articles=new_count
            )
            return new_count
