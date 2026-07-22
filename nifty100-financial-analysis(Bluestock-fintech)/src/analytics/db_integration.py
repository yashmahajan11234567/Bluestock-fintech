"""
Database integration for financial ratio computations.

Populates the financial_ratios table by reading raw financial data
from the existing database and computing ratios using the analytics modules.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure src/ is on the path for analytics imports
_src_path = str(Path(__file__).resolve().parents[2])
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Import analytics functions directly
import importlib.util

def _load_module(module_name, file_name):
    path = Path(_src_path) / "src" / "analytics" / file_name
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_ratios = _load_module("analytics.ratios", "ratios.py")
_cashflow_mod = _load_module("analytics.cashflow", "cashflow.py")

net_profit_margin = _ratios.net_profit_margin
operating_profit_margin = _ratios.operating_profit_margin
return_on_equity = _ratios.return_on_equity
return_on_capital_employed = _ratios.return_on_capital_employed
return_on_assets = _ratios.return_on_assets
debt_to_equity = _ratios.debt_to_equity
interest_coverage_ratio = _ratios.interest_coverage_ratio
asset_turnover = _ratios.asset_turnover

free_cash_flow = _cashflow_mod.free_cash_flow


def get_raw_financial_rows(
    conn: sqlite3.Connection,
) -> List[Dict[str, Any]]:
    """
    Query all financial data rows from the database.

    Joins profitandloss, balancesheet, and cashflow tables by company_id
    to build the raw input dictionaries needed for ratio computation.

    Args:
        conn: Active SQLite database connection.

    Returns:
        List of dictionaries, each containing raw financial values for one
        company/year combination.
    """
    query = """
        SELECT
            p.company_id,
            p.year,
            p.sales,
            p.net_profit,
            p.operating_profit,
            p.other_income,
            p.interest,
            p.eps,
            p.dividend_payout,
            b.equity_capital,
            b.reserves,
            b.borrowings,
            b.total_assets,
            b.investments,
            c.operating_activity AS operating_cashflow,
            c.investing_activity AS investing_activity,
            comp.book_value
        FROM profitandloss p
        LEFT JOIN balancesheet b
            ON p.company_id = b.company_id
            AND (p.year IS NULL OR p.year = b.year OR b.year IS NULL)
        LEFT JOIN cashflow c
            ON p.company_id = c.company_id
            AND (p.year IS NULL OR p.year = c.year OR c.year IS NULL)
        LEFT JOIN companies comp
            ON p.company_id = comp.id
        WHERE p.company_id IS NOT NULL
    """

    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.row_factory = None
    return rows


def compute_row_metrics(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute all financial metrics for a single raw data row.

    Args:
        row: Dictionary of raw financial data from the database.

    Returns:
        Dictionary of computed financial metrics for insertion.
    """
    company_id = row.get("company_id")
    year = row.get("year")
    net_profit = row.get("net_profit")
    sales = row.get("sales")
    operating_profit = row.get("operating_profit")
    equity_capital = row.get("equity_capital")
    reserves = row.get("reserves")
    borrowings = row.get("borrowings")
    total_assets = row.get("total_assets")
    other_income = row.get("other_income")
    interest = row.get("interest")
    investments = row.get("investments")
    operating_cashflow = row.get("operating_cashflow")
    investing_activity = row.get("investing_activity")
    eps = row.get("eps")
    book_value = row.get("book_value")
    dividend_payout = row.get("dividend_payout")

    # Capital expenditure = -investing_activity (negative = outflow)
    capital_expenditure = -investing_activity if investing_activity is not None else None

    # Compute ratios using the analytics modules
    npm = operating_profit_margin(net_profit, sales)
    opm = operating_profit_margin(operating_profit, sales)
    roe = return_on_equity(net_profit, equity_capital, reserves)
    dte = debt_to_equity(borrowings, equity_capital, reserves)
    icr = interest_coverage_ratio(operating_profit, other_income, interest)
    at = asset_turnover(sales, total_assets)
    fcf = free_cash_flow(operating_cashflow, capital_expenditure)

    return {
        "company_id": company_id,
        "year": year,
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": opm,
        "return_on_equity_pct": roe,
        "debt_to_equity": dte,
        "interest_coverage": icr,
        "asset_turnover": at,
        "free_cash_flow_cr": fcf,
        "capex_cr": capital_expenditure,
        "earnings_per_share": eps,
        "book_value_per_share": book_value,
        "dividend_payout_ratio_pct": dividend_payout,
        "total_debt_cr": borrowings,
        "cash_from_operations_cr": operating_cashflow,
    }


def populate_financial_ratios(
    conn: sqlite3.Connection,
    dry_run: bool = False,
) -> int:
    """
    Read raw financial data, compute ratios, and populate financial_ratios table.

    Uses the existing financial_ratios table schema and replaces all data
    with fresh computations. The table is cleared before inserting new rows.

    Args:
        conn: Active SQLite database connection.
        dry_run: If True, only return row count without inserting.

    Returns:
        Number of rows inserted (or would be inserted in dry run mode).
    """
    rows = get_raw_financial_rows(conn)
    metrics_list = []

    for row in rows:
        metrics = compute_row_metrics(row)
        metrics_list.append(metrics)

    if dry_run:
        return len(metrics_list)

    # Clear existing data
    conn.execute("DELETE FROM financial_ratios")

    # Insert new data
    placeholders = ",".join(["?"] * len(financial_ratios_columns()))
    columns = financial_ratios_columns()
    sql = f"INSERT INTO financial_ratios ({','.join(columns)}) VALUES ({placeholders})"

    for metrics in metrics_list:
        values = [metrics.get(col) for col in columns]
        conn.execute(sql, values)

    conn.commit()
    return len(metrics_list)


def financial_ratios_columns() -> List[str]:
    """
    Return the list of column names for the financial_ratios table.

    Excludes the auto-increment 'id' column.
    """
    return [
        "company_id",
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
    ]