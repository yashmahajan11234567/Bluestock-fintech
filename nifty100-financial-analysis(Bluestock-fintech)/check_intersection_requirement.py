import sqlite3
from pathlib import Path

def check_intersection_requirement():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies ORDER BY id")
    company_ids = [row[0] for row in cursor.fetchall()]

    passing_intersection = []
    all_results = []

    for company_id in company_ids:
        # Get distinct years from each table (only where year starts with 4 digits)
        cursor.execute("""
        SELECT DISTINCT SUBSTR(year, 1, 4) as y
        FROM profitandloss
        WHERE company_id = ? AND SUBSTR(year, 1, 4) GLOB '[0-9][0-9][0-9][0-9]'
        """, (company_id,))
        pl_years = set([row[0] for row in cursor.fetchall()])

        cursor.execute("""
        SELECT DISTINCT SUBSTR(year, 1, 4) as y
        FROM balancesheet
        WHERE company_id = ? AND SUBSTR(year, 1, 4) GLOB '[0-9][0-9][0-9][0-9]'
        """, (company_id,))
        bs_years = set([row[0] for row in cursor.fetchall()])

        cursor.execute("""
        SELECT DISTINCT SUBSTR(year, 1, 4) as y
        FROM cashflow
        WHERE company_id = ? AND SUBSTR(year, 1, 4) GLOB '[0-9][0-9][0-9][0-9]'
        """, (company_id,))
        cf_years = set([row[0] for row in cursor.fetchall()])

        # Intersection: years present in ALL three tables
        common_years = pl_years & bs_years & cf_years
        common_count = len(common_years)

        all_results.append((company_id, len(pl_years), len(bs_years), len(cf_years), common_count))

        if common_count >= 10:
            passing_intersection.append(company_id)

    print(f"Companies with >=10 years in INTERSECTION of all three tables: {len(passing_intersection)}/92")
    print(f"Percentage: {len(passing_intersection)/92*100:.2f}%")

    # Show companies failing the intersection requirement
    failing = [r for r in all_results if r[4] < 10]
    print(f"\nCompanies with <10 years in intersection: {len(failing)}/92")
    print("First 10 failing companies:")
    for company_id, pl_cnt, bs_cnt, cf_cnt, common_cnt in failing[:10]:
        print(f"  {company_id}: P&L={pl_cnt}, BS={bs_cnt}, CF={cf_cnt}, Common={common_cnt}")

    conn.close()

if __name__ == "__main__":
    check_intersection_requirement()