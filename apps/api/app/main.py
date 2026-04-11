from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import get_engine
from app.routers import analyze, auth, billing, candidates, contact, events, outreach, roles, uploads, workspaces

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

settings = get_settings()

# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    Startup:
      - Log configuration summary.
      - (Optional) Run a connectivity check against the database.
      - (Optional) Ensure Azure Blob Storage containers exist.

    Shutdown:
      - Dispose the async SQLAlchemy engine, closing all pooled connections.
    """
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    # Verify database connectivity (non-fatal, with timeout)
    import asyncio
    try:
        from sqlalchemy import text

        async def _db_check():
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_db_check(), timeout=5.0)
        logger.info("Database connection: OK")
    except asyncio.TimeoutError:
        logger.warning("Database connectivity check timed out (5s) — continuing without DB")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database connectivity check failed: %s — continuing anyway", exc)

    yield  # Application runs here

    logger.info("Shutting down — disposing database engine.")
    await get_engine().dispose()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "HireIQ API — hiring decision workspace backend. "
            "Provides resume ingestion, deterministic scoring, semantic search, "
            "and Stripe-gated plan entitlements."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Global exception handlers
    # ------------------------------------------------------------------

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------

    API_PREFIX = "/api/v1"

    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(workspaces.router, prefix=API_PREFIX)
    app.include_router(roles.router, prefix=API_PREFIX)
    app.include_router(candidates.router, prefix=API_PREFIX)
    app.include_router(uploads.router, prefix=API_PREFIX)
    app.include_router(billing.router, prefix=API_PREFIX)
    app.include_router(events.router, prefix=API_PREFIX)
    app.include_router(analyze.router, prefix=API_PREFIX)
    app.include_router(contact.router, prefix=API_PREFIX)
    app.include_router(outreach.router)
    app.include_router(outreach.tracking_router)

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @app.get(
        "/health",
        tags=["ops"],
        summary="Liveness probe",
        response_description="Returns 200 when the API process is alive.",
    )
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    @app.get(
        "/health/ready",
        tags=["ops"],
        summary="Readiness probe — checks database connectivity",
    )
    async def ready() -> dict[str, str]:
        """
        Readiness probe for Kubernetes / Azure Container Apps.

        Returns 200 when the API can successfully reach the database.
        Returns 503 on failure (container will be taken out of rotation).
        """
        from sqlalchemy import text  # local import to keep startup clean

        try:
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception as exc:
            logger.error("Readiness check failed: %s", exc)
            return JSONResponse(  # type: ignore[return-value]
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "detail": str(exc)},
            )

    return app


# ---------------------------------------------------------------------------
# Application instance (used by uvicorn)
# ---------------------------------------------------------------------------

app = create_app()
