import sqlite3
from pathlib import Path

def check_company_ids():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name FROM companies ORDER BY id")
    companies = cursor.fetchall()

    print("First 20 companies:")
    for i, (cid, name) in enumerate(companies[:20]):
        print(f"{i+1:2}. {cid}: {name}")

    # Check for specific companies mentioned in the dispute report
    target_companies = ['M&MFIN', 'MANAPPURAM', 'MUTHOOTFIN', 'NATIONALUM', 'NAUKRI', 'NAVINFLUOR', 'NESTLEIND', 'NICHROM', 'NIITLTD', 'NIITTECH']
    print("\nChecking for target companies:")
    for target in target_companies:
        found = False
        for cid, name in companies:
            if target in cid or target in name:
                print(f"Found: {cid} - {name}")
                found = True
                break
        if not found:
            print(f"Not found: {target}")

    conn.close()

if __name__ == "__main__":
    check_company_ids()