"""
Internal health and status endpoints.
These are the only HTTP endpoints exposed — this service does not serve the frontend or core backend.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class StatusResponse(BaseModel):
    status: str
    scheduler_running: bool
    poller_running: bool
    # TODO Phase 10: extend with last_run_times, queue_depths, hit_rate


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Basic liveness probe."""
    return HealthResponse(status="ok")


@router.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    """Operational status — extended in Phase 10."""
    return StatusResponse(
        status="ok",
        scheduler_running=False,  # TODO Phase 10
        poller_running=False,     # TODO Phase 10
    )
