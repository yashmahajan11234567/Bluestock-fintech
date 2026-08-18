import sqlite3
from pathlib import Path

def check_year_format():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    # Check sample year values from each table
    tables = ['profitandloss', 'balancesheet', 'cashflow']

    for table in tables:
        print(f"\n=== {table.upper()} Year Format Samples ===")
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT year FROM {table} LIMIT 10")
        years = cursor.fetchall()
        for year in years:
            print(f"  '{year[0]}'")

        # Also check for NULLs
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE year IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"  NULL years: {null_count}")

        # Check total distinct years
        cursor.execute(f"SELECT COUNT(DISTINCT year) FROM {table}")
        distinct_count = cursor.fetchone()[0]
        print(f"  Distinct year values: {distinct_count}")

    conn.close()

if __name__ == "__main__":
    check_year_format()