"""
Pipeline orchestrator — coordinates the flow from formal matching to RAG to on-demand enrichment.
"""

import time
from datetime import datetime
from app.core.logging import get_logger
from app.repositories.supabase_kpi import SupabaseKpiRepository, KpiRecord
from app.submodules.matching.formal_matcher import FormalMatcher
from app.submodules.matching.informal_matcher import InformalMatcher
from app.submodules.matching.sufficiency import is_rag_sufficient
from app.submodules.matching.merger import ResultMerger
from app.submodules.search.on_demand import OnDemandEnricher
from app.mcp.tools.db_tools import DBTools
from app.submodules.matching.schemas import RequestRecord

logger = get_logger(__name__)


class MatchingPipeline:
    def __init__(
        self,
        formal_matcher: FormalMatcher,
        informal_matcher: InformalMatcher,
        on_demand_enricher: OnDemandEnricher,
        merger: ResultMerger,
        db_tools: DBTools,
        kpi_repo: SupabaseKpiRepository
    ):
        self.formal_matcher = formal_matcher
        self.informal_matcher = informal_matcher
        self.on_demand_enricher = on_demand_enricher
        self.merger = merger
        self.db_tools = db_tools
        self.kpi_repo = kpi_repo

    async def run(self, request: RequestRecord) -> None:
        """
        Execute the full matching pipeline.
        """
        start_at = datetime.now()
        start_time = time.perf_counter()
        on_demand_triggered = False
        new_articles = 0
        error = None
        
        try:
            # 1. Formal Matching
            formal_result = await self.formal_matcher.match(request)
            
            # 2. Initial RAG
            # For brevity, classifying topic and geo tags is assumed to be handled or passed.
            # Here we default to broad search.
            informal_matches = await self.informal_matcher.match(request)
            
            # 3. Sufficiency Check
            if not is_rag_sufficient(informal_matches):
                logger.info("rag_insufficient", request_id=str(request.id))
                on_demand_triggered = True
                
                # 4. On-Demand Enrichment
                new_articles = await self.on_demand_enricher.enrich_and_retry(
                    request=request,
                    topic="general" # Dynamic topic extraction can be added here
                )
                
                # 5. Retry RAG with fresh news
                if new_articles > 0:
                    informal_matches = await self.informal_matcher.match(request)

            # 6. Merge
            payload = self.merger.merge(
                request=request,
                formal=formal_result.matches,
                informal=informal_matches,
                on_demand_triggered=on_demand_triggered
            )

            # 7. Persist Recommendations
            await self.db_tools.write_recommendation(
                request_id=str(request.id),
                formal_matches=[m.model_dump(mode="json") for m in payload.formal_matches],
                informal_matches=[m.model_dump(mode="json") for m in payload.informal_matches]
            )

        except Exception as e:
            logger.error("pipeline_failed", request_id=str(request.id), error=str(e))
            error = str(e)
            raise e
        finally:
            # 8. Update KPI
            end_time = time.perf_counter()
            latency = int((end_time - start_time) * 1000)
            
            kpi = KpiRecord(
                request_id=request.id,
                pipeline_started_at=start_at,
                pipeline_completed_at=datetime.now(),
                formal_matches_count=len(formal_result.matches) if 'formal_result' in locals() else 0,
                informal_matches_count=len(informal_matches) if 'informal_matches' in locals() else 0,
                on_demand_triggered=on_demand_triggered,
                on_demand_articles_added=new_articles,
                total_latency_ms=latency,
                error_occurred=error is not None,
                error_message=error
            )
            await self.kpi_repo.write_kpi(kpi)
            logger.info("pipeline_finished", request_id=str(request.id), latency=latency)
