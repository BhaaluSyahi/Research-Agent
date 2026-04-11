"""
Matching Engine — FastAPI application entry point with dependency initialization and lifespan management.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from supabase import create_client as create_supabase_client
from openai import AsyncOpenAI
from tavily import AsyncTavilyClient
import boto3

from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.health import router as health_router

# Repositories
from app.repositories.supabase_formal import SupabaseFormalRepository
from app.repositories.supabase_informal import SupabaseInformalRepository
from app.repositories.supabase_strategy import SupabaseStrategyRepository
from app.repositories.supabase_kpi import SupabaseKpiRepository
from app.repositories.sqs import SQSRepository
from app.repositories.sns import SNSRepository
from app.repositories.openai_client import OpenAIClientRepository
from app.repositories.tavily import TavilyRepository

# MCP / Tools
from app.mcp.server import MCPServer
from app.mcp.tools.db_tools import DBTools
from app.mcp.tools.search_tools import SearchTools
from app.mcp.tools.embedding_tools import EmbeddingTools

# Logic
from app.submodules.receiver.poller import RequestPoller
from app.submodules.search.scheduler import SearchScheduler
from app.submodules.search.indexer import ContentIndexer
from app.submodules.matching.pipeline import MatchingPipeline
from app.submodules.matching.formal_matcher import FormalMatcher
from app.submodules.matching.informal_matcher import InformalMatcher
from app.submodules.matching.merger import ResultMerger
from app.submodules.search.on_demand import OnDemandEnricher

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize all components and start background tasks."""
    configure_logging()
    logger.info("matching_engine_starting", phase="startup")

    # 1. Initialize External Clients
    supabase = create_supabase_client(settings.supabase_url, settings.supabase_key)
    openai = AsyncOpenAI(api_key=settings.openai_api_key)
    tavily = AsyncTavilyClient(api_key=settings.tavily_api_key)
    
    sqs_client = boto3.client(
        "sqs",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key
    )
    
    logger.info("external_clients_initialized")

    # 2. Initialize Repositories
    formal_repo = SupabaseFormalRepository(supabase)
    informal_repo = SupabaseInformalRepository(supabase)
    strategy_repo = SupabaseStrategyRepository(supabase)
    kpi_repo = SupabaseKpiRepository(supabase)
    sqs_repo = SQSRepository(sqs_client)
    openai_repo = OpenAIClientRepository(
        openai, 
        embedding_model="text-embedding-3-small", 
        chat_model="gpt-4o"
    )
    tavily_repo = TavilyRepository(tavily)

    # 3. Initialize Shared Tools
    db_tools = DBTools(formal_repo, informal_repo)
    search_tools = SearchTools(tavily_repo, openai_repo)
    embedding_tools = EmbeddingTools(openai_repo)
    indexer = ContentIndexer(informal_repo, embedding_tools)
    
    # 4. Initialize Core Logic
    from app.submodules.search.intent_lock import IntentLock
    intent_lock = IntentLock(sqs_repo)
    
    formal_matcher = FormalMatcher(formal_repo)
    informal_matcher = InformalMatcher(informal_repo, openai_repo)
    on_demand_enricher = OnDemandEnricher(search_tools, indexer, intent_lock)
    merger = ResultMerger()
    
    pipeline = MatchingPipeline(
        formal_matcher=formal_matcher,
        informal_matcher=informal_matcher,
        on_demand_enricher=on_demand_enricher,
        merger=merger,
        db_tools=db_tools,
        kpi_repo=kpi_repo
    )

    # 5. Start Background Tasks
    # Poller
    poller = RequestPoller(sqs_repo, formal_repo, settings.sqs_request_queue_url)
    app.state.poller_task = asyncio.create_task(poller.start())
    
    # Scheduler
    scheduler = SearchScheduler(strategy_repo, kpi_repo, search_tools, indexer)
    # Register default topics
    scheduler.register_topic("floods", interval_hours=1.0)
    scheduler.register_topic("healthcare", interval_hours=2.0)
    await scheduler.start()
    app.state.scheduler = scheduler

    logger.info("background_tasks_started")

    yield

    # Shutdown
    logger.info("matching_engine_stopping", phase="shutdown")
    await poller.stop()
    await scheduler.stop()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Matching Engine",
        lifespan=lifespan,
    )
    application.include_router(health_router)
    return application


app = create_app()
