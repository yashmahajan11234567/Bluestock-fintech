"""Tests for the health endpoint.

Day 38 — original health endpoint tests.
Day 42 — extended with database fingerprint verification and DB safety checks.
"""

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"

# Canonical list of all 12 live database tables
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


def _db_fingerprint() -> dict[str, int]:
    """Capture read-only row counts for all 12 tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    counts = {}
    for t in ALL_TABLES:
        row = conn.execute(f'SELECT COUNT(*) AS c FROM "{t}"').fetchone()
        counts[t] = row["c"]
    conn.close()
    return counts


# ---------------------------------------------------------------------------
# Day 38 — original tests (preserved)
# ---------------------------------------------------------------------------


def test_app_imports():
    """Test that the FastAPI app can be imported without error."""
    from src.api.main import app

    assert app is not None


def test_health_endpoint():
    """Test GET /api/v1/health endpoint."""
    from src.api.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Check status
    assert data["status"] == "ok"

    # Check db_row_counts exists
    assert "db_row_counts" in data
    db_row_counts = data["db_row_counts"]

    for table in ALL_TABLES:
        assert table in db_row_counts, f"Missing table: {table}"
        assert isinstance(db_row_counts[table], int), f"Count for {table} is not an integer"
        assert db_row_counts[table] >= 0, f"Count for {table} is negative"

    # Verify companies count is 92
    assert (
        db_row_counts["companies"] == 92
    ), f"Expected 92 companies, got {db_row_counts['companies']}"

    # Check uptime_seconds exists and is >= 0
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0

    # Check version exists and is non-empty
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0
    assert data["version"] == "0.1.0"


def test_health_response_content_type():
    """Test that health endpoint returns JSON content type."""
    from src.api.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_all_routers_registered():
    """Test that all expected routers are registered."""
    from src.api.main import app

    routes = [route.path for route in app.routes]

    expected_prefixes = [
        "/api/v1/companies",
        "/api/v1/screener",
        "/api/v1/sectors",
        "/api/v1/peers",
        "/api/v1/valuation",
        "/api/v1/portfolio",
        "/api/v1/documents",
        "/api/v1/health",
    ]

    for prefix in expected_prefixes:
        matching = [r for r in routes if r.startswith(prefix)]
        assert matching, f"No routes found for prefix: {prefix}"


# ---------------------------------------------------------------------------
# Day 42 — additional tests (extending existing coverage)
# ---------------------------------------------------------------------------


def test_health_db_row_counts_match_fingerprint():
    """Day 42: Health endpoint db_row_counts must match the live DB fingerprint."""
    from src.api.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    api_counts = response.json()["db_row_counts"]
    db_counts = _db_fingerprint()

    assert api_counts == db_counts, (
        f"Health endpoint counts differ from DB:\n" f"  API: {api_counts}\n" f"  DB:  {db_counts}"
    )


def test_health_db_unchanged_after_calls():
    """Day 42: Database row counts must be unchanged after health API calls."""
    from src.api.main import app

    before = _db_fingerprint()

    client = TestClient(app)
    # Make several health calls plus other read-only endpoints
    for _ in range(5):
        client.get("/api/v1/health")
    client.get("/api/v1/companies")
    client.get("/api/v1/screener")
    client.get("/api/v1/sectors")

    after = _db_fingerprint()

    assert before == after, (
        f"Database row counts changed during health tests:\n"
        f"  Before: {before}\n"
        f"  After:  {after}"
    )
