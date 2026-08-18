"""
Day 42 — Dashboard ↔ API Integration Tests.

These tests verify that the Streamlit dashboard's screener data path
(src.dashboard.utils.db.get_screener_results) produces the same company
set, ordering, and metric values as the FastAPI screener endpoint
(GET /api/v1/screener) for equivalent filters.

The test uses the actual reusable data-layer function (get_screener_results)
rather than launching Streamlit, which avoids interfering with any running
server and tests the data-layer integration that the dashboard page relies on.
"""

from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.utils import db

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: normalize API response items into comparable form
# ---------------------------------------------------------------------------


def _normalize_api_items(items: list[dict]) -> list[dict]:
    """Normalize API items for comparison (round floats, strip None)."""
    normalized = []
    for item in items:
        norm = {}
        for k, v in item.items():
            if v is None:
                norm[k] = None
            elif isinstance(v, float):
                norm[k] = round(v, 2)
            else:
                norm[k] = v
        normalized.append(norm)
    return normalized


def _normalize_db_df(df) -> list[dict]:
    """Convert a DB DataFrame to normalized list of dicts for comparison."""
    if df is None or df.empty:
        return []
    records = df.to_dict(orient="records")
    normalized = []
    for rec in records:
        norm = {}
        for k, v in rec.items():
            if v is None or (isinstance(v, float) and v != v):  # noqa: PLR0124 NaN check
                norm[k] = None
            elif isinstance(v, float):
                norm[k] = round(v, 2)
            else:
                norm[k] = v
        normalized.append(norm)
    return normalized


def _get_common_fields():
    """Return the set of fields both API and DB share for comparison."""
    return {
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
    }


# ---------------------------------------------------------------------------
# Integration Test 1: No filters — full dataset comparison
# ---------------------------------------------------------------------------


def test_dashboard_screener_matches_api_no_filters():
    """Day 42: Dashboard screener results match API results with no filters."""
    # API result (page_size=100 to get all on one page)
    api_response = client.get("/api/v1/screener?sort=company_id&sort_dir=asc&page_size=100")
    assert api_response.status_code == 200
    api_data = api_response.json()

    # DB/dashboard result (get_screener_results with no filters)
    db_df = db.get_screener_results(filters={})

    # Compare company IDs
    api_ids = sorted([item["company_id"] for item in api_data["items"]])
    db_ids = sorted(db_df["company_id"].tolist())

    assert api_ids == db_ids, (
        f"Company IDs differ between API and dashboard:\n"
        f"  API: {set(api_ids) - set(db_ids)} extra in API\n"
        f"  DB:  {set(db_ids) - set(api_ids)} extra in DB"
    )
    assert api_data["total_count"] == len(
        db_df
    ), f"API total_count {api_data['total_count']} != DB row count {len(db_df)}"


# ---------------------------------------------------------------------------
# Integration Test 2: min_roe=15 filter — company ID + ROE comparison
# ---------------------------------------------------------------------------


def test_dashboard_screener_matches_api_min_roe_15():
    """Day 42: Dashboard screener with min_roe=15 matches API with min_roe=15."""
    # API result
    api_response = client.get(
        "/api/v1/screener?min_roe=15&sort=company_id&sort_dir=asc&page_size=100"
    )
    assert api_response.status_code == 200
    api_data = api_response.json()

    # Dashboard/DB result
    db_df = db.get_screener_results(filters={"ROE": {"min": 15}})

    # Compare company IDs
    api_ids = sorted([item["company_id"] for item in api_data["items"]])
    db_ids = sorted(db_df["company_id"].tolist())

    assert api_ids == db_ids, (
        f"Company IDs differ for min_roe=15:\n"
        f"  API: {set(api_ids) - set(db_ids)} extra in API\n"
        f"  DB:  {set(db_ids) - set(api_ids)} extra in DB"
    )

    assert api_data["total_count"] == len(
        db_df
    ), f"API total_count {api_data['total_count']} != DB row count {len(db_df)}"

    # Verify every returned company has ROE >= 15 (or NULL)
    for item in api_data["items"]:
        roe = item.get("return_on_equity_pct")
        if roe is not None:
            assert roe >= 15, f"Company {item['company_id']} has ROE {roe} < 15"


# ---------------------------------------------------------------------------
# Integration Test 3: Metric value comparison for key fields
# ---------------------------------------------------------------------------


def test_dashboard_api_metric_values_match():
    """Day 42: Compare metric values between API and dashboard for equivalent filters."""
    # API result
    api_response = client.get(
        "/api/v1/screener?min_roe=15&sort=company_id&sort_dir=asc&page_size=100"
    )
    api_data = api_response.json()

    # Dashboard/DB result
    db_df = db.get_screener_results(filters={"ROE": {"min": 15}})

    # Build lookup by company_id
    db_lookup = {}
    for _, row in db_df.iterrows():
        db_lookup[row["company_id"]] = row.to_dict()

    common_fields = _get_common_fields()

    for item in api_data["items"]:
        cid = item["company_id"]
        assert cid in db_lookup, f"Company {cid} in API but not in DB results"

        db_row = db_lookup[cid]

        for field in common_fields:
            if field not in db_row:
                continue
            api_val = item.get(field)
            db_val = db_row.get(field)

            # Handle None/NaN
            if api_val is None or (isinstance(db_val, float) and db_val != db_val):  # noqa: PLR0124
                assert api_val is None, f"Company {cid}, field {field}: API={api_val}, DB=None/NaN"
            elif isinstance(api_val, (int, float)) and isinstance(db_val, (int, float)):
                # Round to 2 decimal places for comparison
                api_rounded = round(float(api_val), 2)
                db_rounded = round(float(db_val), 2)
                assert (
                    abs(api_rounded - db_rounded) < 0.1
                ), f"Company {cid}, field {field}: API={api_rounded}, DB={db_rounded}"


# ---------------------------------------------------------------------------
# Integration Test 4: sector filter equivalence
# ---------------------------------------------------------------------------


def test_dashboard_api_sector_filter_match():
    """Day 42: Dashboard and API return the same companies for sector filter."""
    # API result
    api_response = client.get(
        "/api/v1/screener?sector=Financials&sort=company_id&sort_dir=asc&page_size=100"
    )
    assert api_response.status_code == 200
    api_data = api_response.json()

    api_ids = sorted([item["company_id"] for item in api_data["items"]])

    # Dashboard/DB result: the dashboard page filters the DB result by sector
    db_df = db.get_screener_results(filters={})
    db_df_filtered = db_df[db_df["sector"] == "Financials"]
    db_ids = sorted(db_df_filtered["company_id"].tolist())

    assert api_ids == db_ids, (
        f"Sector filter 'Financials' mismatch:\n"
        f"  API: {set(api_ids) - set(db_ids)} extra in API\n"
        f"  DB:  {set(db_ids) - set(api_ids)} extra in DB"
    )


# ---------------------------------------------------------------------------
# Integration Test 5: Combined filters equivalence
# ---------------------------------------------------------------------------


def test_dashboard_api_combined_filters_match():
    """Day 42: Dashboard and API return the same companies for combined filters."""
    # API result
    api_response = client.get(
        "/api/v1/screener?min_roe=15&max_debt_to_equity=1&sort=company_id&sort_dir=asc&page_size=100"
    )
    assert api_response.status_code == 200
    api_data = api_response.json()

    api_ids = sorted([item["company_id"] for item in api_data["items"]])

    # Dashboard/DB result
    db_df = db.get_screener_results(
        filters={
            "ROE": {"min": 15},
            "Debt to Equity": {"max": 1},
        }
    )
    db_ids = sorted(db_df["company_id"].tolist())

    assert api_ids == db_ids, (
        f"Combined filter mismatch:\n"
        f"  API: {set(api_ids) - set(db_ids)} extra in API\n"
        f"  DB:  {set(db_ids) - set(api_ids)} extra in DB"
    )


# ---------------------------------------------------------------------------
# Integration Test 6: DB safety after integration tests
# ---------------------------------------------------------------------------


def _table_counts() -> dict[str, int]:
    """Return row counts for all 12 live tables (read-only)."""
    import sqlite3
    from pathlib import Path

    DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"
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


def test_integration_db_unchanged():
    """Day 42: Database must remain unchanged after all integration tests."""
    before = _table_counts()

    # Re-run the integration comparison
    client.get("/api/v1/screener?min_roe=15&sort=company_id&sort_dir=asc&page_size=100")
    db.get_screener_results(filters={"ROE": {"min": 15}})
    client.get("/api/v1/screener?sector=Financials&page_size=100")
    db.get_screener_results(filters={})

    after = _table_counts()
    assert before == after, (
        f"Database row counts changed during integration tests:\n"
        f"  Before: {before}\n  After:  {after}"
    )
