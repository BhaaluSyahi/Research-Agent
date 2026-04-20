"""
Matching Engine — FastAPI application entry point with dependency initialization and lifespan management.
"""

import sys
from contextlib import asynccontextmanager
import asyncio
from typing import AsyncIterator

from fastapi import FastAPI
from supabase import create_async_client as create_supabase_client
from google import genai
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
from app.repositories.gemini_client import GeminiClientRepository
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
    
    # 0. Check for dev-mode
    is_dev = settings.dev_mode or "-dev" in sys.argv
    if is_dev:
        logger.info("DEV_MODE_ACTIVE", mode="simulation", source="tests/dev_mode/requests.py")
    else:
        logger.info("matching_engine_starting", phase="startup")

    # 1. Initialize External Clients
    supabase = await create_supabase_client(settings.supabase_url, settings.supabase_key)
    gemini = genai.Client(api_key=settings.gemini_api_key)
    tavily = AsyncTavilyClient(api_key=settings.tavily_api_key)
    
    if not is_dev:
        sqs_client = boto3.client(
            "sqs",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    else:
        sqs_client = None
    
    logger.info("external_clients_initialized")

    # 2. Initialize Repositories
    formal_repo = SupabaseFormalRepository(supabase)
    informal_repo = SupabaseInformalRepository(supabase)
    kpi_repo = SupabaseKpiRepository(supabase)
    app.state.kpi_repo = kpi_repo

    if is_dev:
        from app.repositories.sqs_dev import DevSQSRepository
        from app.repositories.strategy_dev import DevStrategyRepository
        sqs_repo = DevSQSRepository()
        strategy_repo = DevStrategyRepository()
    else:
        sqs_repo = SQSRepository(sqs_client)
        strategy_repo = SupabaseStrategyRepository(supabase)
        
    gemini_repo = GeminiClientRepository(
        gemini,
        embedding_model=settings.gemini_embedding_model,
        chat_model=settings.gemini_chat_model
    )
    tavily_repo = TavilyRepository(tavily)

    # 3. Initialize Shared Tools
    db_tools = DBTools(formal_repo, informal_repo)
    search_tools = SearchTools(tavily_repo, gemini_repo)
    embedding_tools = EmbeddingTools(gemini_repo)
    indexer = ContentIndexer(informal_repo, embedding_tools)
    
    # 4. Initialize Core Logic
    from app.submodules.search.intent_lock import IntentLock
    intent_lock = IntentLock(sqs_repo)
    
    formal_matcher = FormalMatcher(formal_repo)
    informal_matcher = InformalMatcher(informal_repo, gemini_repo)
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

    # 5. Initialize MCP Server and Register Tools
    mcp_server = MCPServer()
    
    # DB Tools
    mcp_server.register("query_formal_organizations", db_tools.query_formal_organizations)
    mcp_server.register("search_informal_knowledge_base", db_tools.search_informal_knowledge_base)
    mcp_server.register("write_recommendation", db_tools.write_recommendation)
    
    # Search Tools
    mcp_server.register("web_search", search_tools.web_search)
    mcp_server.register("classify_request", search_tools.classify_request)
    
    # Embedding Tools
    mcp_server.register("embed_text", embedding_tools.embed_text)
    mcp_server.register("summarize_and_extract", embedding_tools.summarize_and_extract)
    
    app.state.mcp_server = mcp_server

    # 6. Start Background Tasks
    # Poller
    poller = RequestPoller(sqs_repo, formal_repo, settings.sqs_requests_queue_url, pipeline)
    app.state.poller = poller
    app.state.poller_task = asyncio.create_task(poller.start())
    
    # Scheduler
    scheduler = SearchScheduler(strategy_repo, kpi_repo, sqs_repo, search_tools, indexer)
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
