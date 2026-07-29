"""
Database utility functions for the Nifty 100 Analytics Dashboard.

All data access goes through this module. No direct Excel reading.
"""

import os
import re
import sqlite3
from typing import Any

import numpy as np
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "nifty100.db")


def _get_conn() -> sqlite3.Connection:
    """Get a read-only SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetchone(query: str, params: tuple = ()) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def _fetchall(query: str, params: tuple = ()) -> list[dict]:
    with _get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def _fetch_df(query: str, params: tuple = ()) -> pd.DataFrame:
    with _get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


# ---------------------------------------------------------------------------
# Existing functions used by other pages
# ---------------------------------------------------------------------------

def get_company_list() -> list[dict]:
    return _fetchall("SELECT id as company_id, company_name FROM companies ORDER BY company_name")


def get_sectors_list() -> list[dict]:
    return _fetchall("SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL ORDER BY broad_sector")


def get_latest_date() -> str | None:
    row = _fetchone("SELECT MAX(year) as yr FROM market_cap")
    return str(row["yr"]) if row and row["yr"] else None


def get_company_profile(company_id: str) -> dict | None:
    sql = """
        SELECT c.id, c.company_name, c.about_company, c.website,
               c.face_value, c.book_value, c.roe_percentage, c.roce_percentage,
               s.broad_sector AS sector, s.sub_sector AS industry,
               m.market_cap_crore AS market_cap_cr
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN market_cap m ON m.company_id = c.id
        WHERE c.id = ?
        GROUP BY c.id
    """
    return _fetchone(sql, (company_id,))


def get_financial_ratios(company_id: str) -> list[dict]:
    sql = """
        SELECT year, net_profit_margin_pct, operating_profit_margin_pct,
               return_on_equity_pct, debt_to_equity, interest_coverage,
               asset_turnover, free_cash_flow_cr, capex_cr,
               earnings_per_share, book_value_per_share,
               dividend_payout_ratio_pct, total_debt_cr, cash_from_operations_cr
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _fetchall(sql, (company_id,))


def get_cashflow_data(company_id: str) -> list[dict]:
    sql = """
        SELECT year, operating_activity, investing_activity,
               financing_activity, net_cash_flow
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _fetchall(sql, (company_id,))


def get_capital_alloc_data(company_id: str) -> list[dict]:
    sql = """
        SELECT year, return_on_equity_pct, debt_to_equity,
               free_cash_flow_cr, total_debt_cr, cash_from_operations_cr
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _fetchall(sql, (company_id,))


# ---------------------------------------------------------------------------
# Home dashboard helpers
# ---------------------------------------------------------------------------

def get_available_years() -> list[int]:
    """Return sorted list of years available in the market_cap table."""
    rows = _fetchall("SELECT DISTINCT year FROM market_cap ORDER BY year")
    return [r["year"] for r in rows if r["year"] is not None]


def _fiscal_year_condition(col: str, year: int) -> str:
    """Return a SQL WHERE snippet that matches a date-string column to a fiscal year."""
    return f"SUBSTR({col}, 1, 4) = ?"


def get_home_kpis(year: int) -> dict[str, Any]:
    """
    Compute the six KPI values for a given year.

    Returns
    -------
    dict with keys:
        avg_roe, median_pe, median_debt_equity, total_companies,
        median_revenue_cagr_5yr, debt_free_companies
        Each value is a float, int, or "N/A".
    """
    result: dict[str, Any] = {}

    # --- Total Companies (distinct in financial_ratios for this year) ---
    row = _fetchone(
        f"SELECT COUNT(DISTINCT company_id) AS cnt FROM financial_ratios WHERE {_fiscal_year_condition('year', year)}",
        (str(year),),
    )
    result["total_companies"] = row["cnt"] if row else 0

    # --- Average ROE (winsorized at P5/P95 to handle data outliers) ---
    rows = _fetchall(
        f"""
        SELECT DISTINCT company_id, return_on_equity_pct
        FROM financial_ratios
        WHERE {_fiscal_year_condition('year', year)}
          AND return_on_equity_pct IS NOT NULL
        """,
        (str(year),),
    )
    roe_vals = np.array([r["return_on_equity_pct"] for r in rows if r["return_on_equity_pct"] is not None])
    if len(roe_vals) > 0:
        p5, p95 = np.percentile(roe_vals, [5, 95])
        clipped = roe_vals.clip(p5, p95)
        result["avg_roe"] = round(float(clipped.mean()), 2)
    else:
        result["avg_roe"] = "N/A"

    # --- Median Debt/Equity (dedup'd by company_id) ---
    rows = _fetchall(
        f"""
        SELECT DISTINCT company_id, debt_to_equity
        FROM financial_ratios
        WHERE {_fiscal_year_condition('year', year)}
          AND debt_to_equity IS NOT NULL
        """,
        (str(year),),
    )
    vals = [r["debt_to_equity"] for r in rows if r["debt_to_equity"] is not None]
    result["median_debt_equity"] = round(float(np.median(vals)), 2) if vals else "N/A"

    # --- Median P/E from market_cap ---
    rows = _fetchall(
        "SELECT pe_ratio FROM market_cap WHERE year = ? AND pe_ratio IS NOT NULL",
        (year,),
    )
    vals = [r["pe_ratio"] for r in rows if r["pe_ratio"] is not None]
    result["median_pe"] = round(float(np.median(vals)), 2) if vals else "N/A"

    # --- Debt-Free Companies (debt_to_equity = 0 or NULL) ---
    row = _fetchone(
        f"""
        SELECT COUNT(DISTINCT company_id) AS cnt
        FROM financial_ratios
        WHERE {_fiscal_year_condition('year', year)}
          AND (debt_to_equity = 0 OR debt_to_equity IS NULL)
        """,
        (str(year),),
    )
    result["debt_free_companies"] = row["cnt"] if row else 0

    # --- Median Revenue CAGR (5yr) from P&L ---
    result["median_revenue_cagr_5yr"] = _compute_median_revenue_cagr(year)

    return result


def _compute_median_revenue_cagr(target_year: int) -> float | str:
    """
    Compute 5-year Revenue CAGR from profitandloss.

    CAGR = (sales_current / sales_5yr_ago) ** (1/5) - 1
    """
    past_year = target_year - 5
    sql = """
        SELECT a.company_id,
               CAST(b.sales AS REAL) AS sales_now,
               CAST(a.sales AS REAL) AS sales_past
        FROM profitandloss a
        JOIN profitandloss b ON a.company_id = b.company_id
        WHERE SUBSTR(a.year, 1, 4) = ?
          AND a.sales IS NOT NULL AND CAST(a.sales AS REAL) > 0
          AND SUBSTR(b.year, 1, 4) = ?
          AND b.sales IS NOT NULL AND CAST(b.sales AS REAL) > 0
    """
    rows = _fetchall(sql, (str(past_year), str(target_year)))
    cagrs = []
    for r in rows:
        s_now = r["sales_now"]
        s_past = r["sales_past"]
        if s_now and s_past and s_past > 0:
            cagr = (s_now / s_past) ** (1.0 / 5.0) - 1.0
            cagrs.append(cagr)
    if not cagrs:
        return "N/A"
    return round(float(np.median(cagrs)) * 100, 2)


def get_sector_distribution(year: int) -> list[dict]:
    """Return company count by sector for the given year."""
    sql = f"""
        SELECT s.broad_sector AS sector, COUNT(DISTINCT s.company_id) AS count
        FROM sectors s
        JOIN financial_ratios fr ON fr.company_id = s.company_id
          AND {_fiscal_year_condition('fr.year', year)}
        WHERE s.broad_sector IS NOT NULL
        GROUP BY s.broad_sector
        ORDER BY count DESC
    """
    return _fetchall(sql, (str(year),))


def get_top_companies(year: int, limit: int = 5) -> list[dict]:
    """
    Return top-N companies by composite quality score for the given year.

    Composite score weights (from screener/engine.py):
      35% profitability (ROE + OPM)
      30% cash quality (FCF + CFO)
      20% growth (CAGR-based)
      15% leverage (D/E, Interest Coverage)
    """
    df = _fetch_df(
        f"""
        SELECT c.id AS company_id, c.company_name,
               s.broad_sector AS sector,
               fr.return_on_equity_pct, fr.operating_profit_margin_pct,
               fr.debt_to_equity, fr.interest_coverage,
               fr.free_cash_flow_cr, fr.cash_from_operations_cr,
               fr.total_debt_cr
        FROM companies c
        JOIN sectors s ON s.company_id = c.id
        JOIN (
            SELECT company_id,
                   MAX(return_on_equity_pct) AS return_on_equity_pct,
                   MAX(operating_profit_margin_pct) AS operating_profit_margin_pct,
                   MAX(debt_to_equity) AS debt_to_equity,
                   MAX(interest_coverage) AS interest_coverage,
                   MAX(free_cash_flow_cr) AS free_cash_flow_cr,
                   MAX(cash_from_operations_cr) AS cash_from_operations_cr,
                   MAX(total_debt_cr) AS total_debt_cr
            FROM financial_ratios
            WHERE {_fiscal_year_condition('year', year)}
            GROUP BY company_id
        ) fr ON fr.company_id = c.id
        """,
        (str(year),),
    )

    if df.empty:
        return []

    df = df.copy()

    # Winsorize & scale helper
    def _scale(s: pd.Series, higher_better: bool = True) -> pd.Series:
        s_num = pd.to_numeric(s, errors="coerce")
        valid = s_num.dropna()
        if len(valid) == 0:
            return pd.Series(np.nan, index=s.index)
        p10 = valid.quantile(0.10)
        p90 = valid.quantile(0.90)
        clipped = s_num.clip(lower=p10, upper=p90)
        mn, mx = clipped.min(), clipped.max()
        if mx == mn:
            return pd.Series(50.0, index=s.index)
        scaled = (clipped - mn) / (mx - mn) * 100.0
        if not higher_better:
            scaled = 100.0 - scaled
        return scaled

    # Sub-scores
    profitability = (
        _scale(df["return_on_equity_pct"], higher_better=True)
        + _scale(df["operating_profit_margin_pct"], higher_better=True)
    ) / 2.0

    cash_quality = (
        _scale(df["free_cash_flow_cr"], higher_better=True)
        + _scale(df["cash_from_operations_cr"], higher_better=True)
    ) / 2.0

    # Growth score: use 5Y revenue CAGR from P&L if available
    growth_scores = _compute_growth_scores_for_year(df["company_id"].tolist(), year)
    df["_growth_score"] = df["company_id"].map(growth_scores).fillna(50.0)

    # Leverage score
    ic_num = pd.to_numeric(df["interest_coverage"], errors="coerce")
    # Treat "Debt Free" as max interest coverage
    debt_free_mask = df["interest_coverage"].apply(
        lambda x: isinstance(x, str) and x.strip().lower() == "debt free"
    )
    if debt_free_mask.any():
        mx = ic_num.max()
        if pd.notna(mx):
            ic_num = ic_num.copy()
            ic_num[debt_free_mask] = mx
    leverage = (
        _scale(df["debt_to_equity"], higher_better=False)
        + _scale(ic_num, higher_better=True)
    ) / 2.0

    composite = (
        0.35 * profitability
        + 0.30 * cash_quality
        + 0.20 * df["_growth_score"]
        + 0.15 * leverage
    )

    df["composite_score"] = composite

    top = df.dropna(subset=["composite_score"]).nlargest(limit, "composite_score")

    return [
        {
            "company": r["company_name"],
            "sector": r["sector"],
            "composite_score": round(r["composite_score"], 1),
        }
        for _, r in top.iterrows()
    ]


def _compute_growth_scores_for_year(company_ids: list[str], target_year: int) -> dict[str, float]:
    """
    Compute 5-year revenue CAGR for the given companies and return
    winsorized-scaled growth scores.
    """
    past_year = target_year - 5
    if not company_ids:
        return {}

    placeholders = ",".join("?" for _ in company_ids)
    sql = f"""
        SELECT a.company_id,
               CAST(b.sales AS REAL) AS sales_now,
               CAST(a.sales AS REAL) AS sales_past
        FROM profitandloss a
        JOIN profitandloss b ON a.company_id = b.company_id
        WHERE a.company_id IN ({placeholders})
          AND SUBSTR(a.year, 1, 4) = ?
          AND a.sales IS NOT NULL AND CAST(a.sales AS REAL) > 0
          AND SUBSTR(b.year, 1, 4) = ?
          AND b.sales IS NOT NULL AND CAST(b.sales AS REAL) > 0
    """
    params = company_ids + [str(past_year), str(target_year)]
    rows = _fetchall(sql, params)

    cagr_map: dict[str, float] = {}
    for r in rows:
        s_now = r["sales_now"]
        s_past = r["sales_past"]
        if s_now and s_past and s_past > 0:
            cagr = (s_now / s_past) ** (1.0 / 5.0) - 1.0
            cagr_map[r["company_id"]] = cagr

    if not cagr_map:
        return {cid: 50.0 for cid in company_ids}

    series = pd.Series(cagr_map)
    p10 = series.quantile(0.10)
    p90 = series.quantile(0.90)
    clipped = series.clip(lower=p10, upper=p90)
    mn, mx = clipped.min(), clipped.max()
    if mx == mn:
        scaled = pd.Series(50.0, index=series.index)
    else:
        scaled = (clipped - mn) / (mx - mn) * 100.0

    result = {cid: 50.0 for cid in company_ids}
    result.update(scaled.to_dict())
    return result


# ---------------------------------------------------------------------------
# Stub / minimal implementations for pages imported via __init__.py
# ---------------------------------------------------------------------------

def get_companies() -> list[dict]:
    """Alias for get_company_list."""
    return get_company_list()


def get_financial_trends(company_id: str) -> list[dict]:
    """Return P&L trend data for a company over all available years."""
    sql = """
        SELECT year, sales, expenses, operating_profit, opm_percentage,
               net_profit, eps
        FROM profitandloss
        WHERE company_id = ? AND year IS NOT NULL
        ORDER BY year ASC
    """
    return _fetchall(sql, (company_id,))


def get_sector_aggregates() -> pd.DataFrame:
    """Return sector-level aggregates across the most recent market_cap year."""
    latest_year_row = _fetchone("SELECT MAX(year) AS yr FROM market_cap")
    if not latest_year_row or not latest_year_row["yr"]:
        return pd.DataFrame()
    yr = latest_year_row["yr"]
    sql = f"""
        SELECT s.broad_sector AS sector,
               COUNT(DISTINCT s.company_id) AS company_count,
               AVG(fr.return_on_equity_pct) AS avg_roe,
               AVG(fr.debt_to_equity) AS avg_debt_equity,
               AVG(m.pe_ratio) AS avg_pe
        FROM sectors s
        JOIN financial_ratios fr ON fr.company_id = s.company_id
          AND {_fiscal_year_condition('fr.year', yr)}
        LEFT JOIN market_cap m ON m.company_id = s.company_id AND m.year = ?
        WHERE s.broad_sector IS NOT NULL
        GROUP BY s.broad_sector
    """
    return _fetch_df(sql, (str(yr), yr))


def get_peer_groups() -> list[dict]:
    """Return distinct peer group names."""
    return _fetchall("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name")


def get_peer_group_members(peer_group_name: str) -> list[dict]:
    """Return company IDs in a peer group."""
    sql = """
        SELECT pg.company_id, c.company_name
        FROM peer_groups pg
        JOIN companies c ON c.id = pg.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY c.company_name
    """
    return _fetchall(sql, (peer_group_name,))


def get_peer_percentiles(company_id: str, peer_group_name: str) -> list[dict]:
    """Compute percentile rankings for a company within its peer group."""
    sql = """
        SELECT pg.company_id, c.company_name,
               fr.return_on_equity_pct, fr.debt_to_equity,
               fr.operating_profit_margin_pct, fr.interest_coverage,
               m.pe_ratio
        FROM peer_groups pg
        JOIN companies c ON c.id = pg.company_id
        JOIN financial_ratios fr ON fr.company_id = pg.company_id
        LEFT JOIN market_cap m ON m.company_id = pg.company_id
        WHERE pg.peer_group_name = ?
          AND fr.year = (SELECT MAX(fr2.year) FROM financial_ratios fr2 WHERE fr2.company_id = pg.company_id)
    """
    rows = _fetchall(sql, (peer_group_name,))
    if not rows:
        return []

    df = pd.DataFrame(rows)
    metrics = ["return_on_equity_pct", "debt_to_equity", "operating_profit_margin_pct", "interest_coverage", "pe_ratio"]

    result_rows = []
    for _, r in df.iterrows():
        row: dict = {"company_id": r["company_id"], "company_name": r["company_name"]}
        for m in metrics:
            vals = df[m].dropna()
            if len(vals) > 0:
                pct_rank = (vals < r[m]).sum() / len(vals) * 100 if pd.notna(r[m]) else None
                row[m] = round(pct_rank, 1) if pct_rank is not None else None
            else:
                row[m] = None
        result_rows.append(row)

    return result_rows


def get_screener_results(filters: dict | None = None, sort_by: str = "company_id") -> pd.DataFrame:
    """Return screener results for the most recent year."""
    latest = _fetchone("SELECT MAX(year) AS yr FROM market_cap")
    yr = latest["yr"] if latest else 2024
    sql = f"""
        SELECT c.id AS company_id, c.company_name,
               s.broad_sector AS sector,
               fr.return_on_equity_pct, fr.debt_to_equity,
               fr.operating_profit_margin_pct, fr.interest_coverage,
               fr.free_cash_flow_cr, fr.cash_from_operations_cr,
               fr.net_profit_margin_pct
        FROM companies c
        JOIN sectors s ON s.company_id = c.id
        JOIN financial_ratios fr ON fr.company_id = c.id
          AND {_fiscal_year_condition('fr.year', yr)}
    """
    df = _fetch_df(sql, (str(yr),))
    if not df.empty and filters:
        for col, (op, val) in filters.items():
            if col in df.columns:
                if op == "gt":
                    df = df[df[col] > val]
                elif op == "lt":
                    df = df[df[col] < val]
                elif op == "between":
                    df = df[df[col].between(val[0], val[1])]
    if not df.empty:
        df = df.sort_values(sort_by, ascending=False)
    return df


def get_preset_filters() -> list[dict]:
    """Return list of preset screener filter names."""
    return [
        {"name": "Quality Compounder"},
        {"name": "Value Pick"},
        {"name": "Growth Accelerator"},
        {"name": "Dividend Champion"},
        {"name": "Debt Free Blue Chip"},
        {"name": "Turnaround Watch"},
    ]


def get_ratios(company_id: str) -> list[dict]:
    """Alias for get_financial_ratios."""
    return get_financial_ratios(company_id)


def get_pl(company_id: str) -> list[dict]:
    """Return P&L data for a company."""
    sql = """
        SELECT year, sales, expenses, operating_profit, opm_percentage,
               other_income, interest, depreciation, profit_before_tax,
               tax_percentage, net_profit, eps, dividend_payout
        FROM profitandloss
        WHERE company_id = ? AND year IS NOT NULL
        ORDER BY year DESC
    """
    return _fetchall(sql, (company_id,))


def get_bs(company_id: str) -> list[dict]:
    """Return balance sheet data for a company."""
    sql = """
        SELECT year, equity_capital, reserves, borrowings,
               other_liabilities, total_liabilities,
               fixed_assets, cwip, investments, other_asset, total_assets
        FROM balancesheet
        WHERE company_id = ? AND year IS NOT NULL
        ORDER BY year DESC
    """
    return _fetchall(sql, (company_id,))


def get_cf(company_id: str) -> list[dict]:
    """Alias for get_cashflow_data."""
    return get_cashflow_data(company_id)


def get_sectors() -> list[dict]:
    """Return all sector mappings."""
    return _fetchall(
        """SELECT s.company_id, c.company_name, s.broad_sector, s.sub_sector
           FROM sectors s
           JOIN companies c ON c.id = s.company_id
           ORDER BY s.broad_sector, c.company_name"""
    )


def get_peers(company_id: str) -> list[dict]:
    """Return peer group info for a company."""
    sql = """
        SELECT pg.peer_group_name, pg.company_id AS peer_company_id,
               c.company_name AS peer_company_name
        FROM peer_groups pg
        JOIN companies c ON c.id = pg.company_id
        WHERE pg.peer_group_name IN (
            SELECT peer_group_name FROM peer_groups WHERE company_id = ?
        )
        ORDER BY pg.peer_group_name, c.company_name
    """
    return _fetchall(sql, (company_id,))


def get_valuation(company_id: str) -> list[dict]:
    """Return valuation data for a company."""
    sql = """
        SELECT year, market_cap_crore, enterprise_value_crore,
               pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _fetchall(sql, (company_id,))