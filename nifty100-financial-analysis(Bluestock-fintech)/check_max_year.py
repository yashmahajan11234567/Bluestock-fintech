import sqlite3
from pathlib import Path

def check_max_year():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    # Check max year in each table
    tables = ['profitandloss', 'balancesheet', 'cashflow']
    for table in tables:
        cursor.execute(f"SELECT MAX(year) FROM {table}")
        max_year = cursor.fetchone()[0]
        cursor.execute(f"SELECT MIN(year) FROM {table}")
        min_year = cursor.fetchone()[0]
        print(f"{table}: {min_year} to {max_year}")

    # Check for M&M specifically
    print("\n=== M&M Year Range ===")
    cursor.execute("""
    SELECT MIN(year), MAX(year)
    FROM profitandloss
    WHERE company_id = 'M&M'
    """)
    min_year, max_year = cursor.fetchone()
    print(f"P&L: {min_year} to {max_year}")

    cursor.execute("""
    SELECT MIN(year), MAX(year)
    FROM balancesheet
    WHERE company_id = 'M&M'
    """)
    min_year, max_year = cursor.fetchone()
    print(f"BS: {min_year} to {max_year}")

    cursor.execute("""
    SELECT MIN(year), MAX(year)
    FROM cashflow
    WHERE company_id = 'M&M'
    """)
    min_year, max_year = cursor.fetchone()
    print(f"CF: {min_year} to {max_year}")

    conn.close()

if __name__ == "__main__":
    check_max_year()