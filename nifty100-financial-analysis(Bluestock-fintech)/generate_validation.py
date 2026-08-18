"""
Generate validation output in the acceptance criteria format:
company_id, field, issue, severity

While preserving the detailed diagnostic information from the current validator.
"""
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "Data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV_AC = OUTPUT_DIR / "validation_failures_ac.csv"  # Acceptance criteria format
OUTPUT_CSV_DETAILED = OUTPUT_DIR / "validation_failures_detailed.csv"  # Detailed format

def execute_query(conn, query, parameters=()):
    cursor = conn.cursor()
    cursor.execute(query, parameters)
    return cursor.fetchall()

# Run the existing validator's logic
import sys
sys.path.insert(0, str(BASE_DIR))
from src.etl.validator import (
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
)

def main():
    if not DB_PATH.exists():
        print(f"Database file not found: {DB_PATH}")
        return

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
                print(f"Error in {validate_func.__name__}: {e}")

        if all_failures:
            # Detailed format (existing)
            df_detailed = pd.DataFrame(all_failures)
            df_detailed = df_detailed[["rule_id", "severity", "table", "row_number", "column", "value", "message"]]
            df_detailed.to_csv(OUTPUT_CSV_DETAILED, index=False)
            print(f"Detailed validation report saved to {OUTPUT_CSV_DETAILED} ({len(all_failures)} issues)")

            # Acceptance criteria format: company_id, field, issue, severity
            ac_rows = []
            for failure in all_failures:
                # Get company_id from the table and row_number
                company_id = None
                table = failure.get("table")
                row_number = failure.get("row_number")

                if table and row_number is not None:
                    # Try to find company_id from the table
                    try:
                        query = f"SELECT company_id FROM {table} WHERE id = ?"
                        rows = execute_query(conn, query, (row_number,))
                        if rows:
                            company_id = rows[0][0]
                    except Exception:
                        pass

                if company_id is None:
                    company_id = "N/A"

                field = failure.get("column", "unknown")
                issue = failure.get("message", failure.get("rule_id", "unknown"))
                severity = failure.get("severity", "UNKNOWN")

                ac_rows.append({
                    "company_id": company_id,
                    "field": field,
                    "issue": issue,
                    "severity": severity
                })

            df_ac = pd.DataFrame(ac_rows)
            df_ac.to_csv(OUTPUT_CSV_AC, index=False)
            print(f"AC validation report saved to {OUTPUT_CSV_AC} ({len(ac_rows)} rows)")

            # Also create a summary of rules
            rules_summary = df_detailed.groupby(["rule_id", "severity"]).size().reset_index(name="count")
            print("\nRule summary:")
            print(rules_summary.to_string())

        else:
            # Create empty files with required columns
            df_ac = pd.DataFrame(columns=["company_id", "field", "issue", "severity"])
            df_ac.to_csv(OUTPUT_CSV_AC, index=False)

            df_detailed = pd.DataFrame(columns=["rule_id", "severity", "table", "row_number", "column", "value", "message"])
            df_detailed.to_csv(OUTPUT_CSV_DETAILED, index=False)
            print("Validation complete. No issues found.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()