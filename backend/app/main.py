import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings

# Setup standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager handling application startup and shutdown events."""
    logger.info(
        "Starting application '%s' in environment '%s'...",
        settings.app_name,
        settings.app_env,
    )
    yield
    logger.info("Application '%s' is shutting down...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend API for AI-support-T2DM - Type 2 Diabetes Self-Management Assistant",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions with logging."""
    logger.warning(
        "HTTP %s on %s %s: %s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request schema validation errors."""
    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected server exceptions without swallowing or leaking sensitive traces."""
    logger.exception(
        "Unhandled exception processing %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get(
    "/",
    tags=["root"],
    summary="Root Info",
    description="Root endpoint providing basic service status and documentation link",
)
def root() -> dict[str, Any]:
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
    }


# Mount API v1 router
app.include_router(api_router, prefix="/api/v1")
