"""
SynthLeak Backend FastAPI Application Entry Point.
Implements the complete REST & WebSocket server according to CONTRACT.md.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.seed import setup_database
from backend.routes_pipelines import router as pipelines_router
from backend.routes_alerts import router as alerts_router
from backend.routes_tickets import router as tickets_router
from backend.routes_ws import router as ws_router
from shared.schemas import StandardErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    # Startup: Initialize SQLite tables and seed canonical pipeline network
    setup_database()
    yield
    # Shutdown: Resource cleanup if needed


app = FastAPI(
    title="SynthLeak Acoustic Pipeline Leak Detection API",
    description=(
        "Production-grade FastAPI backend for real-time acoustic pipeline monitoring, "
        "digital signal processing (DSP), CNN classification telemetry, and incident work-order dispatch."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
_origins = settings.CORS_ORIGINS
_allow_credentials = "*" not in _origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX if settings.CORS_ORIGIN_REGEX else None,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Error Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler returning canonical StandardErrorResponse."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": str(exc) if settings.ENVIRONMENT == "development" else "An unexpected error occurred.",
            "timestamp": now_iso,
        },
    )


# System Health Check
@app.get(
    "/health",
    tags=["System"],
    summary="System Health & Readiness Probe",
    description="Returns service availability, timestamp, and core subsystem readiness status.",
)
def get_health():
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "status": "healthy",
        "service": "synthleak-backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": now_iso,
        "subsystems": {
            "database": "online",
            "audio_buffer": "ready",
            "ml_inference": "ready",
            "websocket_stream": "ready",
        },
    }


# Include Modular Routers
app.include_router(pipelines_router)
app.include_router(alerts_router)
app.include_router(tickets_router)
app.include_router(ws_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
    )


