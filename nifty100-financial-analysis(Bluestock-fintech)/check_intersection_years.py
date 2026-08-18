import sqlite3
from pathlib import Path

def check_intersection_years():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies ORDER BY id")
    company_ids = [row[0] for row in cursor.fetchall()]

    results = []
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

        # Intersection: years present in all three tables
        common_years = pl_years & bs_years & cf_years
        common_count = len(common_years)

        results.append((company_id, len(pl_years), len(bs_years), len(cf_years), common_count, sorted(common_years)))

    # Sort by common count ascending
    results.sort(key=lambda x: x[4])

    print("Companies sorted by number of years common to all three tables (ascending):")
    for company_id, pl_cnt, bs_cnt, cf_cnt, common_cnt, common_years in results:
        if common_cnt < 10:
            print(f"{company_id}: P&L={pl_cnt}, BS={bs_cnt}, CF={cf_cnt}, Common={common_cnt} Years={common_years}")

    print("\nSummary:")
    total = len(results)
    passing = sum(1 for r in results if r[4] >= 10)
    print(f"Companies with >=10 common years: {passing}/{total} ({passing/total*100:.2f}%)")
    print(f"Companies with <10 common years: {total - passing}/{total}")

    # Show the companies that have <10 common years (failing)
    failing = [r for r in results if r[4] < 10]
    print(f"\nFailing companies ({len(failing)}):")
    for company_id, pl_cnt, bs_cnt, cf_cnt, common_cnt, common_years in failing:
        print(f"  {company_id}: P&L={pl_cnt}, BS={bs_cnt}, CF={cf_cnt}, Common={common_cnt}")

    # Also, let's list the first 10 failing companies as per dispute report style
    print("\nFirst 10 failing companies (by common years):")
    for company_id, pl_cnt, bs_cnt, cf_cnt, common_cnt, common_years in failing[:10]:
        print(f"  {company_id}: P&L={pl_cnt}, BS={bs_cnt}, CF={cf_cnt}")

    conn.close()

if __name__ == "__main__":
    check_intersection_years()