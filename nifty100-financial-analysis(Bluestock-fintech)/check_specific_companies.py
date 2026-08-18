import sqlite3
from pathlib import Path

def check_specific_companies():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name FROM companies ORDER BY id")
    companies = cursor.fetchall()

    # Map from dispute report names to possible matches
    company_mapping = {
        'M&MFIN': ['M&M', 'M&M Limited', 'Mahindra & Mahindra'],
        'MANAPPURAM': ['Manappuram', 'Manappuram Finance'],
        'MUTHOOTFIN': ['Muthoot', 'Muthoot Finance'],
        'NATIONALUM': ['National Aluminium', 'NATIONALUM', 'NALCO'],
        'NAUKRI': ['NAUKRI', 'Info Edge'],
        'NAVINFLUOR': ['Navin Fluorine', 'NAVINFLUOR'],
        'NESTLEIND': ['NESTLEIND', 'Nestle India'],
        'NICHROM': ['Nichrome', 'NICHROM'],
        'NIITLTD': ['NIIT', 'NIIT Ltd'],
        'NIITTECH': ['NIIT Technologies', 'NIITTECH']
    }

    print("Checking for specific companies from dispute report:")
    for target, possible_names in company_mapping.items():
        found = False
        for cid, name in companies:
            # Check if any possible name matches company ID or name
            for possible in possible_names:
                if possible.upper() in cid.upper() or possible.upper() in name.upper():
                    print(f"Found '{target}' as '{cid}': {name}")
                    found = True
                    break
            if found:
                break
        if not found:
            print(f"NOT FOUND: {target}")
            # Show similar names for debugging
            similar = []
            for cid, name in companies:
                for possible in possible_names:
                    if (possible.upper()[:4] in cid.upper() or
                        possible.upper()[:4] in name.upper() or
                        cid.upper()[:4] in possible.upper() or
                        name.upper()[:4] in possible.upper()):
                        similar.append((cid, name))
            if similar:
                print(f"  Similar matches: {similar[:5]}")

    conn.close()

if __name__ == "__main__":
    check_specific_companies()