"""Day 43 EXPLAIN QUERY PLAN analysis."""
import os
import sys
import time
import sqlite3

# Don't chdir; the shell script handles cd
conn = sqlite3.connect('db/nifty100.db')
conn.row_factory = sqlite3.Row

# Get latest year
latest = conn.execute("SELECT MAX(year) AS yr FROM market_cap").fetchone()
yr = latest["yr"] if latest and latest["yr"] else 2024
print(f"Latest market_cap year: {yr}")

# --- Screener query QEP ---
print("\n=== SCREENER QUERY PLAN ===")
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
for step in plan:
    print(f"  {dict(step)}")

# Measure timing
t0 = time.perf_counter()
for _ in range(10):
    conn.execute(screener_sql, (yr,)).fetchall()
screener_ms = (time.perf_counter() - t0) / 10 * 1000
print(f"  Screener query timing (avg of 10): {screener_ms:.2f} ms")

# --- Company profile query QEP ---
print("\n=== COMPANY PROFILE QUERY PLAN ===")
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
for step in plan:
    print(f"  {dict(step)}")

t0 = time.perf_counter()
for _ in range(100):
    conn.execute(profile_sql, ("TCS",)).fetchone()
profile_ms = (time.perf_counter() - t0) / 100 * 1000
print(f"  Profile query timing (avg of 100): {profile_ms:.2f} ms")

# --- Financial ratios query QEP ---
print("\n=== FINANCIAL RATIOS QUERY PLAN ===")
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
for step in plan:
    print(f"  {dict(step)}")

t0 = time.perf_counter()
for _ in range(100):
    conn.execute(ratios_sql, ("TCS",)).fetchall()
ratios_ms = (time.perf_counter() - t0) / 100 * 1000
print(f"  Ratios query timing (avg of 100): {ratios_ms:.2f} ms")

# --- Cashflow query QEP ---
print("\n=== CASHFLOW QUERY PLAN ===")
cf_sql = """
    SELECT CAST(year AS INTEGER) AS year, operating_activity, investing_activity,
           financing_activity, net_cash_flow
    FROM cashflow
    WHERE company_id = ?
    ORDER BY year DESC
"""
plan = conn.execute("EXPLAIN QUERY PLAN " + cf_sql, ("TCS",)).fetchall()
for step in plan:
    print(f"  {dict(step)}")

t0 = time.perf_counter()
for _ in range(100):
    conn.execute(cf_sql, ("TCS",)).fetchall()
cf_ms = (time.perf_counter() - t0) / 100 * 1000
print(f"  Cashflow query timing (avg of 100): {cf_ms:.2f} ms")

# --- Check for full table scans ---
print("\n=== FULL TABLE SCAN CHECK ===")
print("Checking if any queries do full table scans (SCAN TABLE without USING INDEX)...")
all_plans = {
    "screener": screener_sql + f" (params: year={yr})",
    "profile": profile_sql + " (params: TCS)",
    "ratios": ratios_sql + " (params: TCS)",
    "cashflow": cf_sql + " (params: TCS)",
}

conn.close()
print("\nDone.")
