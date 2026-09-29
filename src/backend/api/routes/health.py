"""Health check and diagnostic API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.backend.db.session import get_db
from src.backend.schemas import HealthResponse
from src.backend.services.health_service import HealthService

router = APIRouter(tags=["Health & System Status"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health and subsystem diagnostics",
    description="Returns database connectivity status, table record counts, and ML subsystem operational state.",
)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Check application and database health."""
    return HealthService.get_health(db)
