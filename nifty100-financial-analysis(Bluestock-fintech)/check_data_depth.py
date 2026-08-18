import sqlite3
from pathlib import Path

def check_data_depth():
    db_path = Path(__file__).parent / "Data" / "bluestock.db"
    conn = sqlite3.connect(db_path)

    # Check distinct years for each company in each table
    query = """
    SELECT
        company_id,
        COUNT(DISTINCT SUBSTR(year, 1, 4)) as distinct_years
    FROM profitandloss
    GROUP BY company_id
    ORDER BY distinct_years ASC
    """

    cursor = conn.cursor()
    cursor.execute(query)
    pl_results = cursor.fetchall()

    print("P&L Distinct Years per Company:")
    pl_under_10 = 0
    for company_id, years in pl_results:
        if years < 10:
            pl_under_10 += 1
        print(f"Company {company_id}: {years} years")
    print(f"Companies with <10 P&L years: {pl_under_10}/92\n")

    # Balance Sheet
    cursor.execute("""
    SELECT
        company_id,
        COUNT(DISTINCT SUBSTR(year, 1, 4)) as distinct_years
    FROM balancesheet
    GROUP BY company_id
    ORDER BY distinct_years ASC
    """)
    bs_results = cursor.fetchall()

    print("Balance Sheet Distinct Years per Company:")
    bs_under_10 = 0
    for company_id, years in bs_results:
        if years < 10:
            bs_under_10 += 1
        print(f"Company {company_id}: {years} years")
    print(f"Companies with <10 BS years: {bs_under_10}/92\n")

    # Cash Flow
    cursor.execute("""
    SELECT
        company_id,
        COUNT(DISTINCT SUBSTR(year, 1, 4)) as distinct_years
    FROM cashflow
    GROUP BY company_id
    ORDER BY distinct_years ASC
    """)
    cf_results = cursor.fetchall()

    print("Cash Flow Distinct Years per Company:")
    cf_under_10 = 0
    for company_id, years in cf_results:
        if years < 10:
            cf_under_10 += 1
        print(f"Company {company_id}: {years} years")
    print(f"Companies with <10 CF years: {cf_under_10}/92\n")

    # Combined check - companies with >=10 years in ALL THREE tables
    cursor.execute("""
    WITH pl_years AS (
        SELECT company_id, COUNT(DISTINCT SUBSTR(year, 1, 4)) as years
        FROM profitandloss
        GROUP BY company_id
    ),
    bs_years AS (
        SELECT company_id, COUNT(DISTINCT SUBSTR(year, 1, 4)) as years
        FROM balancesheet
        GROUP BY company_id
    ),
    cf_years AS (
        SELECT company_id, COUNT(DISTINCT SUBSTR(year, 1, 4)) as years
        FROM cashflow
        GROUP BY company_id
    )
    SELECT
        pl_years.company_id,
        pl_years.years as pl_years,
        bs_years.years as bs_years,
        cf_years.years as cf_years
    FROM pl_years
    JOIN bs_years ON pl_years.company_id = bs_years.company_id
    JOIN cf_years ON pl_years.company_id = cf_years.company_id
    WHERE pl_years.years >= 10 AND bs_years.years >= 10 AND cf_years.years >= 10
    ORDER BY pl_years.company_id
    """)

    passing_companies = cursor.fetchall()
    print(f"Companies with >=10 years in ALL THREE tables: {len(passing_companies)}/92")
    print("Passing companies:")
    for company_id, pl, bs, cf in passing_companies:
        print(f"  {company_id}: P&L={pl}, BS={bs}, CF={cf}")

    conn.close()

if __name__ == "__main__":
    check_data_depth()