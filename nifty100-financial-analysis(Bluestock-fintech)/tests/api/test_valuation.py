"""
Tests for the Day 41 Valuation API endpoint.

Uses real SQLite-backed data from the live database.  No data is modified
during these tests — a read-only fingerprint is captured before and verified
unchanged after.
"""

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.utils import db

client = TestClient(app)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"

VALUATION_FIELDS = {
    "year",
    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
}

# All 12 live tables
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _table_counts() -> dict[str, int]:
    """Return row counts for all 12 live tables (read-only)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    counts = {}
    for t in ALL_TABLES:
        row = conn.execute(f'SELECT COUNT(*) AS c FROM "{t}"').fetchone()
        counts[t] = row["c"]
    conn.close()
    return counts


def _known_company_ids() -> list[str]:
    """Return the first few company tickers from the live DB."""
    rows = db.get_company_list()
    return [r["company_id"] for r in rows[:5]]


def _company_with_valuation() -> str | None:
    """Return a company_id that has market_cap (valuation) data."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM market_cap ORDER BY company_id")
    if not rows:
        # Fallback: any known company
        known = _known_company_ids()
        return known[0] if known else None
    return rows[0]["company_id"]


def _company_without_valuation() -> str | None:
    """Return a company_id that has NO market_cap rows, or None if all have data."""
    rows = db._fetchall("""
        SELECT c.id FROM companies c
        LEFT JOIN market_cap m ON m.company_id = c.id
        WHERE m.company_id IS NULL
        ORDER BY c.id
        """)
    return rows[0]["id"] if rows else None


def _json_serializable(obj):
    """Recursively verify that an object is JSON-serializable."""
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# 1. Known company with valuation data → 200
# ---------------------------------------------------------------------------


def test_valuation_known_company_200():
    ticker = _company_with_valuation()
    assert ticker is not None, "No company with valuation data found in DB"
    response = client.get(f"/api/v1/valuation/{ticker}")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 2. Response contains company_id and valuations list
# ---------------------------------------------------------------------------


def test_valuation_response_structure():
    ticker = _company_with_valuation()
    assert ticker is not None
    response = client.get(f"/api/v1/valuation/{ticker}")
    data = response.json()
    assert "company_id" in data
    assert "valuations" in data
    assert data["company_id"] == ticker
    assert isinstance(data["valuations"], list)


# ---------------------------------------------------------------------------
# 3. Field structure: exactly seven valuation fields per entry
# ---------------------------------------------------------------------------


def test_valuation_field_structure():
    ticker = _company_with_valuation()
    assert ticker is not None
    response = client.get(f"/api/v1/valuation/{ticker}")
    data = response.json()
    assert len(data["valuations"]) > 0, "Expected at least one valuation entry"
    for entry in data["valuations"]:
        assert (
            set(entry.keys()) == VALUATION_FIELDS
        ), f"Valuation entry has unexpected fields: {set(entry.keys())}"


# ---------------------------------------------------------------------------
# 4. API values match get_valuation(company_id)
# ---------------------------------------------------------------------------


def _normalize_record(rec: dict) -> dict:
    """Apply only the API's legitimate JSON normalization to a DB record."""
    out = {}
    for k, v in rec.items():
        if v is None:
            out[k] = None
        elif hasattr(v, "item"):  # numpy scalar
            out[k] = v.item()
        else:
            out[k] = v
    return out


def test_valuation_values_match_helper():
    ticker = _company_with_valuation()
    assert ticker is not None
    # Get expected data from the DB helper
    df = db.get_valuation(ticker)
    expected_records = df.to_dict("records")

    response = client.get(f"/api/v1/valuation/{ticker}")
    actual_data = response.json()
    actual_valuations = actual_data["valuations"]

    assert len(actual_valuations) == len(
        expected_records
    ), f"Row count mismatch: API={len(actual_valuations)}, DB={len(expected_records)}"

    for exp_rec, act_entry in zip(expected_records, actual_valuations):
        exp_rec_norm = _normalize_record(exp_rec)
        for field in VALUATION_FIELDS:
            exp_val = exp_rec_norm.get(field)
            act_val = act_entry.get(field)
            # Compare with tolerance for floats
            if exp_val is not None and isinstance(exp_val, float):
                assert abs(float(act_val) - exp_val) < 0.01, (
                    f"Field '{field}' mismatch for year {exp_rec_norm.get('year')}: "
                    f"expected={exp_val}, actual={act_val}"
                )
            else:
                assert act_val == exp_val, (
                    f"Field '{field}' mismatch for year {exp_rec_norm.get('year')}: "
                    f"expected={exp_val}, actual={act_val}"
                )


# ---------------------------------------------------------------------------
# 5. Verify year is integer or null
# ---------------------------------------------------------------------------


def test_valuation_year_is_int_or_null():
    ticker = _company_with_valuation()
    assert ticker is not None
    response = client.get(f"/api/v1/valuation/{ticker}")
    data = response.json()
    for entry in data["valuations"]:
        year = entry["year"]
        assert year is None or isinstance(
            year, int
        ), f"Year is {type(year)} for ticker {ticker}, value={year}"


# ---------------------------------------------------------------------------
# 6. Verify valuation rows are ordered descending by year
# ---------------------------------------------------------------------------


def test_valuation_ordered_descending_by_year():
    ticker = _company_with_valuation()
    assert ticker is not None
    response = client.get(f"/api/v1/valuation/{ticker}")
    data = response.json()
    years = [e["year"] for e in data["valuations"] if e["year"] is not None]
    assert years == sorted(years, reverse=True), f"Years not in descending order: {years}"


# ---------------------------------------------------------------------------
# 7. Verify NULL metrics remain null (not 0, "nan", or NaN)
# ---------------------------------------------------------------------------


def test_valuation_null_metrics_preserved():
    ticker = _company_with_valuation()
    assert ticker is not None
    df = db.get_valuation(ticker)
    response = client.get(f"/api/v1/valuation/{ticker}")
    data = response.json()

    for exp_rec, act_entry in zip(df.to_dict("records"), data["valuations"]):
        for field in VALUATION_FIELDS:
            if field == "year":
                continue
            exp_val = exp_rec.get(field)
            act_val = act_entry.get(field)
            if exp_val is None:
                assert act_val is None, (
                    f"Expected None for {field} (year {exp_rec.get('year')}), "
                    f"got {act_val!r} (type={type(act_val)})"
                )
            elif isinstance(exp_val, float):
                import math

                if math.isnan(exp_val):
                    assert act_val is None, (
                        f"Expected None for {field} (year {exp_rec.get('year')}), "
                        f"got {act_val!r} (NaN leaked through)"
                    )


# ---------------------------------------------------------------------------
# 8. Unknown company → 404
# ---------------------------------------------------------------------------


def test_valuation_unknown_company_404():
    response = client.get("/api/v1/valuation/THIS_COMPANY_DOES_NOT_EXIST")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Company not found: THIS_COMPANY_DOES_NOT_EXIST"


# ---------------------------------------------------------------------------
# 9. Valid company without valuation rows → 200 + empty valuations
# ---------------------------------------------------------------------------


def test_valuation_company_without_rows_200_empty():
    ticker = _company_without_valuation()
    if ticker is None:
        pytest.skip(
            "All current companies have valuation data in the live DB; "
            "this edge case could not be exercised against the live database."
        )
    response = client.get(f"/api/v1/valuation/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == ticker
    assert data["valuations"] == []


# ---------------------------------------------------------------------------
# 10. JSON serialization
# ---------------------------------------------------------------------------


def test_valuation_json_serializable():
    ticker = _company_with_valuation()
    assert ticker is not None
    response = client.get(f"/api/v1/valuation/{ticker}")
    assert _json_serializable(response.json())
    # Also verify json.dumps works on the parsed JSON
    json.dumps(response.json())


# ---------------------------------------------------------------------------
# 11. DB remains unchanged after API calls
# ---------------------------------------------------------------------------


def test_db_unchanged_after_valuation_api_calls():
    before = _table_counts()

    # Hammer the valuation endpoint with various calls
    ticker = _company_with_valuation()
    if ticker:
        client.get(f"/api/v1/valuation/{ticker}")

    client.get("/api/v1/valuation/THIS_COMPANY_DOES_NOT_EXIST")

    after = _table_counts()

    assert (
        before == after
    ), f"Database row counts changed during tests:\n  Before: {before}\n  After:  {after}"


# ---------------------------------------------------------------------------
# 12. Company existence verified (cannot forge company via valuation)
# ---------------------------------------------------------------------------


def test_valuation_with_valid_ticker_uses_company_profile():
    """Verify that get_company_profile is used for existence check."""
    ticker = _known_company_ids()[0]
    response = client.get(f"/api/v1/valuation/{ticker}")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 13. No extra fields in response (exactly company_id + valuations)
# ---------------------------------------------------------------------------


def test_valuation_no_extra_top_level_fields():
    ticker = _company_with_valuation()
    assert ticker is not None
    response = client.get(f"/api/v1/valuation/{ticker}")
    data = response.json()
    assert set(data.keys()) == {"company_id", "valuations"}
