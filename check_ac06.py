import sqlite3

def check_ac06():
    conn = sqlite3.connect('nifty100-financial-analysis(Bluestock-fintech)/db/nifty100.db')
    c = conn.cursor()

    # List of companies to check (including TCS)
    companies_to_check = ['TCS', 'ABB', 'ADANIENT', 'ASIANPAINT', 'AXISBANK']

    results = []

    for company_id in companies_to_check:
        # Get stored ROE from companies table
        c.execute('''
            SELECT roe_percentage
            FROM companies
            WHERE id = ?
        ''', (company_id,))
        stored_row = c.fetchone()
        stored_roe = stored_row[0] if stored_row else None

        # Get most recent non-TTM ROE from financial_ratios
        c.execute('''
            SELECT return_on_equity_pct
            FROM financial_ratios
            WHERE company_id = ? AND year != 'TTM'
            ORDER BY year DESC
            LIMIT 1
        ''', (company_id,))
        computed_row = c.fetchone()
        computed_roe = computed_row[0] if computed_row else None

        if stored_roe is not None and computed_roe is not None:
            diff = abs(stored_roe - computed_roe)
            within = diff <= 5.0  # within 5 percentage points
            results.append({
                'company': company_id,
                'stored': stored_roe,
                'computed': computed_roe,
                'difference': diff,
                'within': within
            })
            print(f"{company_id}: stored={stored_roe}, computed={computed_roe}, diff={diff:.2f}, within={within}")
        else:
            print(f"{company_id}: missing data - stored={stored_roe}, computed={computed_roe}")
            results.append({
                'company': company_id,
                'stored': stored_roe,
                'computed': computed_roe,
                'difference': None,
                'within': False
            })

    # Summary
    passed = sum(1 for r in results if r['within'])
    total = len([r for r in results if r['difference'] is not None])
    print(f"\nPassed: {passed}/{total}")

    if passed == total and total > 0:
        print("AC-06: PASS")
        return True
    else:
        print("AC-06: FAIL")
        return False

if __name__ == "__main__":
    check_ac06()
    conn.close()