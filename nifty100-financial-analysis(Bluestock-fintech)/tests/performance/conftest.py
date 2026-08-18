"""
Conftest for Day 43 performance tests.
Captures a database fingerprint before tests run and verifies it after.
"""

import sqlite3
from pathlib import Path

import pytest

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"

ALL_TABLES = [
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


@pytest.fixture(scope="module")
def db_fingerprint_before():
    """Capture database row counts before performance tests."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    counts = {}
    for t in ALL_TABLES:
        row = conn.execute(f'SELECT COUNT(*) AS c FROM "{t}"').fetchone()
        counts[t] = row["c"]
    conn.close()
    return counts
