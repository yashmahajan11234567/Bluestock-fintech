"""
AC-19 Validation Script - Generates validation CSV with schema:
company_id, field, issue, severity

Runs data quality checks on the SQLite database and outputs a CSV report
matching the AC-19 acceptance criteria schema.
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
OUTPUT_DIR = BASE_DIR / "Data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV = OUTPUT_DIR / "ac19_validation.csv"


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_table_names(conn):
    """Return a list of table names in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]


def execute_query(conn, query, parameters=()):
    """Execute a query and return the results as a list of tuples."""
    cursor = conn.cursor()
    cursor.execute(query, parameters)
    return cursor.fetchall()


# ----------------------------------------------------------------------
# Validation functions - each returns list of (company_id, field, issue, severity)
# ----------------------------------------------------------------------
def check_primary_key_uniqueness(conn):
    """DQ-01: Check that primary keys are unique in each table."""
    failures = []
    tables = get_table_names(conn)
    for table in tables:
        query = f"""
            SELECT id, company_id, COUNT(*) as cnt
            FROM {table}
            GROUP BY id, company_id
            HAVING cnt > 1
        """
        rows = execute_query(conn, query)
        for row in rows:
            pk_value, company_id, count = row
            failures.append({
                "company_id": company_id,
                "field": f"{table}.id",
                "issue": f"Duplicate primary key: {pk_value} appears {count} times",
                "severity": "CRITICAL"
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
            failures.append({
                "company_id": val1,
                "field": f"{table}.{col1},{col2}",
                "issue": f"Duplicate composite key ({col1}={val1}, {col2}={val2}) appears {count} times",
                "severity": "CRITICAL"
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
        "profitandloss", "balancesheet", "cashflow", "analysis",
        "documents", "prosandcons", "sectors", "financial_ratios", "stock_prices"
    ]
    for table in fk_tables:
        if not company_ids:
            query = f"SELECT company_id, id FROM {table}"
            params = ()
        else:
            placeholders = ",".join(["?"] * len(company_ids))
            query = f"SELECT company_id, id FROM {table} WHERE company_id NOT IN ({placeholders})"
            params = tuple(company_ids)
        rows = execute_query(conn, query, params)
        for row in rows:
            company_id, row_id = row
            failures.append({
                "company_id": company_id,
                "field": f"{table}.company_id",
                "issue": f"Foreign key company_id={company_id} does not exist in companies table (row id: {row_id})",
                "severity": "CRITICAL"
            })
    return failures


def check_balance_sheet_equation(conn):
    """DQ-04: Check that the balance sheet equation holds."""
    failures = []
    query = """
        SELECT company_id, id,
               total_assets,
               fixed_assets, cwip, investments, other_asset,
               total_liabilities,
               borrowings, other_liabilities,
               equity_capital, reserves
        FROM balancesheet
    """
    rows = execute_query(conn, query)
    for row in rows:
        (company_id, row_id, total_assets, fixed_assets, cwip, investments, other_asset,
         total_liabilities, borrowings, other_liabilities,
         equity_capital, reserves) = row

        calculated_assets = (fixed_assets or 0) + (cwip or 0) + (investments or 0) + (other_asset or 0)
        calculated_liabilities = (borrowings or 0) + (other_liabilities or 0)
        calculated_equity = (equity_capital or 0) + (reserves or 0)

        tolerance = 0.01
        if abs(total_assets - calculated_assets) > tolerance:
            failures.append({
                "company_id": company_id,
                "field": "balancesheet.total_assets",
                "issue": f"Total assets mismatch: expected {calculated_assets:.2f}, got {total_assets:.2f}",
                "severity": "WARNING"
            })
        if abs(total_liabilities - calculated_liabilities) > tolerance:
            failures.append({
                "company_id": company_id,
                "field": "balancesheet.total_liabilities",
                "issue": f"Total liabilities mismatch: expected {calculated_liabilities:.2f}, got {total_liabilities:.2f}",
                "severity": "WARNING"
            })
        if abs(total_assets - (total_liabilities + (equity_capital or 0) + (reserves or 0))) > tolerance:
            failures.append({
                "company_id": company_id,
                "field": "balancesheet.balance_sheet_equation",
                "issue": f"Balance sheet equation does not hold: assets={total_assets:.2f}, liabilities+equity={(total_liabilities + (equity_capital or 0) + (reserves or 0)):.2f}",
                "severity": "WARNING"
            })
    return failures


def check_operating_profit_margin(conn):
    """DQ-05: Check that operating profit margin matches operating_profit / sales."""
    failures = []
    query = """
        SELECT company_id, id, operating_profit, sales, opm_percentage
        FROM profitandloss
        WHERE sales IS NOT NULL AND sales != 0
    """
    rows = execute_query(conn, query)
    for row in rows:
        company_id, row_id, operating_profit, sales, opm_percentage = row
        if operating_profit is None or sales is None or opm_percentage is None:
            continue
        calculated_opm = (operating_profit / sales) * 100.0
        if abs(opm_percentage - calculated_opm) > 0.01:
            failures.append({
                "company_id": company_id,
                "field": "profitandloss.opm_percentage",
                "issue": f"OPM mismatch: expected {calculated_opm:.2f}%, got {opm_percentage:.2f}%",
                "severity": "WARNING"
            })
    return failures


def check_positive_sales(conn):
    """DQ-06: Check that sales are positive."""
    failures = []
    query = """
        SELECT company_id, id, sales
        FROM profitandloss
        WHERE sales < 0
    """
    rows = execute_query(conn, query)
    for row in rows:
        company_id, row_id, sales = row
        failures.append({
            "company_id": company_id,
            "field": "profitandloss.sales",
            "issue": f"Sales is negative: {sales}",
            "severity": "WARNING"
        })
    return failures


def check_positive_total_assets(conn):
    """DQ-07: Check that total assets are positive."""
    failures = []
    query = """
        SELECT company_id, id, total_assets
        FROM balancesheet
        WHERE total_assets <= 0
    """
    rows = execute_query(conn, query)
    for row in rows:
        company_id, row_id, total_assets = row
        failures.append({
            "company_id": company_id,
            "field": "balancesheet.total_assets",
            "issue": f"Total assets is non-positive: {total_assets}",
            "severity": "WARNING"
        })
    return failures


def check_net_cash_flow_consistency(conn):
    """DQ-08: Check that net cash flow equals the sum of its components."""
    failures = []
    query = """
        SELECT company_id, id, operating_activity, investing_activity, financing_activity, net_cash_flow
        FROM cashflow
    """
    rows = execute_query(conn, query)
    for row in rows:
        (company_id, row_id, operating_activity, investing_activity, financing_activity, net_cash_flow) = row
        total = (0 if operating_activity is None else operating_activity) + \
                (0 if investing_activity is None else investing_activity) + \
                (0 if financing_activity is None else financing_activity)
        if net_cash_flow is None:
            continue
        if abs(net_cash_flow - total) > 0.01:
            failures.append({
                "company_id": company_id,
                "field": "cashflow.net_cash_flow",
                "issue": f"Net cash flow mismatch: expected {total:.2f}, got {net_cash_flow:.2f}",
                "severity": "WARNING"
            })
    return failures


def check_dividend_payout_validation(conn):
    """DQ-09: Check dividend payout consistency between profitandloss and financial_ratios."""
    failures = []
    query = """
        SELECT pl.company_id, pl.id, pl.dividend_payout, fr.dividend_payout_ratio_pct
        FROM profitandloss pl
        JOIN financial_ratios fr ON pl.company_id = fr.company_id AND pl.year = fr.year
        WHERE pl.dividend_payout IS NOT NULL AND fr.dividend_payout_ratio_pct IS NOT NULL
    """
    rows = execute_query(conn, query)
    for row in rows:
        company_id, pl_id, div_payout, div_ratio = row
        if abs(div_payout - div_ratio) > 0.01:
            failures.append({
                "company_id": company_id,
                "field": "profitandloss.dividend_payout",
                "issue": f"Dividend payout mismatch: profitandloss={div_payout}, financial_ratios={div_ratio}",
                "severity": "WARNING"
            })
    return failures


def check_url_validation(conn):
    """DQ-10: Check that URLs in documents.Annual_Report are valid (start with http:// or https://)."""
    failures = []
    query = """
        SELECT company_id, id, Annual_Report
        FROM documents
        WHERE Annual_Report IS NOT NULL AND Annual_Report != ''
    """
    rows = execute_query(conn, query)
    for row in rows:
        company_id, row_id, url = row
        if not (url.startswith("http://") or url.startswith("https://")):
            failures.append({
                "company_id": company_id,
                "field": "documents.Annual_Report",
                "issue": "Invalid URL format: must start with http:// or https://",
                "severity": "WARNING"
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
            SELECT company_id, id, {column}
            FROM {table}
            WHERE {column} IS NOT NULL AND ({column} < {min_year} OR {column} > {max_year})
        """
        rows = execute_query(conn, query)
        for row in rows:
            company_id, row_id, year_val = row
            failures.append({
                "company_id": company_id,
                "field": f"{table}.{column}",
                "issue": f"Year {year_val} is outside expected range [{min_year}, {max_year}]",
                "severity": "INFO"
            })
    return failures


def check_duplicate_stock_prices(conn):
    """DQ-12: Check for duplicate (company_id, date) in stock_prices."""
    failures = []
    query = """
        SELECT company_id, date, COUNT(*) as cnt
        FROM stock_prices
        GROUP BY company_id, date
        HAVING cnt > 1
    """
    rows = execute_query(conn, query)
    for row in rows:
        company_id, date_val, count = row
        failures.append({
            "company_id": company_id,
            "field": "stock_prices.company_id,date",
            "issue": f"Duplicate stock price for company_id={company_id}, date={date_val} (occurs {count} times)",
            "severity": "CRITICAL"
        })
    return failures


def check_eps_sign_consistency(conn):
    """DQ-13: Check EPS sign consistency and match between profitandloss and financial_ratios."""
    failures = []
    # Part 1: Check that eps and net_profit have the same sign (or both zero) in profitandloss
    query1 = """
        SELECT company_id, id, eps, net_profit
        FROM profitandloss
        WHERE eps IS NOT NULL AND net_profit IS NOT NULL
    """
    rows = execute_query(conn, query1)
    for row in rows:
        company_id, row_id, eps, net_profit = row
        if (eps < 0 and net_profit > 0) or (eps > 0 and net_profit < 0):
            failures.append({
                "company_id": company_id,
                "field": "profitandloss.eps",
                "issue": f"EPS sign ({eps}) does not match net profit sign ({net_profit})",
                "severity": "WARNING"
            })
    # Part 2: Check that eps matches earnings_per_share in financial_ratios
    query2 = """
        SELECT pl.company_id, pl.id, pl.eps, fr.earnings_per_share
        FROM profitandloss pl
        JOIN financial_ratios fr ON pl.company_id = fr.company_id AND pl.year = fr.year
        WHERE pl.eps IS NOT NULL AND fr.earnings_per_share IS NOT NULL
    """
    rows = execute_query(conn, query2)
    for row in rows:
        company_id, pl_id, eps, eps_fr = row
        if abs(eps - eps_fr) > 0.01:
            failures.append({
                "company_id": company_id,
                "field": "profitandloss.eps",
                "issue": f"EPS mismatch: profitandloss={eps}, financial_ratios={eps_fr}",
                "severity": "WARNING"
            })
    return failures


def check_tax_percentage_validation(conn):
    """DQ-14: Check that tax percentage is between 0 and 100."""
    failures = []
    query = """
        SELECT company_id, id, tax_percentage
        FROM profitandloss
        WHERE tax_percentage IS NOT NULL AND (tax_percentage < 0 OR tax_percentage > 100)
    """
    rows = execute_query(conn, query)
    for row in rows:
        company_id, row_id, tax_pct = row
        failures.append({
            "company_id": company_id,
            "field": "profitandloss.tax_percentage",
            "issue": f"Tax percentage out of range [0,100]: {tax_pct}",
            "severity": "WARNING"
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
            # Get the companies that are missing
            missing_query = f"""
                SELECT c.id FROM companies c
                WHERE c.id NOT IN (SELECT DISTINCT company_id FROM {table})
            """
            missing = execute_query(conn, missing_query)
            for m in missing:
                failures.append({
                    "company_id": m[0],
                    "field": f"{table}.company_id",
                    "issue": f"Missing data for company in {table}",
                    "severity": "INFO"
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
            # Get the company_id column name (might be different per table)
            # For companies table, the primary key is 'id'
            if table == "companies":
                query = f"SELECT id, {col} FROM {table} WHERE {col} IS NULL"
                pk_col = "id"
            else:
                query = f"SELECT company_id, id, {col} FROM {table} WHERE {col} IS NULL"
                pk_col = "company_id"
            rows = execute_query(conn, query)
            for row in rows:
                if table == "companies":
                    company_id, value = row
                else:
                    company_id, row_id, value = row
                failures.append({
                    "company_id": company_id,
                    "field": f"{table}.{col}",
                    "issue": f"Critical column {col} is NULL",
                    "severity": "CRITICAL"
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
            # Ensure correct column order: company_id, field, issue, severity
            df = df[["company_id", "field", "issue", "severity"]]
            df.to_csv(OUTPUT_CSV, index=False)
            print(f"Validation complete. Found {len(all_failures)} issues. Report saved to {OUTPUT_CSV}")
        else:
            df = pd.DataFrame(columns=["company_id", "field", "issue", "severity"])
            df.to_csv(OUTPUT_CSV, index=False)
            print("Validation complete. No issues found.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()