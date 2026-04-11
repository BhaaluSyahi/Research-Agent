"""
Matching Engine — FastAPI application entry point.

Responsibilities:
- Initialise structured logging
- Mount routers
- Start/stop background scheduler and SQS poller via lifespan
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.logging import configure_logging, get_logger
from app.api.health import router as health_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: start background tasks on startup, shut down cleanly."""
    configure_logging()
    logger.info("matching_engine_starting", phase="startup")

    # TODO: start SQS poller (Phase 4)
    # TODO: start APScheduler (Phase 9)

    yield

    logger.info("matching_engine_stopping", phase="shutdown")
    # TODO: stop scheduler and poller cleanly


def create_app() -> FastAPI:
    application = FastAPI(
        title="Matching Engine",
        description=(
            "Intelligent microservice that matches help requests with NGOs and volunteers "
            "using formal DB queries and informal RAG-based knowledge retrieval."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(health_router)
    return application


app = create_app()
