import sqlite3

def check_ac02():
    conn = sqlite3.connect('nifty100-financial-analysis(Bluestock-fintech)/db/nifty100.db')
    c = conn.cursor()

    # Get all company IDs
    c.execute("SELECT id FROM companies")
    company_ids = [row[0] for row in c.fetchall()]

    qualifying_companies = []

    for company_id in company_ids:
        # Get distinct years for each statement type
        c.execute("SELECT DISTINCT year FROM profitandloss WHERE company_id = ?", (company_id,))
        pl_years = len(c.fetchall())

        c.execute("SELECT DISTINCT year FROM balancesheet WHERE company_id = ?", (company_id,))
        bs_years = len(c.fetchall())

        c.execute("SELECT DISTINCT year FROM cashflow WHERE company_id = ?", (company_id,))
        cf_years = len(c.fetchall())

        # Company qualifies if all three have >=10 years
        if pl_years >= 10 and bs_years >= 10 and cf_years >= 10:
            qualifying_companies.append(company_id)

    total_companies = len(company_ids)
    qualifying_count = len(qualifying_companies)
    percentage = (qualifying_count / total_companies) * 100

    print(f"Qualifying companies: {qualifying_count}")
    print(f"Total companies: {total_companies}")
    print(f"Percentage: {percentage:.2f}%")

    # List qualifying company IDs for verification
    if qualifying_count <= 20:  # Only show if reasonable number
        print(f"Qualifying company IDs: {qualifying_companies}")
    else:
        print(f"First 10 qualifying company IDs: {qualifying_companies[:10]}")

    conn.close()

    return qualifying_count, total_companies, percentage

if __name__ == "__main__":
    check_ac02()