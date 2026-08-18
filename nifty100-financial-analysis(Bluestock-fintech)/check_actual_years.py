import sqlite3
from pathlib import Path

def check_actual_years():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    # Check the actual companies from dispute report that ARE in DB
    companies_to_check = [
        ('M&MFIN', 'M&M'),  # Maps to M&M
        ('NAUKRI', 'NAUKRI'),  # Exact match
        ('NESTLEIND', 'NESTLEIND'),  # Exact match
    ]

    for dispute_name, db_id in companies_to_check:
        print(f"\n=== {dispute_name} (DB ID: {db_id}) ===")

        # Get all distinct years from each table
        cursor = conn.cursor()
        cursor.execute("""
        SELECT DISTINCT year
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
        """, (db_id,))
        pl_years = [row[0] for row in cursor.fetchall()]
        print(f"P&L years ({len(pl_years)}): {pl_years}")

        cursor.execute("""
        SELECT DISTINCT year
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
        """, (db_id,))
        bs_years = [row[0] for row in cursor.fetchall()]
        print(f"BS years ({len(bs_years)}): {bs_years}")

        cursor.execute("""
        SELECT DISTINCT year
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
        """, (db_id,))
        cf_years = [row[0] for row in cursor.fetchall()]
        print(f"CF years ({len(cf_years)}): {cf_years}")

        # Check using SUBSTR(year, 1, 4) as mentioned in dispute report
        cursor.execute("""
        SELECT DISTINCT SUBSTR(year, 1, 4)
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY SUBSTR(year, 1, 4)
        """, (db_id,))
        pl_substr_years = [row[0] for row in cursor.fetchall()]
        print(f"P&L SUBSTR years ({len(pl_substr_years)}): {pl_substr_years}")

        cursor.execute("""
        SELECT DISTINCT SUBSTR(year, 1, 4)
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY SUBSTR(year, 1, 4)
        """, (db_id,))
        bs_substr_years = [row[0] for row in cursor.fetchall()]
        print(f"BS SUBSTR years ({len(bs_substr_years)}): {bs_substr_years}")

        cursor.execute("""
        SELECT DISTINCT SUBSTR(year, 1, 4)
        FROM cashflow
        WHERE company_id = ?
        ORDER BY SUBSTR(year, 1, 4)
        """, (db_id,))
        cf_substr_years = [row[0] for row in cursor.fetchall()]
        print(f"CF SUBSTR years ({len(cf_substr_years)}): {cf_substr_years}")

    conn.close()

if __name__ == "__main__":
    check_actual_years()