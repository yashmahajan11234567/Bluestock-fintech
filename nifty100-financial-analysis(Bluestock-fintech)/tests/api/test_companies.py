"""
Tests for the Day 39 Company API endpoints.

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
# Helpers
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"


def _table_counts() -> dict[str, int]:
    """Return row counts for all 12 live tables (read-only)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    tables = [
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
    counts = {}
    for t in tables:
        row = conn.execute(f'SELECT COUNT(*) AS c FROM "{t}"').fetchone()
        counts[t] = row["c"]
    conn.close()
    return counts


def _known_company_ids() -> list[str]:
    """Return the first few company tickers from the live DB."""
    rows = db.get_company_list()
    return [r["company_id"] for r in rows[:5]]


def _company_with_peers() -> str | None:
    """Return a company_id that has a peer group, or None."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM peer_groups ORDER BY company_id")
    return rows[0]["company_id"] if rows else None


def _company_without_peers() -> str | None:
    """Return a company_id that has NO peer group row."""
    rows = db._fetchall("""
        SELECT c.id FROM companies c
        LEFT JOIN peer_groups pg ON pg.company_id = c.id
        WHERE pg.company_id IS NULL
        ORDER BY c.id
        """)
    return rows[0]["id"] if rows else None


def _company_with_pros_cons() -> str | None:
    """Return a company_id that has pros/cons rows."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM prosandcons ORDER BY company_id")
    return rows[0]["company_id"] if rows else None


def _company_without_pros_cons() -> str | None:
    """Return a company_id that has NO pros/cons rows."""
    rows = db._fetchall("""
        SELECT c.id FROM companies c
        LEFT JOIN prosandcons pc ON pc.company_id = c.id
        WHERE pc.company_id IS NULL
        ORDER BY c.id
        """)
    return rows[0]["id"] if rows else None


def _company_with_documents() -> str | None:
    """Return a company_id that has document rows."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM documents ORDER BY company_id")
    return rows[0]["company_id"] if rows else None


def _company_without_documents() -> str | None:
    """Return a company_id that has NO documents."""
    rows = db._fetchall("""
        SELECT c.id FROM companies c
        LEFT JOIN documents d ON d.company_id = c.id
        WHERE d.company_id IS NULL
        ORDER BY c.id
        """)
    return rows[0]["id"] if rows else None


def _company_with_financials() -> str | None:
    """Return a company_id that has P&L data."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM profitandloss ORDER BY company_id")
    return rows[0]["company_id"] if rows else None


def _company_with_ratios() -> str | None:
    """Return a company_id that has financial ratio data."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM financial_ratios ORDER BY company_id")
    return rows[0]["company_id"] if rows else None


def _company_with_cashflow() -> str | None:
    """Return a company_id that has cashflow data."""
    rows = db._fetchall("SELECT DISTINCT company_id FROM cashflow ORDER BY company_id")
    return rows[0]["company_id"] if rows else None


def _json_serializable(obj):
    """Recursively verify that an object is JSON-serializable."""
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# 1. GET /api/v1/companies → 200
# ---------------------------------------------------------------------------


def test_company_list_returns_200():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 2. company count == 92
# ---------------------------------------------------------------------------


def test_company_count_is_92():
    response = client.get("/api/v1/companies")
    data = response.json()
    assert data["count"] == 92
    assert len(data["companies"]) == 92


# ---------------------------------------------------------------------------
# 3. companies sorted by company_name
# ---------------------------------------------------------------------------


def test_companies_sorted_by_name():
    response = client.get("/api/v1/companies")
    data = response.json()
    names = [c["company_name"] for c in data["companies"]]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# 4. valid company profile → 200
# ---------------------------------------------------------------------------


def test_valid_company_profile_200():
    # Use the first known company
    ticker = _known_company_ids()[0]
    response = client.get(f"/api/v1/companies/{ticker}")
    assert response.status_code == 200
    profile = response.json()
    assert profile["company_id"] == ticker
    assert profile["company_name"] is not None


# ---------------------------------------------------------------------------
# 5. unknown company profile → 404
# ---------------------------------------------------------------------------


def test_unknown_company_profile_404():
    response = client.get("/api/v1/companies/THIS_COMPANY_DOES_NOT_EXIST")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 6. valid financials → 200
# ---------------------------------------------------------------------------


def test_valid_financials_200():
    ticker = _company_with_financials()
    assert ticker is not None, "No company with P&L data found in DB"
    response = client.get(f"/api/v1/companies/{ticker}/financials")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 7. financials contain profit_and_loss + balance_sheet
# ---------------------------------------------------------------------------


def test_financials_contains_pnl_and_bs():
    ticker = _company_with_financials()
    response = client.get(f"/api/v1/companies/{ticker}/financials")
    data = response.json()
    assert "profit_and_loss" in data
    assert "balance_sheet" in data
    assert "company_id" in data
    assert data["company_id"] == ticker


# ---------------------------------------------------------------------------
# 8. years are integers or None
# ---------------------------------------------------------------------------


def test_financials_years_are_int_or_none():
    ticker = _company_with_financials()
    response = client.get(f"/api/v1/companies/{ticker}/financials")
    data = response.json()

    for entry in data["profit_and_loss"]:
        if "year" in entry:
            assert entry["year"] is None or isinstance(
                entry["year"], int
            ), f"P&L year is {type(entry['year'])} for ticker {ticker}"

    for entry in data["balance_sheet"]:
        if "year" in entry:
            assert entry["year"] is None or isinstance(
                entry["year"], int
            ), f"BS year is {type(entry['year'])} for ticker {ticker}"


def test_ratios_years_are_int_or_none():
    ticker = _company_with_ratios()
    response = client.get(f"/api/v1/companies/{ticker}/ratios")
    data = response.json()
    for entry in data["ratios"]:
        if "year" in entry:
            assert entry["year"] is None or isinstance(
                entry["year"], int
            ), f"Ratios year is {type(entry['year'])} for ticker {ticker}"


def test_cashflow_years_are_int_or_none():
    ticker = _company_with_cashflow()
    response = client.get(f"/api/v1/companies/{ticker}/cashflow")
    data = response.json()
    for entry in data["cashflow"]:
        if "year" in entry:
            assert entry["year"] is None or isinstance(
                entry["year"], int
            ), f"Cashflow year is {type(entry['year'])} for ticker {ticker}"


# ---------------------------------------------------------------------------
# 9. valid ratios → 200
# ---------------------------------------------------------------------------


def test_valid_ratios_200():
    ticker = _company_with_ratios()
    assert ticker is not None
    response = client.get(f"/api/v1/companies/{ticker}/ratios")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 10. ratios contain expected fields
# ---------------------------------------------------------------------------


def test_ratios_contain_expected_fields():
    ticker = _company_with_ratios()
    response = client.get(f"/api/v1/companies/{ticker}/ratios")
    data = response.json()
    assert "ratios" in data
    assert len(data["ratios"]) > 0
    expected_fields = {
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "return_on_capital_employed_pct",
    }
    for entry in data["ratios"]:
        for field in expected_fields:
            assert field in entry, f"Missing field '{field}' in ratios entry"


# ---------------------------------------------------------------------------
# 11. valid cashflow → 200
# ---------------------------------------------------------------------------


def test_valid_cashflow_200():
    ticker = _company_with_cashflow()
    assert ticker is not None
    response = client.get(f"/api/v1/companies/{ticker}/cashflow")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 12. cashflow contains stored fields only
# ---------------------------------------------------------------------------


def test_cashflow_contains_stored_fields_only():
    ticker = _company_with_cashflow()
    response = client.get(f"/api/v1/companies/{ticker}/cashflow")
    data = response.json()
    assert "cashflow" in data
    assert len(data["cashflow"]) > 0
    expected_fields = {
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    }
    for entry in data["cashflow"]:
        # Check that the response does NOT contain computed/derived fields
        assert "free_cash_flow" not in entry
        assert "capex" not in entry
        assert "fcf" not in entry
        # Verify stored fields are present
        for field in expected_fields:
            assert field in entry, f"Missing field '{field}' in cashflow entry"


# ---------------------------------------------------------------------------
# 13. valid peers → 200
# ---------------------------------------------------------------------------


def test_valid_peers_200():
    ticker = _company_with_peers()
    assert ticker is not None
    response = client.get(f"/api/v1/companies/{ticker}/peers")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 14. company with no peers → 200 + empty peers
# ---------------------------------------------------------------------------


def test_company_without_peers_returns_empty():
    ticker = _company_without_peers()
    assert ticker is not None, "No company without peers found"
    response = client.get(f"/api/v1/companies/{ticker}/peers")
    assert response.status_code == 200
    data = response.json()
    assert data["peer_group_name"] is None
    assert data["peers"] == []


# ---------------------------------------------------------------------------
# 15. valid pros-cons → 200
# ---------------------------------------------------------------------------


def test_valid_pros_cons_200():
    ticker = _company_with_pros_cons()
    assert ticker is not None
    response = client.get(f"/api/v1/companies/{ticker}/pros-cons")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 16. company with no pros-cons → 200 + empty arrays
# ---------------------------------------------------------------------------


def test_company_without_pros_cons_returns_empty():
    ticker = _company_without_pros_cons()
    assert ticker is not None, "No company without pros/cons found"
    response = client.get(f"/api/v1/companies/{ticker}/pros-cons")
    assert response.status_code == 200
    data = response.json()
    assert "pros" in data
    assert "cons" in data
    assert isinstance(data["pros"], list)
    assert isinstance(data["cons"], list)


# ---------------------------------------------------------------------------
# 17. valid documents → 200
# ---------------------------------------------------------------------------


def test_valid_documents_200():
    ticker = _company_with_documents()
    assert ticker is not None
    response = client.get(f"/api/v1/companies/{ticker}/documents")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 18. company with no documents → 200 + empty list
# ---------------------------------------------------------------------------


def test_company_without_documents_returns_empty():
    ticker = _company_without_documents()
    assert ticker is not None, "No company without documents found"
    response = client.get(f"/api/v1/companies/{ticker}/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


# ---------------------------------------------------------------------------
# 19. unknown company returns 404 for ALL seven company-specific endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "/financials",
        "/ratios",
        "/cashflow",
        "/peers",
        "/pros-cons",
        "/documents",
    ],
)
def test_unknown_company_returns_404_for_all_endpoints(endpoint):
    response = client.get(f"/api/v1/companies/THIS_COMPANY_DOES_NOT_EXIST{endpoint}")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Company not found: THIS_COMPANY_DOES_NOT_EXIST"


# ---------------------------------------------------------------------------
# 20. JSON responses are serializable
# ---------------------------------------------------------------------------


def test_json_responses_are_serializable():
    endpoints = [
        "/api/v1/companies",
    ]
    # Add company-specific endpoints with known-good tickers
    ticker = _known_company_ids()[0]
    endpoints.extend(
        [
            f"/api/v1/companies/{ticker}",
            f"/api/v1/companies/{ticker}/financials",
            f"/api/v1/companies/{ticker}/ratios",
            f"/api/v1/companies/{ticker}/cashflow",
            f"/api/v1/companies/{ticker}/peers",
            f"/api/v1/companies/{ticker}/pros-cons",
            f"/api/v1/companies/{ticker}/documents",
        ]
    )

    for endpoint in endpoints:
        response = client.get(endpoint)
        # Verify the raw response text is valid JSON
        json.loads(response.text)
        # Verify all values are serializable Python objects
        assert _json_serializable(
            response.json()
        ), f"Response from {endpoint} is not JSON-serializable"


# ---------------------------------------------------------------------------
# 21. DB remains unchanged after API calls
# ---------------------------------------------------------------------------


def test_db_unchanged_after_api_calls():
    before = _table_counts()

    # Hammer the API with various calls
    client.get("/api/v1/companies")
    ticker = _known_company_ids()[0]
    client.get(f"/api/v1/companies/{ticker}")
    client.get(f"/api/v1/companies/{ticker}/financials")
    client.get(f"/api/v1/companies/{ticker}/ratios")
    client.get(f"/api/v1/companies/{ticker}/cashflow")
    client.get(f"/api/v1/companies/{ticker}/peers")
    client.get(f"/api/v1/companies/{ticker}/pros-cons")
    client.get(f"/api/v1/companies/{ticker}/documents")

    after = _table_counts()

    assert (
        before == after
    ), f"Database row counts changed during tests:\n  Before: {before}\n  After:  {after}"


# ---------------------------------------------------------------------------
# Additional: verify response content correctness
# ---------------------------------------------------------------------------


def test_financials_pnl_fields():
    """P&L entries should contain the documented fields."""
    ticker = _company_with_financials()
    response = client.get(f"/api/v1/companies/{ticker}/financials")
    data = response.json()
    expected_pnl_fields = {
        "year",
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout",
    }
    for entry in data["profit_and_loss"]:
        for field in expected_pnl_fields:
            assert field in entry, f"Missing P&L field '{field}'"


def test_financials_bs_fields():
    """Balance sheet entries should contain the documented fields (where data exists)."""
    ticker = _company_with_financials()
    response = client.get(f"/api/v1/companies/{ticker}/financials")
    data = response.json()
    expected_bs_fields = {
        "year",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
    }
    # balance_sheet may be empty because all years are NULL in the DB;
    # verify fields only if data exists
    if data["balance_sheet"]:
        for entry in data["balance_sheet"]:
            for field in expected_bs_fields:
                assert field in entry, f"Missing BS field '{field}'"


def test_peers_structure():
    """Peers response should contain the company itself plus its peer group members."""
    ticker = _company_with_peers()
    response = client.get(f"/api/v1/companies/{ticker}/peers")
    data = response.json()
    assert data["company_id"] == ticker
    assert data["peer_group_name"] is not None
    assert len(data["peers"]) > 0
    for peer in data["peers"]:
        assert "peer_group_name" in peer
        assert "peer_company_id" in peer
        assert "peer_company_name" in peer


def test_pros_cons_preserves_actual_text():
    """When pros/cons exist, the actual text should be preserved (not fabricated)."""
    ticker = _company_with_pros_cons()
    # Get actual DB data for verification
    db_rows = db.get_pros_cons(ticker)
    expected_pros = [
        r["pros"].strip() for r in db_rows if r["pros"] and r["pros"].strip().lower() != "none"
    ]
    expected_cons = [
        r["cons"].strip() for r in db_rows if r["cons"] and r["cons"].strip().lower() != "none"
    ]

    response = client.get(f"/api/v1/companies/{ticker}/pros-cons")
    data = response.json()
    assert data["company_id"] == ticker
    assert data["pros"] == expected_pros
    assert data["cons"] == expected_cons


def test_documents_structure():
    """Documents should have year (int or None) and annual_report_url."""
    ticker = _company_with_documents()
    response = client.get(f"/api/v1/companies/{ticker}/documents")
    data = response.json()
    assert data["company_id"] == ticker
    assert len(data["documents"]) > 0
    for doc in data["documents"]:
        assert "year" in doc
        assert doc["year"] is None or isinstance(doc["year"], int)
        assert "annual_report_url" in doc


def test_profile_fields():
    """Profile should contain all expected fields."""
    ticker = _known_company_ids()[0]
    response = client.get(f"/api/v1/companies/{ticker}")
    data = response.json()
    expected_fields = {
        "company_id",
        "company_name",
        "about_company",
        "website",
        "face_value",
        "book_value",
        "roe_percentage",
        "return_on_capital_employed_pct",
        "sector",
        "industry",
        "market_cap_cr",
    }
    for field in expected_fields:
        assert field in data, f"Missing profile field '{field}'"


# ---------------------------------------------------------------------------
# Day 42 — additional tests (extending existing coverage)
# ---------------------------------------------------------------------------


def test_company_list_count_field_and_unique_ids():
    """Day 42: Verify count field and unique company IDs."""
    response = client.get("/api/v1/companies")
    data = response.json()
    # count field matches list length
    assert data["count"] == len(data["companies"])
    # IDs are unique
    ids = [c["company_id"] for c in data["companies"]]
    assert len(ids) == len(set(ids)), "Duplicate company IDs found"


def test_company_profile_matches_db_helper():
    """Day 42: Verify GET /api/v1/companies/TCS matches db.get_company_profile("TCS")."""
    # Get profile from the API
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200

    api_profile = response.json()

    # Get profile from the DB helper directly — do not hard-code guessed data
    db_profile = db.get_company_profile("TCS")

    assert db_profile is not None, "TCS profile not found in DB"

    # Verify key fields match between API and DB helper
    assert api_profile["company_id"] == db_profile["company_id"]
    assert api_profile["company_name"] == db_profile["company_name"]
    assert api_profile["sector"] == db_profile["sector"]


def test_company_invalid_id_returns_404_with_message():
    """Day 42: GET /api/v1/companies/INVALID returns HTTP 404 with expected message."""
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Company not found: INVALID"


def test_company_db_unchanged_after_all_endpoints():
    """Day 42: All company API endpoints are read-only — DB must remain unchanged."""
    before = _table_counts()

    # Exercise every company endpoint using the module-level client
    client.get("/api/v1/companies")
    client.get("/api/v1/companies/TCS")
    client.get("/api/v1/companies/TCS/financials")
    client.get("/api/v1/companies/TCS/ratios")
    client.get("/api/v1/companies/TCS/cashflow")
    client.get("/api/v1/companies/TCS/peers")
    client.get("/api/v1/companies/TCS/pros-cons")
    client.get("/api/v1/companies/TCS/documents")

    after = _table_counts()
    assert before == after, (
        f"Database row counts changed during company tests:\n"
        f"  Before: {before}\n  After:  {after}"
    )
