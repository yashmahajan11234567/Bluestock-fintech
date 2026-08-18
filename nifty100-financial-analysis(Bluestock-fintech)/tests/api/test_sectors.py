"""
Tests for the Day 40 Sector API endpoints.

Uses real SQLite-backed data from the live database.  No data is modified.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.utils import db

client = TestClient(app)

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"


def _json_serializable(obj):
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# 1. GET /sectors → 200
# ---------------------------------------------------------------------------


def test_list_sectors_returns_200():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 2. exactly 10 sectors
# ---------------------------------------------------------------------------


def test_list_sectors_has_10():
    response = client.get("/api/v1/sectors")
    data = response.json()
    assert "sectors" in data
    assert len(data["sectors"]) == 10


# ---------------------------------------------------------------------------
# 3. aggregate fields present
# ---------------------------------------------------------------------------


def test_sectors_aggregate_fields_present():
    response = client.get("/api/v1/sectors")
    data = response.json()
    expected_fields = {
        "sector",
        "company_count",
        "avg_roe_pct",
        "avg_roce_pct",
        "avg_debt_to_equity",
        "avg_net_profit_margin_pct",
        "avg_pe_ratio",
        "total_market_cap_cr",
    }
    for entry in data["sectors"]:
        for field in expected_fields:
            assert field in entry, f"Missing field '{field}' in sector aggregate"


# ---------------------------------------------------------------------------
# 4. valid sector → 200
# ---------------------------------------------------------------------------


def test_valid_sector_returns_200():
    response = client.get("/api/v1/sectors/Financials")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 5. sector aggregate matches get_sector_aggregates()
# ---------------------------------------------------------------------------


def test_sector_aggregate_matches_db():
    df = db.get_sector_aggregates()
    for _, row in df.iterrows():
        sector_name = row["sector"]
        response = client.get(f"/api/v1/sectors/{sector_name}")
        assert response.status_code == 200, f"Failed for sector: {sector_name}"
        data = response.json()
        assert data["sector"] == sector_name
        assert data["company_count"] == int(row["company_count"])
        # Check a few aggregate values match (rounded)
        assert abs(float(data["avg_roe_pct"]) - float(row["avg_roe_pct"])) < 0.01


# ---------------------------------------------------------------------------
# 6. unknown sector → 404
# ---------------------------------------------------------------------------


def test_unknown_sector_returns_404():
    response = client.get("/api/v1/sectors/NonexistentSector123")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 7. valid sector companies → 200
# ---------------------------------------------------------------------------


def test_valid_sector_companies_200():
    response = client.get("/api/v1/sectors/Financials/companies")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 8. company count matches returned list
# ---------------------------------------------------------------------------


def test_sector_companies_count_matches():
    response = client.get("/api/v1/sectors/Financials/companies")
    data = response.json()
    assert data["count"] == len(data["companies"])


# ---------------------------------------------------------------------------
# 9. returned companies actually belong to requested broad_sector
# ---------------------------------------------------------------------------


def test_sector_companies_belong_to_sector():
    response = client.get("/api/v1/sectors/Financials/companies")
    data = response.json()
    assert data["sector"] == "Financials"
    # Cross-check each returned company is actually in Financials via db
    db_rows = db.get_sectors()
    financials_companies = {
        r["company_id"] for r in db_rows if r.get("broad_sector") == "Financials"
    }
    for company in data["companies"]:
        assert (
            company["company_id"] in financials_companies
        ), f"Company {company['company_id']} is not in Financials sector"


# ---------------------------------------------------------------------------
# 10. unknown sector companies → 404
# ---------------------------------------------------------------------------


def test_unknown_sector_companies_404():
    response = client.get("/api/v1/sectors/NonexistentSector123/companies")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 11. JSON serializable
# ---------------------------------------------------------------------------


def test_sectors_json_serializable():
    response = client.get("/api/v1/sectors")
    assert _json_serializable(response.json())

    response = client.get("/api/v1/sectors/Financials")
    assert _json_serializable(response.json())

    response = client.get("/api/v1/sectors/Financials/companies")
    assert _json_serializable(response.json())


# ---------------------------------------------------------------------------
# Additional: company fields in sector companies list
# ---------------------------------------------------------------------------


def test_sector_companies_fields_present():
    response = client.get("/api/v1/sectors/Financials/companies")
    data = response.json()
    expected_fields = {"company_id", "company_name", "sub_sector"}
    for entry in data["companies"]:
        for field in expected_fields:
            assert field in entry, f"Missing field '{field}' in sector company entry"


# ---------------------------------------------------------------------------
# Additional: case sensitivity is preserved
# ---------------------------------------------------------------------------


def test_sector_case_sensitivity():
    # 'financials' (lowercase) should NOT match 'Financials'
    response = client.get("/api/v1/sectors/financials")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Day 42 — extended tests
# ---------------------------------------------------------------------------


def test_sector_count_day42():
    """Day 42: Verify sector count."""
    response = client.get("/api/v1/sectors")
    data = response.json()
    actual_count = len(data["sectors"])

    # The live DB has 10 broad sectors — do NOT fabricate an 11th.
    assert actual_count == 10, (
        f"Expected 10 sectors per live DB, got {actual_count}. "
        f"Day 42 roadmap expected 11 — this is a spec/data mismatch."
    )


def test_sector_it_not_found_returns_404():
    """Day 42: GET /api/v1/sectors/IT returns 404."""
    response = client.get("/api/v1/sectors/IT")
    assert response.status_code == 404
    data = response.json()
    assert "IT" in data["detail"]


def test_sector_information_technology_returns_200():
    """Day 42: Verify the correct sector name for IT returns 200."""
    response = client.get("/api/v1/sectors/Information%20Technology")
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] == "Information Technology"


def test_sector_it_companies_not_found_returns_404():
    """Day 42: GET /api/v1/sectors/IT/companies returns 404."""
    response = client.get("/api/v1/sectors/IT/companies")
    assert response.status_code == 404


def test_sector_information_technology_companies_belong_to_sector():
    """Day 42: Verify every company returned by /sectors/Information%20Technology/companies"""
    response = client.get("/api/v1/sectors/Information%20Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] == "Information Technology"

    db_rows = db.get_sectors()
    it_companies = {
        r["company_id"] for r in db_rows if r.get("broad_sector") == "Information Technology"
    }
    for company in data["companies"]:
        assert (
            company["company_id"] in it_companies
        ), f"Company {company['company_id']} is not in Information Technology sector"


def test_sectors_db_unchanged_after_calls():
    """Day 42: Sector endpoints must be read-only."""
    before_counts: dict[str, int] = {}
    import sqlite3

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    for t in ["companies", "sectors"]:
        row = conn.execute(f'SELECT COUNT(*) AS c FROM "{t}"').fetchone()
        before_counts[t] = row["c"]
    conn.close()

    client.get("/api/v1/sectors")
    client.get("/api/v1/sectors/Information%20Technology")
    client.get("/api/v1/sectors/Information%20Technology/companies")
    client.get("/api/v1/sectors/IT")  # Should 404, no mutation
    client.get("/api/v1/sectors/nonexistent")

    after_counts: dict[str, int] = {}
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    for t in ["companies", "sectors"]:
        row = conn.execute(f'SELECT COUNT(*) AS c FROM "{t}"').fetchone()
        after_counts[t] = row["c"]
    conn.close()

    assert (
        before_counts == after_counts
    ), f"DB counts changed:\n  Before: {before_counts}\n  After:  {after_counts}"
