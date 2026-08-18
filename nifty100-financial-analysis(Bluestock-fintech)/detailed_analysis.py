import sqlite3
from pathlib import Path

def detailed_analysis():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    # Get all company IDs
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies ORDER BY id")
    company_ids = [row[0] for row in cursor.fetchall()]

    print(f"Total companies: {len(company_ids)}")

    # For each company, count distinct years in each table using SUBSTR(year, 1, 4) as mentioned in dispute report
    pl_counts = []
    bs_counts = []
    cf_counts = []
    passing_all = []

    for company_id in company_ids:
        # P&L years
        cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
        FROM profitandloss
        WHERE company_id = ?
        """, (company_id,))
        pl_years = cursor.fetchone()[0]
        pl_counts.append(pl_years)

        # BS years
        cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
        FROM balancesheet
        WHERE company_id = ?
        """, (company_id,))
        bs_years = cursor.fetchone()[0]
        bs_counts.append(bs_years)

        # CF years
        cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
        FROM cashflow
        WHERE company_id = ?
        """, (company_id,))
        cf_years = cursor.fetchone()[0]
        cf_counts.append(cf_years)

        # Check if passes all three
        if pl_years >= 10 and bs_years >= 10 and cf_years >= 10:
            passing_all.append(company_id)

    # Statistics
    pl_ge_10 = sum(1 for count in pl_counts if count >= 10)
    bs_ge_10 = sum(1 for count in bs_counts if count >= 10)
    cf_ge_10 = sum(1 for count in cf_counts if count >= 10)

    print(f"Companies with >=10 distinct P&L years: {pl_ge_10}/92")
    print(f"Companies with >=10 distinct BS years: {bs_ge_10}/92")
    print(f"Companies with >=10 distinct CF years: {cf_ge_10}/92")
    print(f"Companies passing all three criteria: {len(passing_all)}/92")

    # Show companies failing each criterion
    print("\nCompanies with <10 P&L years:")
    failing_pl = [(company_ids[i], pl_counts[i]) for i in range(len(company_ids)) if pl_counts[i] < 10]
    for company_id, count in failing_pl[:10]:  # Show first 10
        print(f"  {company_id}: {count} years")

    print("\nCompanies with <10 BS years:")
    failing_bs = [(company_ids[i], bs_counts[i]) for i in range(len(company_ids)) if bs_counts[i] < 10]
    for company_id, count in failing_bs[:10]:  # Show first 10
        print(f"  {company_id}: {count} years")

    print("\nCompanies with <10 CF years:")
    failing_cf = [(company_ids[i], cf_counts[i]) for i in range(len(company_ids)) if cf_counts[i] < 10]
    for company_id, count in failing_cf[:10]:  # Show first 10
        print(f"  {company_id}: {count} years")

    # Show companies that fail the combined criteria
    failing_all = [company_ids[i] for i in range(len(company_ids))
                   if pl_counts[i] < 10 or bs_counts[i] < 10 or cf_counts[i] < 10]
    print(f"\nCompanies failing at least one criterion: {len(failing_all)}/92")
    print("First 10 failing companies:")
    for company_id in failing_all[:10]:
        idx = company_ids.index(company_id)
        print(f"  {company_id}: P&L={pl_counts[idx]}, BS={bs_counts[idx]}, CF={cf_counts[idx]}")

    conn.close()

if __name__ == "__main__":
    detailed_analysis()