from fastapi import Request
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str

class StatusResponse(BaseModel):
    status: str
    scheduler: dict
    poller: dict
    hit_rate: float


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Basic liveness probe."""
    return HealthResponse(status="ok")


@router.get("/status", response_model=StatusResponse)
async def status(request: Request) -> StatusResponse:
    """Operational status — aggregated from background tasks."""
    scheduler = request.app.state.scheduler
    poller = request.app.state.poller
    kpi_repo = request.app.state.kpi_repo
    
    return StatusResponse(
        status="ok",
        scheduler=scheduler.get_status(),
        poller=poller.get_status(),
        hit_rate=await kpi_repo.get_hit_rate()
    )
