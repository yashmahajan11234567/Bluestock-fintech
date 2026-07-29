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


# ---------------------------------------------------------------------------
# FIX 1: Company Profile
# ---------------------------------------------------------------------------

def get_company_profile(company_id: str) -> dict | None:
    """
    Return company profile including symbol/ticker (company_id), sector, industry, market cap, etc.

    Returns
    -------
    dict with keys: company_id (symbol), company_name, about_company, website,
                    face_value, book_value, sector, industry, market_cap_cr,
                    roe_percentage, roce_percentage
    """
    sql = """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.about_company,
            c.website,
            c.face_value,
            c.book_value,
            c.roe_percentage,
            c.roce_percentage AS return_on_capital_employed_pct,
            s.broad_sector AS sector,
            s.sub_sector AS industry,
            m.market_cap_crore AS market_cap_cr
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        LEFT JOIN market_cap m ON m.company_id = c.id
        WHERE c.id = ?
        GROUP BY c.id
    """
    return _fetchone(sql, (company_id,))


def get_financial_ratios(company_id: str) -> pd.DataFrame:
    """
    Return financial ratios for a company as a DataFrame.

    Deduplicates to one row per company per year.
    Includes ROCE from companies table.

    Returns
    -------
    pd.DataFrame with columns: year, net_profit_margin_pct, operating_profit_margin_pct,
        return_on_equity_pct, return_on_capital_employed_pct, debt_to_equity,
        interest_coverage, asset_turnover, free_cash_flow_cr, capex_cr,
        earnings_per_share, book_value_per_share, dividend_payout_ratio_pct,
        total_debt_cr, cash_from_operations_cr
    Year is integer.
    """
    sql = """
        SELECT
            CAST(fr.year AS INTEGER) AS year,
            fr.net_profit_margin_pct,
            fr.operating_profit_margin_pct,
            fr.return_on_equity_pct,
            c.roce_percentage AS return_on_capital_employed_pct,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.asset_turnover,
            fr.free_cash_flow_cr,
            fr.capex_cr,
            fr.earnings_per_share,
            fr.book_value_per_share,
            fr.dividend_payout_ratio_pct,
            fr.total_debt_cr,
            fr.cash_from_operations_cr
        FROM financial_ratios fr
        JOIN companies c ON c.id = fr.company_id
        WHERE fr.company_id = ?
        ORDER BY fr.year DESC
    """
    df = _fetch_df(sql, (company_id,))
    # Ensure year is integer
    if not df.empty:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        # Deduplicate: keep first row per year
        df = df.drop_duplicates(subset=["year"], keep="first")
    return df


def get_cashflow_data(company_id: str) -> pd.DataFrame:
    """Return cash flow data for a company as a DataFrame."""
    sql = """
        SELECT CAST(year AS INTEGER) AS year, operating_activity, investing_activity,
               financing_activity, net_cash_flow
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year DESC
    """
    df = _fetch_df(sql, (company_id,))
    # Ensure year is nullable integer (Int64) to handle any NaN values
    if not df.empty:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def get_capital_alloc_data(company_id: str) -> pd.DataFrame:
    """
    Return capital allocation data for a company as a DataFrame.

    Deduplicates to one row per company per year.

    Returns
    -------
    pd.DataFrame with columns: year, return_on_equity_pct, debt_to_equity,
        free_cash_flow_cr, total_debt_cr, cash_from_operations_cr,
        return_on_capital_employed_pct, cash_conversion_ratio
        Year is integer.
    """
    sql = """
        SELECT
            CAST(fr.year AS INTEGER) AS year,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.total_debt_cr,
            fr.cash_from_operations_cr,
            c.roce_percentage AS return_on_capital_employed_pct,
            CASE
                WHEN pl.net_profit IS NOT NULL AND pl.net_profit > 0
                THEN CAST(fr.cash_from_operations_cr AS REAL) / CAST(pl.net_profit AS REAL)
                ELSE NULL
            END AS cash_conversion_ratio
        FROM financial_ratios fr
        JOIN companies c ON c.id = fr.company_id
        LEFT JOIN profitandloss pl
            ON pl.company_id = fr.company_id
            AND CAST(pl.year AS INTEGER) = CAST(fr.year AS INTEGER)
        WHERE fr.company_id = ?
        ORDER BY fr.year DESC
    """
    df = _fetch_df(sql, (company_id,))
    # Ensure year is integer
    if not df.empty:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        # Drop rows with null year
        df = df.dropna(subset=["year"])
        # Deduplicate: keep first row per year
        df = df.drop_duplicates(subset=["year"], keep="first")
    return df


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
    dict with keys: avg_roe, median_pe, median_debt_equity, total_companies,
                    median_revenue_cagr_5yr, debt_free_companies
                    Each value is float, int, or "N/A".
    """
    result: dict[str, Any] = {}

    # --- Total Companies (distinct in financial_ratios for this year) ---
    row = _fetchone(
        f"SELECT COUNT(DISTINCT company_id) AS cnt FROM financial_ratios WHERE {_fiscal_year_condition('year', year)}",
        (str(year),),
    )
    result["total_companies"] = row["cnt"] if row else 0

    # --- Average ROE (winsorized at P5/P95) ---
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
    """Compute 5-year Revenue CAGR from profitandloss."""
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

    Composite score weights:
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
    """Compute 5-year revenue CAGR for the given companies and return winsorized-scaled growth scores."""
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
# FIX 2: Screener
# ---------------------------------------------------------------------------

def get_screener_results(filters: dict | None = None, sort_by: str = "company_id") -> pd.DataFrame:
    """
    Return screener results for the most recent year.

    Accepts filters in {"ROE": {"min": 15, "max": 30}} format (min/max keys).

    Returns
    -------
    pd.DataFrame with columns: company_id, company_name, sector,
        return_on_equity_pct, debt_to_equity, operating_profit_margin_pct,
        interest_coverage, free_cash_flow_cr, cash_from_operations_cr,
        net_profit_margin_pct, compounded_sales_growth, compounded_profit_growth,
        dividend_yield_pct, pe_ratio, pb_ratio, net_profit,
        composite_quality_score, sector_relative_score
    """
    latest = _fetchone("SELECT MAX(year) AS yr FROM market_cap")
    yr = latest["yr"] if latest else 2024
    sql = f"""
        SELECT c.id AS company_id, c.company_name,
               s.broad_sector AS sector,
               fr.return_on_equity_pct, fr.debt_to_equity,
               fr.operating_profit_margin_pct, fr.interest_coverage,
               fr.free_cash_flow_cr, fr.cash_from_operations_cr,
               fr.net_profit_margin_pct,
               m.pe_ratio, m.pb_ratio, m.dividend_yield_pct,
               a.compounded_sales_growth, a.compounded_profit_growth,
               pl.net_profit
        FROM companies c
        JOIN sectors s ON s.company_id = c.id
        JOIN financial_ratios fr ON fr.company_id = c.id
          AND {_fiscal_year_condition('fr.year', yr)}
        LEFT JOIN market_cap m ON m.company_id = c.id AND m.year = ?
        LEFT JOIN analysis a ON a.company_id = c.id
        LEFT JOIN profitandloss pl ON pl.company_id = c.id
    """
    df = _fetch_df(sql, (str(yr), yr))
    if df.empty:
        return df

    # Parse CAGR strings ("10 Years: 21%" -> 21.0)
    for col in ["compounded_sales_growth", "compounded_profit_growth"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.extract(r"(\d+\.?\d*)%?", expand=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Deduplicate: keep first row per company for tables with multiple rows
    for col in ["net_profit", "compounded_sales_growth", "compounded_profit_growth"]:
        if col in df.columns:
            df[col] = df.groupby("company_id", sort=False)[col].transform("first")
    df = df.drop_duplicates(subset=["company_id"], keep="first")

    # --- Compute composite scores (replicating engine.py logic) ---
    def _winsorize_scale(s, higher_better=True):
        s = pd.to_numeric(s, errors="coerce")
        valid = s.dropna()
        if len(valid) == 0:
            return pd.Series(np.nan, index=s.index)
        p10, p90 = valid.quantile([0.10, 0.90])
        clipped = s.clip(lower=p10, upper=p90)
        mn, mx = clipped.min(), clipped.max()
        if mx == mn:
            return pd.Series(50.0, index=s.index)
        scaled = (clipped - mn) / (mx - mn) * 100.0
        if not higher_better:
            scaled = 100.0 - scaled
        return scaled

    # Profitability (35%)
    roe_s = _winsorize_scale(df["return_on_equity_pct"], True)
    npm_s = _winsorize_scale(df["net_profit_margin_pct"], True)
    profitability = 0.6 * roe_s + 0.4 * npm_s

    # Cash Quality (30%)
    fcf_s = _winsorize_scale(df["free_cash_flow_cr"], True)
    cfo = pd.to_numeric(df["cash_from_operations_cr"], errors="coerce")
    pat = pd.to_numeric(df["net_profit"], errors="coerce").replace(0, np.nan)
    cfo_pat = (cfo / pat).replace([np.inf, -np.inf], np.nan)
    cfo_pat_s = _winsorize_scale(cfo_pat, True)
    fcf_pos = (pd.to_numeric(df["free_cash_flow_cr"], errors="coerce") > 0).astype(float) * 100.0
    cash_quality = 0.5 * fcf_s + (1/3) * cfo_pat_s + (1/6) * fcf_pos

    # Growth (20%)
    rev_cagr_s = _winsorize_scale(df["compounded_sales_growth"], True)
    pat_cagr_s = _winsorize_scale(df["compounded_profit_growth"], True)
    growth = 0.5 * rev_cagr_s + 0.5 * pat_cagr_s

    # Leverage (15%)
    de_s = _winsorize_scale(df["debt_to_equity"], False)
    ic = df["interest_coverage"].apply(
        lambda x: float("nan") if pd.isna(x) else (
            df["interest_coverage"].max() if isinstance(x, str) and "debt free" in x.strip().lower()
            else pd.to_numeric(x, errors="coerce")
        )
    )
    ic_s = _winsorize_scale(ic, True)
    leverage = (2/3) * de_s + (1/3) * ic_s

    # Composite
    df["composite_quality_score"] = (
        0.35 * profitability + 0.30 * cash_quality + 0.20 * growth + 0.15 * leverage
    )

    # Sector-relative score
    sector_scores = df.groupby("sector", group_keys=False, sort=False).apply(
        lambda g: (
            0.35 * (0.6 * _winsorize_scale(g["return_on_equity_pct"], True)
                    + 0.4 * _winsorize_scale(g["net_profit_margin_pct"], True))
            + 0.30 * (0.5 * _winsorize_scale(g["free_cash_flow_cr"], True)
                      + (1/3) * _winsorize_scale(
                          pd.to_numeric(g["cash_from_operations_cr"], errors="coerce")
                          / pd.to_numeric(g["net_profit"], errors="coerce").replace(0, np.nan), True)
                      + (1/6) * (pd.to_numeric(g["free_cash_flow_cr"], errors="coerce") > 0).astype(float) * 100.0)
            + 0.20 * (0.5 * _winsorize_scale(g["compounded_sales_growth"], True)
                      + 0.5 * _winsorize_scale(g["compounded_profit_growth"], True))
            + 0.15 * ((2/3) * _winsorize_scale(g["debt_to_equity"], False)
                      + (1/3) * _winsorize_scale(g["interest_coverage"], True))
        ),
        include_groups=False
    )
    if len(sector_scores) == len(df):
        df["sector_relative_score"] = sector_scores.values
    else:
        df["sector_relative_score"] = np.nan

    # --- Apply filters ({"ROE": {"min": 15, "max": 30}} format) ---
    FILTER_COLUMN_MAP = {
        "ROE": "return_on_equity_pct",
        "Free Cash Flow": "free_cash_flow_cr",
        "Revenue CAGR": "compounded_sales_growth",
        "PAT CAGR": "compounded_profit_growth",
        "Dividend Yield": "dividend_yield_pct",
        "Debt to Equity": "debt_to_equity",
        "PE": "pe_ratio",
        "PB": "pb_ratio",
        "Interest Coverage": "interest_coverage",
        "Market Cap": "market_cap_crore",
    }

    if filters:
        for display_name, condition in filters.items():
            col = FILTER_COLUMN_MAP.get(display_name, display_name)
            if col not in df.columns:
                continue
            if "min" in condition:
                min_val = condition["min"]
                if min_val is not None:
                    df = df[pd.to_numeric(df[col], errors="coerce") >= min_val]
            if "max" in condition:
                max_val = condition["max"]
                if max_val is not None:
                    df = df[pd.to_numeric(df[col], errors="coerce") <= max_val]

    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=False)

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")

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


# ---------------------------------------------------------------------------
# FIX 3: Peer Comparison
# ---------------------------------------------------------------------------

def get_peer_groups(company_id: str | None = None) -> list[dict] | str:
    """
    Return peer group name for a company, or list of all peer groups.

    Parameters
    ----------
    company_id : str, optional
        If provided, returns the peer group name for that company as a string.
        If None, returns list of all distinct peer group names.

    Returns
    -------
    str or list[dict]
        Peer group name string when company_id is given,
        list of dicts with 'peer_group_name' key otherwise.
    """
    if company_id:
        row = _fetchone(
            "SELECT peer_group_name FROM peer_groups WHERE company_id = ?",
            (company_id,),
        )
        return row["peer_group_name"] if row else ""
    return _fetchall("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name")


def get_peer_percentiles(company_id: str) -> dict:
    """
    Compute percentile rankings for a company within its peer group.

    Restricted to the selected peer group only.

    Returns
    -------
    dict with keys: roe_percentile, net_profit_margin_percentile, debt_to_equity_percentile,
                    free_cash_flow_percentile, pe_percentile, pb_percentile,
                    overall_peer_score, peer_group_name
    """
    # Find this company's peer group
    peer_row = _fetchone(
        "SELECT peer_group_name FROM peer_groups WHERE company_id = ?",
        (company_id,),
    )
    if not peer_row:
        return {"overall_peer_score": None}
    peer_group_name = peer_row["peer_group_name"]

    # Get latest year
    latest = _fetchone("SELECT MAX(year) AS yr FROM market_cap")
    yr = latest["yr"] if latest else 2024

    # Get all companies in THIS peer group with their financial data
    sql = """
        SELECT pg.company_id, c.company_name,
               fr.return_on_equity_pct, fr.net_profit_margin_pct,
               fr.debt_to_equity, fr.operating_profit_margin_pct,
               fr.interest_coverage, fr.free_cash_flow_cr,
               m.pe_ratio, m.pb_ratio, m.dividend_yield_pct
        FROM peer_groups pg
        JOIN companies c ON c.id = pg.company_id
        JOIN financial_ratios fr ON fr.company_id = pg.company_id
            AND CAST(fr.year AS INTEGER) = ?
        LEFT JOIN market_cap m ON m.company_id = pg.company_id AND m.year = ?
        WHERE pg.peer_group_name = ?
    """
    rows = _fetchall(sql, (yr, yr, peer_group_name))
    if not rows:
        return {"overall_peer_score": None}

    df = pd.DataFrame(rows)

    # Metrics to compute percentiles for
    METRICS = {
        "return_on_equity_pct": "roe_percentile",
        "net_profit_margin_pct": "net_profit_margin_percentile",
        "debt_to_equity": "debt_to_equity_percentile",
        "free_cash_flow_cr": "free_cash_flow_percentile",
        "pe_ratio": "pe_percentile",
        "pb_ratio": "pb_percentile",
    }
    LOWER_BETTER = {"debt_to_equity_percentile", "pe_percentile", "pb_percentile"}

    # Find the target company row
    company_row = df[df["company_id"] == company_id]
    if company_row.empty:
        return {"overall_peer_score": None}
    company_idx = company_row.index[0]

    # Compute percentiles
    result = {"peer_group_name": peer_group_name}
    for metric_col, pct_col in METRICS.items():
        if metric_col not in df.columns:
            continue
        vals = pd.to_numeric(df[metric_col], errors="coerce")
        valid = vals.dropna()
        if len(valid) == 0 or pd.isna(vals.iloc[company_idx]):
            result[pct_col] = None
            continue
        pct = (valid < vals.iloc[company_idx]).sum() / len(valid) * 100
        if pct_col in LOWER_BETTER:
            pct = 100 - pct
        result[pct_col] = round(pct, 1)

    # Overall peer score: average of all available percentiles
    pct_values = [v for k, v in result.items() if k.endswith("_percentile") and v is not None]
    result["overall_peer_score"] = round(sum(pct_values) / len(pct_values), 1) if pct_values else None

    return result


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


# ---------------------------------------------------------------------------
# FIX 4: Financial Trends
# ---------------------------------------------------------------------------

def get_financial_trends(company_id: str) -> pd.DataFrame:
    """
    Return P&L trend data for a company over all available years.

    Deduplicates to one row per company per year.

    Returns
    -------
    pd.DataFrame with columns: year, sales, expenses, operating_profit,
        operating_profit_margin_pct, net_profit, eps, return_on_equity_pct,
        debt_to_equity, free_cash_flow_cr, net_profit_margin_pct
    Year is integer.
    """
    sql = """
        SELECT
            CAST(pl.year AS INTEGER) AS year,
            pl.sales,
            pl.expenses,
            pl.operating_profit,
            pl.opm_percentage AS operating_profit_margin_pct,
            pl.net_profit,
            pl.eps,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.net_profit_margin_pct
        FROM profitandloss pl
        LEFT JOIN financial_ratios fr
            ON fr.company_id = pl.company_id
            AND CAST(fr.year AS INTEGER) = CAST(pl.year AS INTEGER)
        WHERE pl.company_id = ? AND pl.year IS NOT NULL
        ORDER BY year ASC
    """
    df = _fetch_df(sql, (company_id,))
    # Ensure year is integer
    if not df.empty:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        # Deduplicate: keep first row per year
        df = df.drop_duplicates(subset=["year"], keep="first")
    return df


# ---------------------------------------------------------------------------
# FIX 5: Sector Analysis
# ---------------------------------------------------------------------------

def get_sector_aggregates() -> pd.DataFrame:
    """
    Return sector-level aggregates across the most recent market_cap year.

    Returns
    -------
    pd.DataFrame with columns: sector, company_count, avg_roe_pct, avg_roce_pct,
        avg_debt_to_equity, avg_net_profit_margin_pct, avg_pe_ratio, total_market_cap_cr
    """
    latest_year_row = _fetchone("SELECT MAX(year) AS yr FROM market_cap")
    if not latest_year_row or not latest_year_row["yr"]:
        return pd.DataFrame()
    yr = latest_year_row["yr"]
    sql = f"""
        SELECT
            s.broad_sector AS sector,
            COUNT(DISTINCT s.company_id) AS company_count,
            ROUND(AVG(fr.return_on_equity_pct), 2) AS avg_roe_pct,
            ROUND(AVG(c.roce_percentage), 2) AS avg_roce_pct,
            ROUND(AVG(fr.debt_to_equity), 2) AS avg_debt_to_equity,
            ROUND(AVG(fr.net_profit_margin_pct), 2) AS avg_net_profit_margin_pct,
            ROUND(AVG(m.pe_ratio), 2) AS avg_pe_ratio,
            ROUND(SUM(m.market_cap_crore), 2) AS total_market_cap_cr
        FROM sectors s
        JOIN financial_ratios fr ON fr.company_id = s.company_id
          AND {_fiscal_year_condition('fr.year', yr)}
        JOIN companies c ON c.id = s.company_id
        LEFT JOIN market_cap m ON m.company_id = s.company_id AND m.year = ?
        WHERE s.broad_sector IS NOT NULL
        GROUP BY s.broad_sector
    """
    return _fetch_df(sql, (str(yr), yr))


# ---------------------------------------------------------------------------
# Aliases for backward compatibility
# ---------------------------------------------------------------------------

def get_companies() -> list[dict]:
    """Alias for get_company_list."""
    return get_company_list()


def get_ratios(company_id: str) -> pd.DataFrame:
    """Alias for get_financial_ratios returning DataFrame."""
    return get_financial_ratios(company_id)


def get_pl(company_id: str) -> pd.DataFrame:
    """Return P&L data for a company as DataFrame."""
    sql = """
        SELECT CAST(year AS INTEGER) AS year, sales, expenses, operating_profit, opm_percentage,
               other_income, interest, depreciation, profit_before_tax,
               tax_percentage, net_profit, eps, dividend_payout
        FROM profitandloss
        WHERE company_id = ? AND year IS NOT NULL
        ORDER BY year DESC
    """
    return _fetch_df(sql, (company_id,))


def get_bs(company_id: str) -> pd.DataFrame:
    """Return balance sheet data for a company as DataFrame."""
    sql = """
        SELECT CAST(year AS INTEGER) AS year, equity_capital, reserves, borrowings,
               other_liabilities, total_liabilities,
               fixed_assets, cwip, investments, other_asset, total_assets
        FROM balancesheet
        WHERE company_id = ? AND year IS NOT NULL
        ORDER BY year DESC
    """
    return _fetch_df(sql, (company_id,))


def get_cf(company_id: str) -> pd.DataFrame:
    """Alias for get_cashflow_data returning DataFrame."""
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


def get_valuation(company_id: str) -> pd.DataFrame:
    """Return valuation data for a company as DataFrame."""
    sql = """
        SELECT CAST(year AS INTEGER) AS year, market_cap_crore, enterprise_value_crore,
               pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year DESC
    """
    return _fetch_df(sql, (company_id,))