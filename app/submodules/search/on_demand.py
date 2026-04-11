"""
On-demand enrichment logic — builds queries, searches Tavily, indexes results, and retries RAG.
Triggered when the initial RAG results are insufficient.
"""

from app.core.logging import get_logger
from app.mcp.tools.search_tools import SearchTools
from app.submodules.search.indexer import ContentIndexer
from app.submodules.matching.schemas import RequestRecord

logger = get_logger(__name__)


class OnDemandEnricher:
    """
    Fast-path crawler that runs synchronously as part of the matching pipeline.
    """

    def __init__(
        self, 
        search_tools: SearchTools,
        indexer: ContentIndexer
    ):
        self.search_tools = search_tools
        self.indexer = indexer

    async def enrich_and_retry(
        self, 
        request: RequestRecord,
        topic: str
    ) -> int:
        """
        1. Generate search queries from request
        2. Run Tavily search
        3. Index top results
        4. Return count of new articles added
        """
        logger.info("on_demand_enrichment_started", request_id=str(request.id), topic=topic)
        
        # 1. Simple query generation (can be improved with LLM)
        query = f"NGO volunteer help {topic} {request.location_text or ''} {request.title}"
        
        # 2. Search
        results = await self.search_tools.web_search(query=query, max_results=5)
        
        new_count = 0
        # 3. Index
        for res in results:
            content = res.get("content", "")
            if len(content) < 200: continue
            
            created = await self.indexer.index(
                raw_text=content,
                source_url=res["url"],
                topic=topic,
                indexed_by="on_demand_enricher"
            )
            if created:
                new_count += 1
                
        logger.info(
            "on_demand_enrichment_complete", 
            request_id=str(request.id), 
            new_articles=new_count
        )
        return new_count
