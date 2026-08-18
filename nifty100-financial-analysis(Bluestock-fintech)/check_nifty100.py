import sqlite3
from pathlib import Path

def check_nifty100_companies():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name FROM companies ORDER BY id")
    companies = cursor.fetchall()

    print(f"Total companies in database: {len(companies)}")
    print("\nFirst 30 companies:")
    for i, (cid, name) in enumerate(companies[:30]):
        print(f"{i+1:2}. {cid}: {name}")

    print("\nLast 30 companies:")
    for i, (cid, name) in enumerate(companies[-30:], len(companies)-29):
        print(f"{i:2}. {cid}: {name}")

    # Check for missing companies that should be in Nifty 100
    # Based on common Nifty 100 constituents as of 2024
    expected_companies = [
        'M&MFIN', 'MANAPPURAM', 'MUTHOOTFIN', 'NATIONALUM',
        'NAUKRI', 'NAVINFLUOR', 'NESTLEIND', 'NICHROM',
        'NIITLTD', 'NIITTECH', 'SBIN', 'ICICIBANK', 'HDFCBANK',
        'KOTAKBANK', 'AXISBANK', 'INDUSINDBK', 'YES BANK',
        'SBILIFE', 'HDFCLIFE', 'ICICIPRULI', 'ICICIGI',
        'BAJFINANCE', 'CHOLAFIN', 'SHRIRAMFIN', 'MUTHOOT',
        'RECLTD', 'PFC', 'RELIANCE', 'TCS', 'INFY', 'HCLTECH',
        'TECHM', 'WIPRO', 'LTIM', 'LT', 'Ultratech Cement',
        'GRASIM', 'AMBUJACEM', 'SHREECEM', 'ACC', 'DLF',
        'GODREJPROP', 'MOTHERSON', 'MARUTI', 'TATAMOTORS',
        'M&M', 'EICHERMOT', 'BAJAJ-AUTO', 'HEROMOTOCO',
        'TVSMOTOR', 'ASIANPAINT', 'BERGERPAINT', 'HINDUNILVR',
        'GODREJCP', 'DABUR', 'MARICO', 'COALINDIA', 'NTPC',
        'POWERGRID', 'ADANIPORTS', 'ADANIGREEN', 'ADANIENT',
        'JSWSTEEL', 'TATASTEEL', 'JINDALSTEL', 'SAIL',
        'HINDALCO', 'VEDL', 'ONGC', 'IOC', 'BPCL', 'GAIL',
        'IOL', 'NIFTY BANK', 'NIFTY IT'
    ]

    print("\nChecking for expected Nifty 100 companies:")
    found_count = 0
    not_found = []

    for expected in expected_companies:
        found = False
        for cid, name in companies:
            if (expected.upper() in cid.upper() or
                expected.upper() in name.upper() or
                cid.upper() == expected.upper()):
                found = True
                found_count += 1
                break
        if not found:
            not_found.append(expected)

    print(f"Found {found_count}/{len(expected_companies)} expected companies")
    if not_found:
        print(f"Not found: {not_found[:20]}")  # Show first 20

    conn.close()

if __name__ == "__main__":
    check_nifty100_companies()