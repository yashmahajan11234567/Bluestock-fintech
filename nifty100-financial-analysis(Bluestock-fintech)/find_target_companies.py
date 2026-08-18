import sqlite3
from pathlib import Path

def find_target_companies():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name FROM companies ORDER BY id")
    companies = cursor.fetchall()

    # Target companies from dispute report
    target_names = [
        'M&MFIN', 'MANAPPURAM', 'MUTHOOTFIN', 'NATIONALUM',
        'NAUKRI', 'NAVINFLUOR', 'NESTLEIND', 'NICHROM',
        'NIITLTD', 'NIITTECH'
    ]

    print("Searching for target companies:")
    for target in target_names:
        found = False
        for cid, name in companies:
            # Check if target is in company ID or name (case insensitive)
            if target.upper() in cid.upper() or target.upper() in name.upper():
                print(f"Found '{target}': {cid} - {name}")
                found = True
                break
        if not found:
            print(f"NOT FOUND: {target}")

    # Also show all company IDs for manual inspection
    print("\nAll company IDs:")
    for cid, name in companies:
        print(f"{cid}: {name}")

    conn.close()

if __name__ == "__main__":
    find_target_companies()