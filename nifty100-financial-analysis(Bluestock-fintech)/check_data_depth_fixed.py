import sqlite3
import re
from pathlib import Path

def extract_year_from_string(date_str):
    """Extract 4-digit year from various date formats"""
    if not isinstance(date_str, str):
        return None

    # Handle formats like "Dec 2012" or "Mar 2014"
    match = re.search(r'(\d{4})', date_str)
    if match:
        return match.group(1)

    # Handle formats like "Mar-13" or "Mar-14"
    match = re.search(r'-(\d{2})$', date_str)
    if match:
        year_2digit = match.group(1)
        # Assume 20xx for years 00-29, 19xx for 30-99 (adjust as needed)
        year_int = int(year_2digit)
        if year_int <= 29:
            return f"20{year_2digit:02d}"
        else:
            return f"19{year_2digit:02d}"

    return None

def check_data_depth():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    # Check distinct years for each company in each table
    query = """
    SELECT
        company_id,
        year
    FROM profitandloss
    ORDER BY company_id
    """

    cursor = conn.cursor()
    cursor.execute(query)
    pl_rows = cursor.fetchall()

    # Process P&L years
    pl_years_by_company = {}
    for company_id, year_str in pl_rows:
        if company_id not in pl_years_by_company:
            pl_years_by_company[company_id] = set()
        year = extract_year_from_string(year_str)
        if year:
            pl_years_by_company[company_id].add(year)

    print("P&L Distinct Years per Company:")
    pl_under_10 = 0
    for company_id in sorted(pl_years_by_company.keys()):
        years = sorted(list(pl_years_by_company[company_id]))
        count = len(years)
        if count < 10:
            pl_under_10 += 1
        print(f"Company {company_id}: {count} years {years}")
    print(f"Companies with <10 P&L years: {pl_under_10}/92\n")

    # Balance Sheet
    cursor.execute("""
    SELECT
        company_id,
        year
    FROM balancesheet
    ORDER BY company_id
    """)
    bs_rows = cursor.fetchall()

    # Process BS years
    bs_years_by_company = {}
    for company_id, year_str in bs_rows:
        if company_id not in bs_years_by_company:
            bs_years_by_company[company_id] = set()
        year = extract_year_from_string(year_str)
        if year:
            bs_years_by_company[company_id].add(year)

    print("Balance Sheet Distinct Years per Company:")
    bs_under_10 = 0
    for company_id in sorted(bs_years_by_company.keys()):
        years = sorted(list(bs_years_by_company[company_id]))
        count = len(years)
        if count < 10:
            bs_under_10 += 1
        print(f"Company {company_id}: {count} years {years}")
    print(f"Companies with <10 BS years: {bs_under_10}/92\n")

    # Cash Flow
    cursor.execute("""
    SELECT
        company_id,
        year
    FROM cashflow
    ORDER BY company_id
    """)
    cf_rows = cursor.fetchall()

    # Process CF years
    cf_years_by_company = {}
    for company_id, year_str in cf_rows:
        if company_id not in cf_years_by_company:
            cf_years_by_company[company_id] = set()
        year = extract_year_from_string(year_str)
        if year:
            cf_years_by_company[company_id].add(year)

    print("Cash Flow Distinct Years per Company:")
    cf_under_10 = 0
    for company_id in sorted(cf_years_by_company.keys()):
        years = sorted(list(cf_years_by_company[company_id]))
        count = len(years)
        if count < 10:
            cf_under_10 += 1
        print(f"Company {company_id}: {count} years {years}")
    print(f"Companies with <10 CF years: {cf_under_10}/92\n")

    # Combined check - companies with >=10 years in ALL THREE tables
    all_company_ids = set(pl_years_by_company.keys()) & set(bs_years_by_company.keys()) & set(cf_years_by_company.keys())

    passing_companies = []
    for company_id in sorted(all_company_ids):
        pl_years = pl_years_by_company.get(company_id, set())
        bs_years = bs_years_by_company.get(company_id, set())
        cf_years = cf_years_by_company.get(company_id, set())

        if len(pl_years) >= 10 and len(bs_years) >= 10 and len(cf_years) >= 10:
            passing_companies.append((company_id, len(pl_years), len(bs_years), len(cf_years)))

    print(f"Companies with >=10 years in ALL THREE tables: {len(passing_companies)}/92")
    print("Passing companies:")
    for company_id, pl_count, bs_count, cf_count in passing_companies:
        print(f"  {company_id}: P&L={pl_count}, BS={bs_count}, CF={cf_count}")

    conn.close()

if __name__ == "__main__":
    check_data_depth()