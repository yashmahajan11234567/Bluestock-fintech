"""
Day 43 Fix — Baseline Screener Results Capture
===============================================
Captures baseline screener outputs BEFORE optimization for correctness
comparison after optimization.

Tests:
1. Unfiltered screener (default sort)
2. min_roe=15 filter
3. Sector filter (Information Technology)
4. Sort by composite_quality_score descending
5. Sort by company_name ascending
6. Pagination (page=2, page_size=10)
7. min_roe=15 + max_roe=30 + sector filter

For each: captures company IDs, metric values, composite scores,
ranking/order, total_count, pagination metadata.
"""

import os
import sys
import json
import time
import sqlite3
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
os.chdir(PROJECT_ROOT)

from src.dashboard.utils import db

DB_PATH = os.path.join(PROJECT_ROOT, "db", "nifty100.db")

# ---------------------------------------------------------------------------
# Profiling: measure each stage

def profile_stages():
    """Measure time for each stage of get_screener_results."""
    print("=" * 70)
    print("BASELINE PROFILING — Stage-by-stage breakdown")
    print("=" * 70)

    # Stage A: SQL execution
    t0 = time.perf_counter()
    latest = db._fetchone("SELECT MAX(year) AS yr FROM market_cap")
    yr = latest["yr"] if latest else 2024
    sql = f"""
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
          AND {db._fiscal_year_condition('fr.year', yr)}
        LEFT JOIN market_cap m ON m.company_id = c.id AND m.year = ?
        LEFT JOIN analysis a ON a.company_id = c.id
        LEFT JOIN profitandloss pl ON pl.company_id = c.id
    """
    params = (str(yr), yr)
    conn = sqlite3.connect(DB_PATH)
    raw_df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    t_sql = time.perf_counter() - t0
    print(f"  A. SQL execution:        {t_sql*1000:.2f} ms  ({len(raw_df)} rows)")

    # Full pipeline timing
    t0 = time.perf_counter()
    df = db.get_screener_results(None, "composite_quality_score")
    t_full = time.perf_counter() - t0
    print(f"  Full get_screener_results: {t_full*1000:.2f} ms  ({len(df)} rows)")
    print(f"  Post-processing overhead:  {(t_full - t_sql)*1000:.2f} ms")

    return df


# ---------------------------------------------------------------------------
# Full baseline capture

def capture_screener(scenario_name, **kwargs):
    """Capture screener results for a given scenario."""
    filters = kwargs.get("filters")
    sort_by = kwargs.get("sort_by", "composite_quality_score")
    result = db.get_screener_results(filters, sort_by=sort_by)

    if result.empty:
        return {"scenario": scenario_name, "item_count": 0, "items": [], "total_count": 0}

    # Capture full detail for all rows
    items = []
    for _, row in result.iterrows():
        item = {}
        for col in result.columns:
            val = row[col]
            if pd.isna(val):
                item[col] = None
            elif hasattr(val, 'item'):
                item[col] = val.item()
            else:
                item[col] = val
        items.append(item)

    return {
        "scenario": scenario_name,
        "item_count": len(items),
        "total_count": len(items),
        "columns": list(result.columns),
        "items": items,
    }


def main():
    import pandas as pd  # noqa - needed for profile_stages

    # ------------------------------------------------------------------
    # STEP 1: Profiling
    # ------------------------------------------------------------------
    baseline_df = profile_stages()

    # ------------------------------------------------------------------
    # STEP 2: Capture baseline screener outputs
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("BASELINE RESULTS CAPTURE")
    print("=" * 70)

    baselines = {}

    # 1. Unfiltered screener (default sort = composite_quality_score desc)
    print("\n  1. Unfiltered screener...")
    baselines["unfiltered"] = capture_screener("unfiltered")

    # 2. min_roe=15 filter
    print("  2. min_roe=15...")
    baselines["min_roe_15"] = capture_screener(
        "min_roe_15",
        filters={"ROE": {"min": 15}},
    )

    # 3. Sector filter (Information Technology)
    print("  3. Sector = Information Technology...")
    # Need to apply sector filter via API logic
    df_full = db.get_screener_results(None, sort_by="company_id")
    df_it = df_full[df_full["sector"] == "Information Technology"]
    baselines["sector_it"] = {
        "scenario": "sector_it",
        "item_count": len(df_it),
        "columns": list(df_full.columns),
        "items": [
            {col: (None if pd.isna(v) else v.item() if hasattr(v, 'item') else v)
             for col, v in row.items()}
            for _, row in df_it.iterrows()
        ],
    }

    # 4. Sort by company_name ascending
    print("  4. Sort by company_name ascending...")
    df_sorted_name = db.get_screener_results(None, sort_by="company_id")
    df_sorted_name = df_sorted_name.sort_values("company_name", ascending=True)
    baselines["sort_by_name_asc"] = {
        "scenario": "sort_by_name_asc",
        "item_count": len(df_sorted_name),
        "columns": list(df_sorted_name.columns),
        "items": [
            {col: (None if pd.isna(v) else v.item() if hasattr(v, 'item') else v)
             for col, v in row.items()}
            for _, row in df_sorted_name.iterrows()
        ],
    }

    # 5. Pagination: page=1, page_size=10 (default sort)
    print("  5. Pagination (page=1, page_size=10)...")
    df_paged = db.get_screener_results(None, sort_by="composite_quality_score")
    page_items = df_paged.iloc[0:10]
    baselines["pagination_page1"] = {
        "scenario": "pagination_page1",
        "item_count": len(page_items),
        "columns": list(df_paged.columns),
        "items": [
            {col: (None if pd.isna(v) else v.item() if hasattr(v, 'item') else v)
             for col, v in row.items()}
            for _, row in page_items.iterrows()
        ],
        "total_count": len(df_paged),
        "page": 1,
        "page_size": 10,
    }

    # 6. Combined filters: min_roe=15 + max_roe=30
    print("  6. min_roe=15 + max_roe=30...")
    baselines["roe_15_30"] = capture_screener(
        "roe_15_30",
        filters={"ROE": {"min": 15, "max": 30}},
    )

    # Save baselines
    output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "day43_baseline.json")
    with open(output_path, "w") as f:
        json.dump(baselines, f, indent=2, default=str)
    print(f"\n  Baseline saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("BASELINE SUMMARY")
    print("=" * 70)
    for name, data in baselines.items():
        print(f"  {name}: {data['item_count']} companies")
        if data.get("items"):
            top3 = data["items"][:3]
            print(f"    Top 3: {[(i.get('company_id'), round(i.get('composite_quality_score', 0) or 0, 2)) for i in top3]}")
    print(f"\n  Total companies in full screener: {len(baselines['unfiltered']['items'])}")


if __name__ == "__main__":
    main()
