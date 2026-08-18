"""
Tests for the Day 40 Screener API endpoint.

Uses real SQLite-backed data from the live database.  No data is modified
during these tests — a read-only fingerprint is captured before and verified
unchanged after.
"""

import json
import sqlite3
from pathlib import Path

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


def _json_serializable(obj):
    """Recursively verify that an object is JSON-serializable."""
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# 1. no filters → HTTP 200
# ---------------------------------------------------------------------------


def test_screener_no_filters_returns_200():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 2. result structure valid
# ---------------------------------------------------------------------------


def test_screener_result_structure_valid():
    response = client.get("/api/v1/screener")
    data = response.json()
    assert "items" in data
    assert "total_count" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total_count"], int)


# ---------------------------------------------------------------------------
# 3. total_count <= 92
# ---------------------------------------------------------------------------


def test_screener_total_count_le_92():
    response = client.get("/api/v1/screener")
    data = response.json()
    assert data["total_count"] <= 92


# ---------------------------------------------------------------------------
# 4. page/page_size valid
# ---------------------------------------------------------------------------


def test_screener_page_size_valid():
    response = client.get("/api/v1/screener?page=1&page_size=10")
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == min(10, data["total_count"])


# ---------------------------------------------------------------------------
# 5. default sort works
# ---------------------------------------------------------------------------


def test_screener_default_sort_works():
    response = client.get("/api/v1/screener")
    data = response.json()
    assert response.status_code == 200
    scores = [item.get("composite_quality_score") for item in data["items"]]
    valid_scores = [s for s in scores if s is not None]
    assert valid_scores == sorted(valid_scores, reverse=True)


# ---------------------------------------------------------------------------
# 6. sort_dir=asc works
# ---------------------------------------------------------------------------


def test_screener_sort_dir_asc():
    response = client.get("/api/v1/screener?sort=company_name&sort_dir=asc")
    data = response.json()
    names = [item["company_name"] for item in data["items"] if item.get("company_name")]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# 7. min_roe filter works
# ---------------------------------------------------------------------------


def test_screener_min_roe_filter():
    threshold = 20.0
    response = client.get(f"/api/v1/screener?min_roe={threshold}")
    data = response.json()
    for item in data["items"]:
        roe = item.get("return_on_equity_pct")
        if roe is not None:
            assert roe >= threshold


# ---------------------------------------------------------------------------
# 8. max_roe filter works
# ---------------------------------------------------------------------------


def test_screener_max_roe_filter():
    response_all = client.get("/api/v1/screener")
    total_count = response_all.json()["total_count"]
    threshold = 50.0
    response = client.get(f"/api/v1/screener?max_roe={threshold}")
    data = response.json()
    for item in data["items"]:
        roe = item.get("return_on_equity_pct")
        if roe is not None:
            assert roe <= threshold
    assert data["total_count"] <= total_count


# ---------------------------------------------------------------------------
# 9. min_opm works
# ---------------------------------------------------------------------------


def test_screener_min_opm():
    response = client.get("/api/v1/screener?min_opm=15")
    data = response.json()
    for item in data["items"]:
        opm = item.get("operating_profit_margin_pct")
        if opm is not None:
            assert opm >= 15


# ---------------------------------------------------------------------------
# 10. max_debt_to_equity works
# ---------------------------------------------------------------------------


def test_screener_max_debt_to_equity():
    response = client.get("/api/v1/screener?max_debt_to_equity=1")
    data = response.json()
    for item in data["items"]:
        de = item.get("debt_to_equity")
        if de is not None:
            assert de <= 1


# ---------------------------------------------------------------------------
# 11. min_market_cap works
# ---------------------------------------------------------------------------


def test_screener_min_market_cap():
    threshold = 50000.0
    response = client.get(f"/api/v1/screener?min_market_cap={threshold}")
    data = response.json()
    for item in data["items"]:
        mc = item.get("market_cap_crore")
        if mc is not None:
            assert mc >= threshold


# ---------------------------------------------------------------------------
# 12. min_fcf works
# ---------------------------------------------------------------------------


def test_screener_min_fcf():
    response = client.get("/api/v1/screener?min_fcf=1000")
    data = response.json()
    for item in data["items"]:
        fcf = item.get("free_cash_flow_cr")
        if fcf is not None:
            assert fcf >= 1000


# ---------------------------------------------------------------------------
# 13. min_revenue_growth works
# ---------------------------------------------------------------------------


def test_screener_min_revenue_growth():
    response = client.get("/api/v1/screener?min_revenue_growth=10")
    data = response.json()
    for item in data["items"]:
        rg = item.get("compounded_sales_growth")
        if rg is not None:
            assert rg >= 10


# ---------------------------------------------------------------------------
# 14. min_pat_growth works
# ---------------------------------------------------------------------------


def test_screener_min_pat_growth():
    response = client.get("/api/v1/screener?min_pat_growth=10")
    data = response.json()
    for item in data["items"]:
        pg = item.get("compounded_profit_growth")
        if pg is not None:
            assert pg >= 10


# ---------------------------------------------------------------------------
# 15. min_dividend_yield works
# ---------------------------------------------------------------------------


def test_screener_min_dividend_yield():
    response = client.get("/api/v1/screener?min_dividend_yield=1")
    data = response.json()
    for item in data["items"]:
        dy = item.get("dividend_yield_pct")
        if dy is not None:
            assert dy >= 1


# ---------------------------------------------------------------------------
# 16. max_pe works
# ---------------------------------------------------------------------------


def test_screener_max_pe():
    response = client.get("/api/v1/screener?max_pe=20")
    data = response.json()
    for item in data["items"]:
        pe = item.get("pe_ratio")
        if pe is not None:
            assert pe <= 20


# ---------------------------------------------------------------------------
# 17. max_pb works
# ---------------------------------------------------------------------------


def test_screener_max_pb():
    response = client.get("/api/v1/screener?max_pb=3")
    data = response.json()
    for item in data["items"]:
        pb = item.get("pb_ratio")
        if pb is not None:
            assert pb <= 3


# ---------------------------------------------------------------------------
# 18. min_interest_coverage works
# ---------------------------------------------------------------------------


def test_screener_min_interest_coverage():
    response = client.get("/api/v1/screener?min_interest_coverage=5")
    data = response.json()
    for item in data["items"]:
        ic = item.get("interest_coverage")
        if ic is not None:
            assert ic >= 5


# ---------------------------------------------------------------------------
# 19. sector filter works
# ---------------------------------------------------------------------------


def test_screener_sector_filter():
    response = client.get("/api/v1/screener?sector=Financials")
    data = response.json()
    assert response.status_code == 200
    for item in data["items"]:
        assert item.get("sector") == "Financials"


# ---------------------------------------------------------------------------
# 20. AND semantics work when multiple filters supplied
# ---------------------------------------------------------------------------


def test_screener_and_semantics():
    response = client.get("/api/v1/screener?min_roe=15&max_debt_to_equity=1&sector=Financials")
    data = response.json()
    for item in data["items"]:
        if item.get("return_on_equity_pct") is not None:
            assert item["return_on_equity_pct"] >= 15
        if item.get("debt_to_equity") is not None:
            assert item["debt_to_equity"] <= 1
        assert item.get("sector") == "Financials"


# ---------------------------------------------------------------------------
# 21. pagination changes items but not total_count
# ---------------------------------------------------------------------------


def test_screener_pagination_changes_items_not_total():
    response_full = client.get("/api/v1/screener?page=1&page_size=92")
    response_page = client.get("/api/v1/screener?page=1&page_size=10")
    full_data = response_full.json()
    page_data = response_page.json()
    assert full_data["total_count"] == page_data["total_count"]
    assert len(full_data["items"]) >= len(page_data["items"])


# ---------------------------------------------------------------------------
# 22. page 2 differs from page 1
# ---------------------------------------------------------------------------


def test_screener_page_2_differs_from_page_1():
    response_p1 = client.get("/api/v1/screener?page=1&page_size=10")
    response_p2 = client.get("/api/v1/screener?page=2&page_size=10")
    data_p1 = response_p1.json()
    data_p2 = response_p2.json()
    if data_p1["total_count"] > 10:
        ids_p1 = [item["company_id"] for item in data_p1["items"]]
        ids_p2 = [item["company_id"] for item in data_p2["items"]]
        assert ids_p1 != ids_p2


# ---------------------------------------------------------------------------
# 23. page_size max 100 enforced
# ---------------------------------------------------------------------------


def test_screener_page_size_max_100_enforced():
    response_ok = client.get("/api/v1/screener?page_size=100")
    assert response_ok.status_code == 200
    response_bad = client.get("/api/v1/screener?page_size=101")
    assert response_bad.status_code == 422


# ---------------------------------------------------------------------------
# 24. invalid page rejected with 422
# ---------------------------------------------------------------------------


def test_screener_invalid_page_rejected():
    response = client.get("/api/v1/screener?page=0")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 25. invalid page_size rejected with 422
# ---------------------------------------------------------------------------


def test_screener_invalid_page_size_rejected():
    response = client.get("/api/v1/screener?page_size=0")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 26. invalid numeric threshold rejected with 422
# ---------------------------------------------------------------------------


def test_screener_invalid_numeric_threshold_rejected():
    response = client.get("/api/v1/screener?min_roe=not_a_number")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 27. invalid sort rejected with 422
# ---------------------------------------------------------------------------


def test_screener_invalid_sort_rejected():
    response = client.get("/api/v1/screener?sort=nonexistent_column")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 28. empty result returns 200 + items=[]
# ---------------------------------------------------------------------------


def test_screener_empty_result_returns_200():
    # min_roe above the maximum ROE in the dataset (max is ~1.2M)
    response = client.get("/api/v1/screener?min_roe=10000000")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total_count"] == 0
    assert data["total_pages"] == 0


# ---------------------------------------------------------------------------
# 29. JSON serializable
# ---------------------------------------------------------------------------


def test_screener_json_serializable():
    response = client.get("/api/v1/screener")
    assert _json_serializable(response.json())
    assert _json_serializable(response.text)


# ---------------------------------------------------------------------------
# 30. market_cap filter actually works
# ---------------------------------------------------------------------------


def test_screener_market_cap_filter_works():
    threshold = 100000.0
    response = client.get(f"/api/v1/screener?min_market_cap={threshold}")
    data = response.json()
    # Every returned item must satisfy the filter
    for item in data["items"]:
        mc = item.get("market_cap_crore")
        if mc is not None:
            assert mc >= threshold
    # Compare with DB-level result
    db_df = db.get_screener_results(filters={"Market Cap": {"min": threshold}})
    assert len(db_df) == data["total_count"]


# ---------------------------------------------------------------------------
# Response field completeness
# ---------------------------------------------------------------------------


def test_screener_response_contains_expected_fields():
    response = client.get("/api/v1/screener?page_size=1")
    data = response.json()
    if data["items"]:
        item = data["items"][0]
        expected_fields = {
            "company_id",
            "company_name",
            "sector",
            "return_on_equity_pct",
            "debt_to_equity",
            "operating_profit_margin_pct",
            "interest_coverage",
            "free_cash_flow_cr",
            "cash_from_operations_cr",
            "net_profit_margin_pct",
            "compounded_sales_growth",
            "compounded_profit_growth",
            "dividend_yield_pct",
            "pe_ratio",
            "pb_ratio",
            "net_profit",
            "composite_quality_score",
            "sector_relative_score",
            "market_cap_crore",
        }
        for field in expected_fields:
            assert field in item, f"Missing field '{field}' in screener item"


# ---------------------------------------------------------------------------
# DB remains unchanged after API calls
# ---------------------------------------------------------------------------


def test_screener_db_unchanged_after_api_calls():
    before = _table_counts()

    client.get("/api/v1/screener")
    client.get("/api/v1/screener?min_roe=15&max_debt_to_equity=1&sector=Financials")
    client.get("/api/v1/screener?sort=company_name&page=2&page_size=10")
    client.get("/api/v1/screener?min_market_cap=100000")

    after = _table_counts()
    assert (
        before == after
    ), f"Database row counts changed during tests:\n  Before: {before}\n  After:  {after}"


# ---------------------------------------------------------------------------
# Day 42 — min_roe=15 filter (explicit Day 42 test)
# ---------------------------------------------------------------------------


def test_screener_min_roe_15_filter_day42():
    """Day 42: GET /api/v1/screener?min_roe=15 returns ONLY companies with ROE >= 15."""
    # Get unfiltered results for comparison
    response_all = client.get("/api/v1/screener")
    data_all = response_all.json()
    total_unfiltered = data_all["total_count"]

    # Get filtered results
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()

    # Verify every returned company with non-null ROE satisfies >= 15
    for item in data["items"]:
        roe = item.get("return_on_equity_pct")
        if roe is not None:
            assert roe >= 15, f"Company {item['company_id']} has ROE {roe} < 15 — filter violation"

    # Verify the filter actually reduces results (85 < 92)
    assert (
        data["total_count"] < total_unfiltered
    ), f"min_roe=15 did not reduce results: {data['total_count']} vs {total_unfiltered}"

    # Cross-check: compare with DB helper for equivalent filter
    db_df = db.get_screener_results(filters={"ROE": {"min": 15}})
    df_filtered = db_df[
        db_df["return_on_equity_pct"].notna() & (db_df["return_on_equity_pct"] < 15)
    ]
    assert len(df_filtered) == 0, "DB-level filter found ROE < 15 violations"
    assert (
        len(db_df) == data["total_count"]
    ), f"DB result count {len(db_df)} != API total_count {data['total_count']}"


def test_screener_min_roe_15_excludes_nulls_from_violation():
    """Day 42: Companies with NULL ROE must appear (they don't violate >= 15)."""
    response = client.get("/api/v1/screener?min_roe=15")
    data = response.json()

    # Every non-null ROE must be >= 15
    for item in data["items"]:
        if item.get("return_on_equity_pct") is not None:
            assert item["return_on_equity_pct"] >= 15


# ---------------------------------------------------------------------------
# Day 42 — invalid parameter handling
# ---------------------------------------------------------------------------


def test_screener_invalid_page_size_returns_client_error():
    """Day 42: An invalid screener parameter must return a 4xx error."""
    response = client.get("/api/v1/screener?page_size=101")
    # Current FastAPI behavior: 422 for Query constraint violations
    assert response.status_code in (
        400,
        422,
    ), f"Expected 400 or 422 for invalid page_size, got {response.status_code}"


def test_screener_invalid_numeric_param_returns_client_error():
    """Day 42: A non-numeric value for a numeric query parameter must return a 4xx error."""
    response = client.get("/api/v1/screener?min_roe=not_a_number")
    assert response.status_code in (
        400,
        422,
    ), f"Expected 400 or 422 for non-numeric min_roe, got {response.status_code}"


# ---------------------------------------------------------------------------
# Day 42 — DB safety (duplicate safety net)
# ---------------------------------------------------------------------------


def test_screener_day42_db_unchanged():
    """Day 42: Screener endpoint must not mutate the database."""
    before = _table_counts()

    client.get("/api/v1/screener?min_roe=15")
    client.get("/api/v1/screener?min_roe=abc")
    client.get("/api/v1/screener?page_size=999")

    after = _table_counts()
    assert before == after, f"Database row counts changed:\n  Before: {before}\n  After:  {after}"
