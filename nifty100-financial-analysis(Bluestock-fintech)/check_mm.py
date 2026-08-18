import sqlite3
from pathlib import Path

def check_mm():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    # Check M&M company
    print("=== M&M (Mahindra & Mahindra Ltd) ===")
    cursor.execute("""
    SELECT year FROM profitandloss
    WHERE company_id = 'M&M'
    ORDER BY year
    """)
    pl_years = [row[0] for row in cursor.fetchall()]
    print(f"P&L years (raw): {pl_years}")
    pl_distinct = len(set([str(y)[:4] for y in pl_years if y]))
    print(f"P&L distinct years (first 4 chars): {pl_distinct}")

    cursor.execute("""
    SELECT year FROM balancesheet
    WHERE company_id = 'M&M'
    ORDER BY year
    """)
    bs_years = [row[0] for row in cursor.fetchall()]
    print(f"BS years (raw): {bs_years}")
    bs_distinct = len(set([str(y)[:4] for y in bs_years if y]))
    print(f"BS distinct years (first 4 chars): {bs_distinct}")

    cursor.execute("""
    SELECT year FROM cashflow
    WHERE company_id = 'M&M'
    ORDER BY year
    """)
    cf_years = [row[0] for row in cursor.fetchall()]
    print(f"CF years (raw): {cf_years}")
    cf_distinct = len(set([str(y)[:4] for y in cf_years if y]))
    print(f"CF distinct years (first 4 chars): {cf_distinct}")

    # Check using SUBSTR as in the dispute report
    cursor.execute("""
    SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
    FROM profitandloss
    WHERE company_id = 'M&M'
    """)
    pl_substr = cursor.fetchone()[0]
    print(f"P&L years using SUBSTR: {pl_substr}")

    cursor.execute("""
    SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
    FROM balancesheet
    WHERE company_id = 'M&M'
    """)
    bs_substr = cursor.fetchone()[0]
    print(f"BS years using SUBSTR: {bs_substr}")

    cursor.execute("""
    SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
    FROM cashflow
    WHERE company_id = 'M&M'
    """)
    cf_substr = cursor.fetchone()[0]
    print(f"CF years using SUBSTR: {cf_substr}")

    conn.close()

if __name__ == "__main__":
    check_mm()