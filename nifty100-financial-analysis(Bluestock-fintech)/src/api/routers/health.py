"""Health check router."""

import sqlite3
import time

from fastapi import APIRouter

from ..main import APP_VERSION, START_TIME

router = APIRouter()

# Explicit list of the 12 verified live tables (10 documented + 2 additional)
LIVE_TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "financial_ratios",
    "market_cap",
    "peer_groups",
]

DB_PATH = "db/nifty100.db"


def get_db_connection():
    """Get a SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    db_row_counts = {}

    try:
        with get_db_connection() as conn:
            for table in LIVE_TABLES:
                cursor = conn.execute(f'SELECT COUNT(*) FROM "{table}"')
                count = cursor.fetchone()[0]
                db_row_counts[table] = count
    except Exception as e:
        # Return error state but still provide partial data if available
        db_row_counts = {"error": str(e)}

    uptime_seconds = round(time.time() - START_TIME, 2)

    return {
        "status": "ok",
        "db_row_counts": db_row_counts,
        "uptime_seconds": uptime_seconds,
        "version": APP_VERSION,
    }
