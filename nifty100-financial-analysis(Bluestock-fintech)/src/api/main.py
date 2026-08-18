"""FastAPI application for Bluestock Fintech API."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Application version
APP_VERSION = "0.1.0"

# Application startup time for uptime calculation
START_TIME = time.time()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bluestock.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Bluestock Fintech API v%s", APP_VERSION)
    yield
    logger.info("Shutting down Bluestock Fintech API")


app = FastAPI(
    title="Bluestock Fintech API",
    description="Financial analytics API for Nifty 100 companies",
    version=APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware - allow all origins for internal use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP method, request path, and response time."""
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(
            "%s %s failed after %.4fs: %s",
            request.method,
            request.url.path,
            elapsed,
            str(e),
        )
        raise
    else:
        elapsed = time.perf_counter() - start_time
        logger.info(
            "%s %s completed in %.4fs",
            request.method,
            request.url.path,
            elapsed,
        )
    return response


# Import and register routers
from .routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(screener.router, prefix="/api/v1", tags=["screener"])
app.include_router(sectors.router, prefix="/api/v1", tags=["sectors"])
app.include_router(peers.router, prefix="/api/v1", tags=["peers"])
app.include_router(valuation.router, prefix="/api/v1", tags=["valuation"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
