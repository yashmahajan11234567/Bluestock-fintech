"""
Validation script for the financial data warehouse.
Runs data quality checks on the SQLite database and outputs a CSV report.
"""

import sqlite3
import sys
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]  # project root
DB_PATH = BASE_DIR / "db" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV = OUTPUT_DIR / "validation_failures.csv"


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_table_names(conn):
    """Return a list of table names in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]


def get_column_names(conn, table_name):
    """Return a list of column names for a given table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    return [row[1] for row in cursor.fetchall()]


def execute_query(conn, query, parameters=()):
    """Execute a query and return the results as a list of tuples."""
    cursor = conn.cursor()
    cursor.execute(query, parameters)
    return cursor.fetchall()


# ----------------------------------------------------------------------
# Validation functions
# ----------------------------------------------------------------------
def check_primary_key_uniqueness(conn):
    """DQ-01: Check that primary keys are unique in each table."""
    failures = []
    tables = get_table_names(conn)
    for table in tables:
        query = f"""
            SELECT id, COUNT(*) as cnt
            FROM {table}
            GROUP BY id
            HAVING cnt > 1
        """
        rows = execute_query(conn, query)
        for row in rows:
            pk_value, count = row
            failures.append({
                "rule_id": "DQ-01",
                "severity": "CRITICAL",
                "table": table,
                "row_number": pk_value,
                "column": "id",
                "value": pk_value,
                "message": f"Duplicate primary key: {pk_value} appears {count} times"
            })
    return failures


def check_composite_key_uniqueness(conn):
    """DQ-02: Check that (company_id, year) is unique in relevant tables."""
    failures = []
    tables_columns = [
        ("profitandloss", "company_id", "year"),
        ("balancesheet", "company_id", "year"),
        ("cashflow", "company_id", "year"),
        ("financial_ratios", "company_id", "year"),
        ("documents", "company_id", "Year")
    ]
    for table, col1, col2 in tables_columns:
        query = f"""
            SELECT {col1}, {col2}, COUNT(*) as cnt
            FROM {table}
            GROUP BY {col1}, {col2}
            HAVING cnt > 1
        """
        rows = execute_query(conn, query)
        for row in rows:
            val1, val2, count = row
            id_query = f"""
                SELECT id FROM {table}
                WHERE {col1} = ? AND {col2} = ?
                LIMIT 1
            """
            id_row = execute_query(conn, id_query, (val1, val2))
            row_id = id_row[0][0] if id_row else None
            failures.append({
                "rule_id": "DQ-02",
                "severity": "CRITICAL",
                "table": table,
                "row_number": row_id,
                "column": f"{col1},{col2}",
                "value": f"{val1},{val2}",
                "message": f"Duplicate combination ({col1}={val1}, {col2}={val2}) appears {count} times"
            })
    return failures


def check_foreign_key_integrity(conn):
    """DQ-03: Check that foreign keys (company_id) reference a valid company."""
    failures = []
    company_ids = set()
    rows = execute_query(conn, "SELECT id FROM companies")
    for row in rows:
        company_ids.add(row[0])

    fk_tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "financial_ratios",
        "stock_prices"
    ]
    for table in fk_tables:
        if not company_ids:
            query = f"SELECT id, company_id FROM {table}"
            params = ()
        else:
            placeholders = ",".join(["?"] * len(company_ids))
            query = f"SELECT id, company_id FROM {table} WHERE company_id NOT IN ({placeholders})"
            params = tuple(company_ids)
        rows = execute_query(conn, query, params)
        for row in rows:
            row_id, company_id = row
            failures.append({
                "rule_id": "DQ-03",
                "severity": "CRITICAL",
                "table": table,
                "row_number": row_id,
                "column": "company_id",
                "value": company_id,
                "message": f"Foreign key company_id={company_id} does not exist in companies table"
            })
    return failures


def check_balance_sheet_equation(conn):
    """DQ-04: Check that the balance sheet equation holds."""
    failures = []
    query = """
        SELECT id,
               total_assets,
               fixed_assets, cwip, investments, other_asset,
               total_liabilities,
               borrowings, other_liabilities,
               equity_capital, reserves
        FROM balancesheet
    """
    rows = execute_query(conn, query)
    for row in rows:
        (row_id, total_assets, fixed_assets, cwip, investments, other_asset,
         total_liabilities, borrowings, other_liabilities,
         equity_capital, reserves) = row

        calculated_assets = (fixed_assets or 0) + (cwip or 0) + (investments or 0) + (other_asset or 0)
        calculated_liabilities = (borrowings or 0) + (other_liabilities or 0)
        calculated_equity = (equity_capital or 0) + (reserves or 0)

        tolerance = 0.01
        if abs(total_assets - calculated_assets) > tolerance:
            failures.append({
                "rule_id": "DQ-04",
                "severity": "WARNING",
                "table": "balancesheet",
                "row_number": row_id,
                "column": "total_assets",
                "value": total_assets,
                "message": f"Total assets mismatch: expected {calculated_assets}, got {total_assets}"
            })
        if abs(total_liabilities - calculated_liabilities) > tolerance:
            failures.append({
                "rule_id": "DQ-04",
                "severity": "WARNING",
                "table": "balancesheet",
                "row_number": row_id,
                "column": "total_liabilities",
                "value": total_liabilities,
                "message": f"Total liabilities mismatch: expected {calculated_liabilities}, got {total_liabilities}"
            })
        if abs(total_assets - (total_liabilities + (equity_capital or 0) + (reserves or 0))) > tolerance:
            failures.append({
                "rule_id": "DQ-04",
                "severity": "WARNING",
                "table": "balancesheet",
                "row_number": row_id,
                "column": "balance_sheet_equation",
                "value": f"assets={total_assets}, liabilities={total_liabilities}, equity={(equity_capital or 0)+(reserves or 0)}",
                "message": "Balance sheet equation does not hold: assets != liabilities + equity"
            })
    return failures


def check_operating_profit_margin(conn):
    """DQ-05: Check that operating profit margin matches operating_profit / sales."""
    failures = []
    query = """
        SELECT id, operating_profit, sales, opm_percentage
        FROM profitandloss
        WHERE sales IS NOT NULL AND sales != 0
    """
    rows = execute_query(conn, query)
    for row in rows:
        row_id, operating_profit, sales, opm_percentage = row
        if operating_profit is None or sales is None or opm_percentage is None:
            continue
        calculated_opm = (operating_profit / sales) * 100.0
        if abs(opm_percentage - calculated_opm) > 0.01:
            failures.append({
                "rule_id": "DQ-05",
                "severity": "WARNING",
                "table": "profitandloss",
                "row_number": row_id,
                "column": "opm_percentage",
                "value": opm_percentage,
                "message": f"OPM mismatch: expected {calculated_opm:.2f}, got {opm_percentage}"
            })
    return failures


def check_positive_sales(conn):
    """DQ-06: Check that sales are positive."""
    failures = []
    query = """
        SELECT id, sales
        FROM profitandloss
        WHERE sales < 0
    """
    rows = execute_query(conn, query)
    for row in rows:
        row_id, sales = row
        failures.append({
            "rule_id": "DQ-06",
            "severity": "WARNING",
            "table": "profitandloss",
            "row_number": row_id,
            "column": "sales",
            "value": sales,
            "message": f"Sales is negative: {sales}"
        })
    return failures


def check_positive_total_assets(conn):
    """DQ-07: Check that total assets are positive."""
    failures = []
    query = """
        SELECT id, total_assets
        FROM balancesheet
        WHERE total_assets <= 0
    """
    rows = execute_query(conn, query)
    for row in rows:
        row_id, total_assets = row
        failures.append({
            "rule_id": "DQ-07",
            "severity": "WARNING",
            "table": "balancesheet",
            "row_number": row_id,
            "column": "total_assets",
            "value": total_assets,
            "message": f"Total assets is non-positive: {total_assets}"
        })
    return failures


def check_net_cash_flow_consistency(conn):
    """DQ-08: Check that net cash flow equals the sum of its components."""
    failures = []
    query = """
        SELECT id, operating_activity, investing_activity, financing_activity, net_cash_flow
        FROM cashflow
    """
    rows = execute_query(conn, query)
    for row in rows:
        (row_id, operating_activity, investing_activity, financing_activity, net_cash_flow) = row
        total = (0 if operating_activity is None else operating_activity) + \
                (0 if investing_activity is None else investing_activity) + \
                (0 if financing_activity is None else financing_activity)
        if net_cash_flow is None:
            continue
        if abs(net_cash_flow - total) > 0.01:
            failures.append({
                "rule_id": "DQ-08",
                "severity": "WARNING",
                "table": "cashflow",
                "row_number": row_id,
                "column": "net_cash_flow",
                "value": net_cash_flow,
                "message": f"Net cash flow mismatch: expected {total}, got {net_cash_flow}"
            })
    return failures


def check_dividend_payout_validation(conn):
    """DQ-09: Check dividend payout consistency between profitandloss and financial_ratios."""
    failures = []
    query = """
        SELECT pl.id, pl.dividend_payout, fr.dividend_payout_ratio_pct
        FROM profitandloss pl
        JOIN financial_ratios fr ON pl.company_id = fr.company_id AND pl.year = fr.year
        WHERE pl.dividend_payout IS NOT NULL AND fr.dividend_payout_ratio_pct IS NOT NULL
    """
    rows = execute_query(conn, query)
    for row in rows:
        pl_id, div_payout, div_ratio = row
        if abs(div_payout - div_ratio) > 0.01:
            failures.append({
                "rule_id": "DQ-09",
                "severity": "WARNING",
                "table": "profitandloss",
                "row_number": pl_id,
                "column": "dividend_payout",
                "value": div_payout,
                "message": f"Dividend payout mismatch: profitandloss={div_payout}, financial_ratios={div_ratio}"
            })
    return failures


def check_url_validation(conn):
    """DQ-10: Check that URLs in documents.Annual_Report are valid (start with http:// or https://)."""
    failures = []
    query = """
        SELECT id, Annual_Report
        FROM documents
        WHERE Annual_Report IS NOT NULL AND Annual_Report != ''
    """
    rows = execute_query(conn, query)
    for row in rows:
        row_id, url = row
        if not (url.startswith("http://") or url.startswith("https://")):
            failures.append({
                "rule_id": "DQ-10",
                "severity": "WARNING",
                "table": "documents",
                "row_number": row_id,
                "column": "Annual_Report",
                "value": url,
                "message": "Invalid URL format: must start with http:// or https://"
            })
    return failures


def check_year_validation(conn):
    """DQ-11: Check that years are within a reasonable range (e.g., 1900 to current year+1)."""
    import datetime
    current_year = datetime.datetime.now().year
    min_year = 1900
    max_year = current_year + 1

    failures = []
    tables_columns = [
        ("profitandloss", "year"),
        ("balancesheet", "year"),
        ("cashflow", "year"),
        ("financial_ratios", "year"),
        ("documents", "Year")
    ]
    for table, column in tables_columns:
        query = f"""
            SELECT id, {column}
            FROM {table}
            WHERE {column} IS NOT NULL AND ({column} < {min_year} OR {column} > {max_year})
        """
        rows = execute_query(conn, query)
        for row in rows:
            row_id, year_val = row
            failures.append({
                "rule_id": "DQ-11",
                "severity": "INFO",
                "table": table,
                "row_number": row_id,
                "column": column,
                "value": year_val,
                "message": f"Year {year_val} is outside expected range [{min_year}, {max_year}]"
            })
    return failures


def check_duplicate_stock_prices(conn):
    """DQ-12: Check for duplicate (company_id, date) in stock_prices."""
    failures = []
    query = """
        SELECT id, company_id, date, COUNT(*) as cnt
        FROM stock_prices
        GROUP BY company_id, date
        HAVING cnt > 1
    """
    rows = execute_query(conn, query)
    for row in rows:
        row_id, company_id, date_val, count = row
        id_query = """
            SELECT id FROM stock_prices
            WHERE company_id = ? AND date = ?
            LIMIT 1
        """
        id_row = execute_query(conn, id_query, (company_id, date_val))
        record_id = id_row[0][0] if id_row else None
        failures.append({
            "rule_id": "DQ-12",
            "severity": "CRITICAL",
            "table": "stock_prices",
            "row_number": record_id,
            "column": "company_id,date",
            "value": f"{company_id},{date_val}",
            "message": f"Duplicate stock price for company_id={company_id}, date={date_val} (occurs {count} times)"
        })
    return failures


def check_eps_sign_consistency(conn):
    """DQ-13: Check EPS sign consistency and match between profitandloss and financial_ratios."""
    failures = []
    # Part 1: Check that eps and net_profit have the same sign (or both zero) in profitandloss
    query1 = """
        SELECT id, eps, net_profit
        FROM profitandloss
        WHERE eps IS NOT NULL AND net_profit IS NOT NULL
    """
    rows = execute_query(conn, query1)
    for row in rows:
        row_id, eps, net_profit = row
        if (eps < 0 and net_profit > 0) or (eps > 0 and net_profit < 0):
            failures.append({
                "rule_id": "DQ-13",
                "severity": "WARNING",
                "table": "profitandloss",
                "row_number": row_id,
                "column": "eps",
                "value": eps,
                "message": f"EPS sign ({eps}) does not match net profit sign ({net_profit})"
            })
    # Part 2: Check that eps matches earnings_per_share in financial_ratios
    query2 = """
        SELECT pl.id, pl.eps, fr.earnings_per_share
        FROM profitandloss pl
        JOIN financial_ratios fr ON pl.company_id = fr.company_id AND pl.year = fr.year
        WHERE pl.eps IS NOT NULL AND fr.earnings_per_share IS NOT NULL
    """
    rows = execute_query(conn, query2)
    for row in rows:
        pl_id, eps, eps_fr = row
        if abs(eps - eps_fr) > 0.01:
            failures.append({
                "rule_id": "DQ-13",
                "severity": "WARNING",
                "table": "profitandloss",
                "row_number": pl_id,
                "column": "eps",
                "value": eps,
                "message": f"EPS mismatch: profitandloss={eps}, financial_ratios={eps_fr}"
            })
    return failures


def check_tax_percentage_validation(conn):
    """DQ-14: Check that tax percentage is between 0 and 100."""
    failures = []
    query = """
        SELECT id, tax_percentage
        FROM profitandloss
        WHERE tax_percentage IS NOT NULL AND (tax_percentage < 0 OR tax_percentage > 100)
    """
    rows = execute_query(conn, query)
    for row in rows:
        row_id, tax_pct = row
        failures.append({
            "rule_id": "DQ-14",
            "severity": "WARNING",
            "table": "profitandloss",
            "row_number": row_id,
            "column": "tax_percentage",
            "value": tax_pct,
            "message": f"Tax percentage out of range [0,100]: {tax_pct}"
        })
    return failures


def check_dataset_coverage_validation(conn):
    """DQ-15: Check that we have data for a reasonable number of companies and years."""
    failures = []
    company_count = execute_query(conn, "SELECT COUNT(*) FROM companies")[0][0]

    fact_tables = ["profitandloss", "balancesheet", "cashflow", "financial_ratios"]
    for table in fact_tables:
        query = f"SELECT COUNT(DISTINCT company_id) FROM {table}"
        distinct_count = execute_query(conn, query)[0][0]
        if distinct_count != company_count:
            failures.append({
                "rule_id": "DQ-15",
                "severity": "INFO",
                "table": table,
                "row_number": None,
                "column": "company_id",
                "value": f"{distinct_count}/{company_count}",
                "message": f"Company coverage: only {distinct_count} out of {company_count} companies have data in {table}"
            })
    return failures


def check_critical_nulls(conn):
    """DQ-16: Check for NULLs in critical columns."""
    failures = []
    critical_columns = {
        "companies": ["id", "company_name"],
        "profitandloss": ["company_id", "year", "sales", "net_profit"],
        "balancesheet": ["company_id", "year", "total_assets"],
        "cashflow": ["company_id", "year", "net_cash_flow"],
        "analysis": ["company_id"],
        "documents": ["company_id", "Year", "Annual_Report"],
        "prosandcons": ["company_id"],
        "sectors": ["company_id"],
        "financial_ratios": ["company_id", "year"],
        "stock_prices": ["company_id", "date", "close_price"]
    }

    for table, columns in critical_columns.items():
        if table not in get_table_names(conn):
            continue
        for col in columns:
            query = f"""
                SELECT id, {col}
                FROM {table}
                WHERE {col} IS NULL
            """
            rows = execute_query(conn, query)
            for row in rows:
                row_id, value = row
                failures.append({
                    "rule_id": "DQ-16",
                    "severity": "CRITICAL",
                    "table": table,
                    "row_number": row_id,
                    "column": col,
                    "value": value,
                    "message": f"Critical column {col} is NULL"
                })
    return failures


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    if not DB_PATH.exists():
        print(f"Database file not found: {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        all_failures = []

        validation_functions = [
            check_primary_key_uniqueness,
            check_composite_key_uniqueness,
            check_foreign_key_integrity,
            check_balance_sheet_equation,
            check_operating_profit_margin,
            check_positive_sales,
            check_positive_total_assets,
            check_net_cash_flow_consistency,
            check_dividend_payout_validation,
            check_url_validation,
            check_year_validation,
            check_duplicate_stock_prices,
            check_eps_sign_consistency,
            check_tax_percentage_validation,
            check_dataset_coverage_validation,
            check_critical_nulls
        ]

        for validate_func in validation_functions:
            try:
                failures = validate_func(conn)
                all_failures.extend(failures)
                print(f"Function {validate_func.__name__} found {len(failures)} issues")
            except Exception as e:
                print(f"Error in {validate_func.__name__}: {e}", file=sys.stderr)

        if all_failures:
            df = pd.DataFrame(all_failures)
            df = df[["rule_id", "severity", "table", "row_number", "column", "value", "message"]]
            df.to_csv(OUTPUT_CSV, index=False)
            print(f"Validation complete. Found {len(all_failures)} issues. Report saved to {OUTPUT_CSV}")
        else:
            df = pd.DataFrame(columns=["rule_id", "severity", "table", "row_number", "column", "value", "message"])
            df.to_csv(OUTPUT_CSV, index=False)
            print("Validation complete. No issues found.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()