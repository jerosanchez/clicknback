from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import engine

router = APIRouter(tags=["health"])


@router.get("/health/live")
def liveness() -> dict[str, str]:
    """Liveness probe: confirms the process is running. No I/O."""
    return {"status": "alive"}


@router.get("/health/ready")
def readiness() -> JSONResponse:
    """Readiness probe: confirms the DB is reachable via a lightweight SELECT 1."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "ready"})

    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable"},
        )
