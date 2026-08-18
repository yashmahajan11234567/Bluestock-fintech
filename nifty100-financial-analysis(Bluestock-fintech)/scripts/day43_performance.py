"""
Day 43 Performance Test Script
==============================

Sprint 6 — Day 43: Performance & Integration Testing

This script performs:
1. Screener API load test: 10 concurrent requests via ThreadPoolExecutor
2. Company Profile dashboard load time for 5 real tickers
3. SQLite index analysis (EXPLAIN QUERY PLAN)
4. Database fingerprint capture (read-only, before and after)

Safety:
- Read-only database access (no INSERT/UPDATE/DELETE/CREATE/DROP)
- Does NOT modify any production code
- Does NOT start or kill any servers (uses FastAPI TestClient for API testing)
- Does NOT modify db.py or any protected Day 36-42 files
"""

from __future__ import annotations

import json
import os
import platform
import sqlite3
import statistics
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — ensure src/ is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(str(PROJECT_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"

# ---------------------------------------------------------------------------
# All 12 tables for DB safety fingerprint
# ---------------------------------------------------------------------------
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


def db_fingerprint() -> dict[str, int]:
    """Read-only row counts for all 12 tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    counts = {}
    for t in ALL_TABLES:
        row = conn.execute(f'SELECT COUNT(*) AS c FROM "{t}"').fetchone()
        counts[t] = row["c"]
    conn.close()
    return counts


# ---------------------------------------------------------------------------
# Section: Screener Load Test
# ---------------------------------------------------------------------------

def run_screener_load_test() -> dict:
    """
    Run 10 concurrent screener API calls using ThreadPoolExecutor.
    Uses FastAPI TestClient (real application execution path).
    """
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)

    results = []
    total_start = time.perf_counter()

    def make_request(req_id: int) -> dict:
        start = time.perf_counter()
        try:
            response = client.get("/api/v1/screener?page_size=10")
            elapsed = time.perf_counter() - start
            status = response.status_code
            ok = status == 200
        except Exception as e:
            elapsed = time.perf_counter() - start
            status = -1
            ok = False
            response = type('obj', (), {'json': lambda: {'error': str(e)}})()
        return {
            "req_id": req_id,
            "status": status,
            "ok": ok,
            "elapsed": round(elapsed, 4),
        }

    # Launch 10 concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(10)]
        for future in as_completed(futures):
            results.append(future.result())

    total_elapsed = time.perf_counter() - total_start

    # Sort by req_id for consistent reporting
    results.sort(key=lambda r: r["req_id"])

    times = [r["elapsed"] for r in results]
    success_count = sum(1 for r in results if r["ok"])
    failure_count = 10 - success_count

    return {
        "endpoint": "GET /api/v1/screener?page_size=10",
        "methodology": "FastAPI TestClient — real application execution path (no HTTP server started). 10 concurrent via ThreadPoolExecutor(max_workers=10).",
        "individual_times": results,
        "min": round(min(times), 4),
        "max": round(max(times), 4),
        "avg": round(statistics.mean(times), 4),
        "median": round(statistics.median(times), 4),
        "total_wall_clock": round(total_elapsed, 4),
        "success_count": success_count,
        "failure_count": failure_count,
        "status_codes": [r["status"] for r in results],
        "target": "All 10 requests complete within 10 seconds.",
        "target_seconds": 10,
        "PASS": total_elapsed < 10 and success_count == 10,
    }


# ---------------------------------------------------------------------------
# Section: Company Profile Dashboard Performance
# ---------------------------------------------------------------------------

def select_5_real_tickers() -> list[str]:
    """Select 5 representative real company tickers from the database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # Get 5 companies that have financial data (ratios, cashflow, profile)
    rows = conn.execute(
        """
        SELECT DISTINCT c.id
        FROM companies c
        JOIN financial_ratios fr ON fr.company_id = c.id
        JOIN cashflow cf ON cf.company_id = c.id
        WHERE fr.company_id = c.id
        ORDER BY c.id
        LIMIT 5
        """
    ).fetchall()
    conn.close()
    tickers = [r["id"] for r in rows]
    return tickers


def measure_company_profile(ticker: str) -> dict:
    """
    Measure the dashboard Company Profile data-loading path.
    This measures the complete Python/data-loading path used by the page
    (src/dashboard/_pages/_02_profile.py render() function calls):
      - get_company_list()
      - get_company_profile(company_id)
      - get_financial_ratios(company_id)
      - get_cashflow_data(company_id)
      - get_capital_alloc_data(company_id)

    This is backend/data-path timing, NOT browser-rendered timing.
    """
    from src.dashboard.utils.db import (
        get_company_list,
        get_company_profile,
        get_financial_ratios,
        get_cashflow_data,
        get_capital_alloc_data,
    )

    start = time.perf_counter()

    # Replicate the data-loading path from _02_profile.py render()
    companies = get_company_list()  # loads company list (same as page does)
    profile = get_company_profile(ticker)
    ratios = get_financial_ratios(ticker)
    cashflow = get_cashflow_data(ticker)
    capital = get_capital_alloc_data(ticker)

    elapsed = time.perf_counter() - start

    # Verify data exists
    success = (
        profile is not None
        and not (ratios is not None and ratios.empty)
        and not (cashflow is not None and cashflow.empty)
    )

    return {
        "ticker": ticker,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 4),
        "success": success,
        "profile_exists": profile is not None,
        "ratios_rows": len(ratios) if ratios is not None else 0,
        "cashflow_rows": len(cashflow) if cashflow is not None else 0,
        "capital_alloc_rows": len(capital) if capital is not None else 0,
    }


def run_company_profile_tests() -> dict:
    """Measure Company Profile load time for 5 real tickers."""
    tickers = select_5_real_tickers()

    if len(tickers) < 5:
        return {
            "error": f"Could not find 5 tickers with data; found {len(tickers)}: {tickers}",
            "tickers_used": tickers,
        }

    results = []
    for ticker in tickers:
        r = measure_company_profile(ticker)
        r["target"] = "Each < 3 seconds."
        r["PASS"] = r["elapsed_seconds"] < 3.0 and r["success"]
        results.append(r)

    elapsed_times = [r["elapsed_seconds"] for r in results]
    success_count = sum(1 for r in results if r["PASS"])

    return {
        "tickers_used": tickers,
        "results": results,
        "fastest": round(min(elapsed_times), 4),
        "slowest": round(max(elapsed_times), 4),
        "average": round(statistics.mean(elapsed_times), 4),
        "target": "Each < 3 seconds.",
        "target_seconds": 3,
        "success_count": success_count,
        "total_count": len(results),
        "PASS": all(r["PASS"] for r in results),
        "timing_type": "Backend/data-path timing via direct db.py function calls (not browser-rendered. Full data-loading path from _02_profile.py is exercised).",
    }


# ---------------------------------------------------------------------------
# Section: SQLite Index Analysis
# ---------------------------------------------------------------------------

def analyze_sqlite_indexes() -> dict:
    """Inspect existing indexes and run EXPLAIN QUERY PLAN on key queries."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    result = {
        "relevant_tables": {},
        "existing_indexes": [],
        "query_plans": {},
        "measured_query_timings": {},
    }

    # Relevant tables: those with company_id and year columns
    relevant_tables = [
        "financial_ratios",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "market_cap",
        "stock_prices",
        "peer_groups",
        "prosandcons",
        "documents",
        "analysis",
    ]

    # Record which tables have company_id and year columns
    for t in relevant_tables:
        cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
        col_names = [c["name"] for c in cols]
        has_company_id = "company_id" in col_names
        has_year = "year" in col_names
        if has_company_id or has_year:
            result["relevant_tables"][t] = {
                "has_company_id": has_company_id,
                "has_year": has_year,
                "columns": col_names,
            }

    # All indexes
    for row in conn.execute(
        "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY tbl_name, name"
    ):
        idx_name = row["name"]
        tbl_name = row["tbl_name"]
        info = conn.execute(f"PRAGMA index_info({idx_name})").fetchall()
        cols = [r["name"] for r in info]
        result["existing_indexes"].append({
            "name": idx_name,
            "table": tbl_name,
            "columns": cols,
        })

    # EXPLAIN QUERY PLAN for screener query
    latest_row = conn.execute("SELECT MAX(year) AS yr FROM market_cap").fetchone()
    yr = latest_row["yr"] if latest_row and latest_row["yr"] else 2024

    # Screener query (from db.py get_screener_results, simplified)
    screener_sql = f"""
        SELECT c.id AS company_id, c.company_name,
               s.broad_sector AS sector,
               fr.return_on_equity_pct, fr.debt_to_equity,
               fr.operating_profit_margin_pct, fr.interest_coverage,
               fr.free_cash_flow_cr, fr.cash_from_operations_cr,
               fr.net_profit_margin_pct,
               m.pe_ratio, m.pb_ratio, m.dividend_yield_pct,
               m.market_cap_crore,
               a.compounded_sales_growth, a.compounded_profit_growth,
               pl.net_profit
        FROM companies c
        JOIN sectors s ON s.company_id = c.id
        JOIN financial_ratios fr ON fr.company_id = c.id
          AND SUBSTR(fr.year, 1, 4) = '{yr}'
        LEFT JOIN market_cap m ON m.company_id = c.id AND m.year = ?
        LEFT JOIN analysis a ON a.company_id = c.id
        LEFT JOIN profitandloss pl ON pl.company_id = c.id
    """
    plan = conn.execute(f"EXPLAIN QUERY PLAN {screener_sql}", (yr,)).fetchall()
    result["query_plans"]["screener"] = [dict(r) for r in plan]

    # Measure screener timing
    import time as _time
    t0 = _time.perf_counter()
    for _ in range(5):
        conn.execute(screener_sql, (yr,)).fetchall()
    screener_ms = (_time.perf_counter() - t0) / 5 * 1000
    result["measured_query_timings"]["screener_sql"] = round(screener_ms, 2)

    # Company profile query
    profile_sql = """
        SELECT
            c.id AS company_id, c.company_name, c.about_company, c.website,
            c.face_value, c.book_value, c.roe_percentage,
            c.roce_percentage AS return_on_capital_employed_pct,
            s.broad_sector AS sector, s.sub_sector AS industry,
            m.market_cap_crore AS market_cap_cr
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN market_cap m ON m.company_id = c.id
        WHERE c.id = ?
        GROUP BY c.id
    """
    plan = conn.execute("EXPLAIN QUERY PLAN " + profile_sql, ("TCS",)).fetchall()
    result["query_plans"]["company_profile"] = [dict(r) for r in plan]

    t0 = _time.perf_counter()
    for _ in range(100):
        conn.execute(profile_sql, ("TCS",)).fetchone()
    profile_ms = (_time.perf_counter() - t0) / 100 * 1000
    result["measured_query_timings"]["company_profile"] = round(profile_ms, 2)

    # Financial ratios query
    ratios_sql = """
        SELECT CAST(fr.year AS INTEGER) AS year,
               fr.net_profit_margin_pct, fr.operating_profit_margin_pct,
               fr.return_on_equity_pct, c.roce_percentage AS return_on_capital_employed_pct,
               fr.debt_to_equity, fr.interest_coverage, fr.asset_turnover,
               fr.free_cash_flow_cr, fr.capex_cr, fr.earnings_per_share,
               fr.book_value_per_share, fr.dividend_payout_ratio_pct,
               fr.total_debt_cr, fr.cash_from_operations_cr
        FROM financial_ratios fr
        JOIN companies c ON c.id = fr.company_id
        WHERE fr.company_id = ?
        ORDER BY fr.year DESC
    """
    plan = conn.execute("EXPLAIN QUERY PLAN " + ratios_sql, ("TCS",)).fetchall()
    result["query_plans"]["financial_ratios"] = [dict(r) for r in plan]

    t0 = _time.perf_counter()
    for _ in range(100):
        conn.execute(ratios_sql, ("TCS",)).fetchall()
    ratios_ms = (_time.perf_counter() - t0) / 100 * 1000
    result["measured_query_timings"]["financial_ratios"] = round(ratios_ms, 2)

    # Cashflow query
    cf_sql = """
        SELECT CAST(year AS INTEGER) AS year, operating_activity, investing_activity,
               financing_activity, net_cash_flow
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year DESC
    """
    plan = conn.execute("EXPLAIN QUERY PLAN " + cf_sql, ("TCS",)).fetchall()
    result["query_plans"]["cashflow"] = [dict(r) for r in plan]

    t0 = _time.perf_counter()
    for _ in range(100):
        conn.execute(cf_sql, ("TCS",)).fetchall()
    cf_ms = (_time.perf_counter() - t0) / 100 * 1000
    result["measured_query_timings"]["cashflow"] = round(cf_ms, 2)

    conn.close()
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("DAY 43 PERFORMANCE TEST SCRIPT")
    print("=" * 70)

    # --- Environment ---
    print("\n--- Environment ---")
    import platform
    print(f"Python: {sys.version}")
    print(f"OS: {platform.platform()}")
    print(f"SQLite: {sqlite3.sqlite_version}")
    print(f"DB Path: {DB_PATH}")

    # --- DB Fingerprint BEFORE ---
    print("\n--- DB Fingerprint (BEFORE testing) ---")
    before = db_fingerprint()
    for t in ALL_TABLES:
        print(f"  {t}: {before[t]}")

    # --- Screener Load Test ---
    print("\n--- Screener Load Test (10 concurrent) ---")
    try:
        screener_results = run_screener_load_test()
        print(f"  Endpoint: {screener_results['endpoint']}")
        print(f"  Method: {screener_results['methodology']}")
        print(f"  Individual times: {[r['elapsed'] for r in screener_results['individual_times']]}")
        print(f"  Min: {screener_results['min']}")
        print(f"  Max: {screener_results['max']}")
        print(f"  Avg: {screener_results['avg']}")
        print(f"  Median: {screener_results['median']}")
        print(f"  Total wall-clock: {screener_results['total_wall_clock']}")
        print(f"  Success: {screener_results['success_count']}, Failure: {screener_results['failure_count']}")
        print(f"  Status codes: {screener_results['status_codes']}")
        print(f"  Target: {screener_results['target']}")
        print(f"  PASS: {screener_results['PASS']}")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        screener_results = {"error": str(e), "PASS": False}

    # --- Company Profile Tests ---
    print("\n--- Company Profile Performance (5 tickers) ---")
    try:
        profile_results = run_company_profile_tests()
        print(f"  Tickers used: {profile_results.get('tickers_used', [])}")
        if "results" in profile_results:
            for r in profile_results["results"]:
                print(f"  {r['ticker']}: {r['elapsed_seconds']}s — {'PASS' if r['PASS'] else 'FAIL'}")
            print(f"  Fastest: {profile_results['fastest']}")
            print(f"  Slowest: {profile_results['slowest']}")
            print(f"  Average: {profile_results['average']}")
            print(f"  PASS: {profile_results['PASS']}")
        else:
            print(f"  ERROR: {profile_results.get('error')}")
            print(f"  PASS: {profile_results.get('PASS', False)}")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        profile_results = {"error": str(e), "PASS": False}

    # --- SQLite Analysis ---
    print("\n--- SQLite Index Analysis ---")
    try:
        sqlite_results = analyze_sqlite_indexes()
        print("  Relevant tables (with company_id/year):")
        for t, info in sqlite_results["relevant_tables"].items():
            print(f"    {t}: company_id={info['has_company_id']}, year={info['has_year']}")
        print("\n  Existing indexes:")
        if sqlite_results["existing_indexes"]:
            for idx in sqlite_results["existing_indexes"]:
                print(f"    {idx['name']} on {idx['table']}({', '.join(idx['columns'])})")
        else:
            print("    (none)")
        print("\n  EXPLAIN QUERY PLAN findings:")
        for query_name, plan in sqlite_results["query_plans"].items():
            print(f"    {query_name}:")
            for step in plan:
                print(f"      detail: {step.get('detail', '')}")
        print("\n  Measured query timings (ms):")
        for q, t_ms in sqlite_results["measured_query_timings"].items():
            print(f"    {q}: {t_ms} ms")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        sqlite_results = {"error": str(e)}

    # --- DB Fingerprint AFTER ---
    print("\n--- DB Fingerprint (AFTER testing) ---")
    after = db_fingerprint()
    print(f"  Data mutation: {'NO' if before == after else 'YES — DATA CHANGED!'}")
    for t in ALL_TABLES:
        print(f"  {t}: {before[t]} -> {after[t]}")

    # --- Save results ---
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "python": sys.version,
            "os": platform.platform(),
            "sqlite": sqlite3.sqlite_version,
            "db_path": str(DB_PATH),
        },
        "db_fingerprint_before": before,
        "db_fingerprint_after": after,
        "db_data_unchanged": before == after,
        "screener_load_test": screener_results,
        "company_profile_tests": profile_results,
        "sqlite_analysis": sqlite_results,
    }

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "day43_raw_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n--- Raw results saved to: {output_file} ---")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    screener_pass = screener_results.get("PASS", False) if "error" not in screener_results else False
    profile_pass = profile_results.get("PASS", False) if "error" not in profile_results else False
    db_safe = before == after

    print(f"  Screener load test (10 concurrent < 10s): {'PASS' if screener_pass else 'FAIL'}")
    print(f"  Company profile (5 tickers < 3s each):    {'PASS' if profile_pass else 'FAIL'}")
    print(f"  Database unchanged:                       {'PASS' if db_safe else 'FAIL - DATA MUTATED!'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
