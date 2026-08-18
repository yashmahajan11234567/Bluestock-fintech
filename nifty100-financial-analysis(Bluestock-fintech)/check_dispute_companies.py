import sqlite3
from pathlib import Path

def check_dispute_companies():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name FROM companies ORDER BY id")
    companies = {row[0]: row[1] for row in cursor.fetchall()}

    # Map from dispute report names to actual company IDs in DB
    dispute_to_db = {
        'M&MFIN': 'M&M',  # Mahindra & Mahindra Ltd
        'MANAPPURAM': None,  # Not found
        'MUTHOOTFIN': None,  # Not found
        'NATIONALUM': None,  # Not found
        'NAUKRI': 'NAUKRI',  # Info Edge (India) Ltd
        'NAVINFLUOR': None,  # Not found
        'NESTLEIND': 'NESTLEIND',  # Nestle India Ltd
        'NICHROM': None,  # Not found
        'NIITLTD': None,  # Not found
        'NIITTECH': None   # Not found
    }

    # Also try to find partial matches
    all_company_ids = list(companies.keys())

    for dispute_name in ['M&MFIN', 'MANAPPURAM', 'MUTHOOTFIN', 'NATIONALUM', 'NAUKRI', 'NAVINFLUOR', 'NESTLEIND', 'NICHROM', 'NIITLTD', 'NIITTECH']:
        if dispute_name in dispute_to_db and dispute_to_db[dispute_name]:
            company_id = dispute_to_db[dispute_name]
            company_name = companies.get(company_id, "Unknown")
            print(f"\n{dispute_name} -> {company_id}: {company_name}")

            # Check P&L years
            cursor.execute("""
            SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
            FROM profitandloss
            WHERE company_id = ?
            """, (company_id,))
            pl_years = cursor.fetchone()[0]

            # Check BS years
            cursor.execute("""
            SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
            FROM balancesheet
            WHERE company_id = ?
            """, (company_id,))
            bs_years = cursor.fetchone()[0]

            # Check CF years
            cursor.execute("""
            SELECT COUNT(DISTINCT SUBSTR(year, 1, 4))
            FROM cashflow
            WHERE company_id = ?
            """, (company_id,))
            cf_years = cursor.fetchone()[0]

            print(f"  P&L years: {pl_years}")
            print(f"  BS years: {bs_years}")
            print(f"  CF years: {cf_years}")
            print(f"  Passes all three (>=10 each): {pl_years >= 10 and bs_years >= 10 and cf_years >= 10}")
        else:
            print(f"\n{dispute_name}: NOT FOUND in database")

            # Try to find similar names
            similar = []
            for cid, name in companies.items():
                if (dispute_name.upper() in cid.upper() or
                    dispute_name.upper() in name.upper()):
                    similar.append((cid, name))

            if similar:
                print(f"  Similar matches found: {similar}")
            else:
                # Try first 4 characters
                prefix = dispute_name.upper()[:4]
                for cid, name in companies.items():
                    if (prefix in cid.upper() or prefix in name.upper()):
                        similar.append((cid, name))
                if similar:
                    print(f"  Matches on first 4 chars '{prefix}': {similar[:5]}")

    conn.close()

if __name__ == "__main__":
    check_dispute_companies()