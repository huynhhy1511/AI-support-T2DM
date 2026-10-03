from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthCheckResponse
from app.services.database import check_database_connection

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health status of the backend API service and database connectivity",
)
def health_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    is_connected = check_database_connection(db)
    database_status = "connected" if is_connected else "disconnected"

    return HealthCheckResponse(
        status="ok",
        service="AI-support-T2DM",
        database=database_status,
    )
