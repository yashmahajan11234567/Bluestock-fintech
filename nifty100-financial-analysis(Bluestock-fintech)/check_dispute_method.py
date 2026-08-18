import sqlite3
from pathlib import Path

def check_dispute_method():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies ORDER BY id")
    company_ids = [row[0] for row in cursor.fetchall()]

    results = []
    for company_id in company_ids:
        # P&L years: only those where the first 4 characters are digits
        cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
        FROM profitandloss
        WHERE company_id = ?
          AND SUBSTR(year, 1, 4) GLOB '[0-9][0-9][0-9][0-9]'
        """, (company_id,))
        pl_years = cursor.fetchone()[0]

        # BS years
        cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
        FROM balancesheet
        WHERE company_id = ?
          AND SUBSTR(year, 1, 4) GLOB '[0-9][0-9][0-9][0-9]'
        """, (company_id,))
        bs_years = cursor.fetchone()[0]

        # CF years
        cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
        FROM cashflow
        WHERE company_id = ?
          AND SUBSTR(year, 1, 4) GLOB '[0-9][0-9][0-9][0-9]'
        """, (company_id,))
        cf_years = cursor.fetchone()[0]

        # Check if passes all three
        passes = (pl_years >= 10 and bs_years >= 10 and cf_years >= 10)
        results.append((company_id, pl_years, bs_years, cf_years, passes))

    # Statistics
    pl_ge_10 = sum(1 for r in results if r[1] >= 10)
    bs_ge_10 = sum(1 for r in results if r[2] >= 10)
    cf_ge_10 = sum(1 for r in results if r[3] >= 10)
    passing_all = sum(1 for r in results if r[4])

    print(f"Companies with >=10 distinct P&L years (digits only): {pl_ge_10}/92")
    print(f"Companies with >=10 distinct BS years (digits only): {bs_ge_10}/92")
    print(f"Companies with >=10 distinct CF years (digits only): {cf_ge_10}/92")
    print(f"Companies passing all three criteria: {passing_all}/92")

    # Show companies failing each criterion
    print("\nCompanies with <10 P&L years:")
    failing_pl = [(r[0], r[1]) for r in results if r[1] < 10]
    for company_id, count in failing_pl[:10]:
        print(f"  {company_id}: {count} years")

    print("\nCompanies with <10 BS years:")
    failing_bs = [(r[0], r[2]) for r in results if r[2] < 10]
    for company_id, count in failing_bs[:10]:
        print(f"  {company_id}: {count} years")

    print("\nCompanies with <10 CF years:")
    failing_cf = [(r[0], r[3]) for r in results if r[3] < 10]
    for company_id, count in failing_cf[:10]:
        print(f"  {company_id}: {count} years")

    # Show companies that fail the combined criteria
    failing_all = [r for r in results if not r[4]]
    print(f"\nCompanies failing at least one criterion: {len(failing_all)}/92")
    print("First 10 failing companies:")
    for company_id, pl_cnt, bs_cnt, cf_cnt, passes in failing_all[:10]:
        print(f"  {company_id}: P&L={pl_cnt}, BS={bs_cnt}, CF={cf_cnt}")

    conn.close()

if __name__ == "__main__":
    check_dispute_method()