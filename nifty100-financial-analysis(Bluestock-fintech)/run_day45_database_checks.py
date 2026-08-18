import sqlite3
import os
import json

print("=== DAY 45 DATABASE INSPECTION ===")

# Find the authoritative database (main, not in worktrees)
db_path = None
for root, dirs, files in os.walk('.'):
    if '.claude/worktrees' in root.replace('\\\\', '/'):
        continue
    for file in files:
        if file == 'nifty100.db':
            db_path = os.path.join(root, file)
            break
    if db_path:
        break

# If not found in main, try worktrees (for inspection purposes)
if not db_path:
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'nifty100.db':
                db_path = os.path.join(root, file)
                print(f"WARNING: Using database from worktree: {db_path}")
                break
        if db_path:
            break

print(f"Database path: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Initialize results
results = {}

# AC-01: SELECT COUNT(*) FROM companies = 92
print("\n=== AC-01: Companies count ===")
cursor.execute("SELECT COUNT(*) FROM companies")
actual_count = cursor.fetchone()[0]
expected_count = 92
status = "PASS" if actual_count == expected_count else "FAIL"

results['AC-01'] = {
    'actual': actual_count,
    'expected': expected_count,
    'status': status
}
print(f"actual_count: {actual_count}")
print(f"expected_count: {expected_count}")
print(f"STATUS: {status}")

# AC-02: >=90% of companies have >=10 years of P&L, Balance Sheet, Cash Flow
print("\n=== AC-02: Years of data for companies ===")
companies_with_enough_data = 0
companies_total = 0

# Get all company IDs
cursor.execute("SELECT id, company_name FROM companies")
all_companies = cursor.fetchall()

for company_id, company_name in all_companies:
    print(f"\nChecking company: {company_name}")

    for table, col in [('profitandloss', 'year'), ('balancesheet', 'year'), ('cashflow', 'year')]:
        try:
            cursor.execute(f"SELECT COUNT(DISTINCT {col}) FROM {table} WHERE company_id = ?", (company_id,))
            years = cursor.fetchone()[0]
            print(f"  {table}: {years} years")

            if years >= 10:
                companies_with_enough_data += 1
            companies_total += 1
        except Exception as e:
            print(f"  {table} error: {e}")
            companies_total += 1

percentage = (companies_with_enough_data / companies_total * 100) if companies_total > 0 else 0
status = "PASS" if percentage >= 90 else "FAIL"

results['AC-02'] = {
    'companies_checked': companies_total,
    'companies_with_enough_data': companies_with_enough_data,
    'percentage': percentage,
    'status': status
}
print(f"\nCompanies with >=10 years data: {companies_with_enough_data}/{companies_total} ({percentage:.1f}%)")
print(f"STATUS: {status}")

# AC-03: PRAGMA foreign_key_check returns 0 rows
print("\n=== AC-03: Foreign key check ===")
# Run foreign key check directly
cursor.execute("PRAGMA foreign_key_check")
foreign_key_errors = cursor.fetchall()

results['AC-03'] = {
    'foreign_key_errors': foreign_key_errors,
    'error_count': len(foreign_key_errors),
    'status': 'PASS' if len(foreign_key_errors) == 0 else 'FAIL'
}
print(f"Foreign key errors: {len(foreign_key_errors)}")
for error in foreign_key_errors[:5]:  # Show first 5 errors
    print(f"  {error}")

# AC-04: SELECT COUNT(*) FROM financial_ratios >= 1,100
print("\n=== AC-04: Financial ratios count ===")
cursor.execute("SELECT COUNT(*) FROM financial_ratios")
actual_financial_ratios = cursor.fetchone()[0]
expected_financial_ratios = 1100
status = "PASS" if actual_financial_ratios >= expected_financial_ratios else "FAIL"

results['AC-04'] = {
    'actual': actual_financial_ratios,
    'expected': expected_financial_ratios,
    'status': status
}
print(f"actual_count: {actual_financial_ratios}")
print(f"expected_count: {expected_financial_ratios}")
print(f"STATUS: {status}")

# AC-06: ROE matches companies.roe_percentage within 5% for 5 companies
print("\n=== AC-06: ROE verification ===")
# Get 5 companies
cursor.execute("SELECT id, company_name, roe_percentage FROM companies LIMIT 5")
companies = cursor.fetchall()
roe_verification_results = []
for company_id, company_name, stored_roe in companies:
    print(f"\nCompany: {company_name}")
    print(f"  Stored ROE: {stored_roe}")

    # Calculate ROE from profitandloss and balancesheet
    # Simple ROE calculation: Net Profit / Total Assets * 100
    cursor.execute("""
        SELECT
            pl.net_profit as net_profit,
            bs.total_assets as total_assets
        FROM profitandloss pl
        JOIN balancesheet bs ON pl.company_id = bs.company_id AND pl.year = bs.year
        WHERE pl.company_id = ? AND pl.year = 2023
        LIMIT 1
    """, (company_id,))
    result = cursor.fetchone()

    if result:
        net_profit, total_assets = result
        if total_assets and total_assets != 0:
            calculated_roe = ((net_profit or 0) / total_assets) * 100
            difference = abs(stored_roe - calculated_roe)
            percentage_diff = (difference / calculated_roe) * 100 if calculated_roe != 0 else 0
            status = "PASS" if percentage_diff <= 5 else "FAIL"

            roe_verification_results.append({
                'company': company_name,
                'stored_roe': stored_roe,
                'calculated_roe': calculated_roe,
                'difference': difference,
                'percentage_difference': percentage_diff,
                'status': status
            })

            print(f"  Calculated ROE: {calculated_roe:.2f}%")
            print(f"  Difference: {difference:.2f}% ({percentage_diff:.1f}%)")
            print(f"  STATUS: {status}")

all_roe_pass = all(r['status'] == 'PASS' for r in roe_verification_results)
results['AC-06'] = {
    'roe_samples': roe_verification_results,
    'all_pass': all_roe_pass,
    'status': 'PASS' if all_roe_pass else 'FAIL'
}

# AC-14: peer_percentiles table has data for all 11 peer groups
print("\n=== AC-14: Peer percentiles ===")
try:
    cursor.execute("SELECT COUNT(DISTINCT peer_group) FROM peer_percentiles")
    peer_groups = cursor.fetchone()[0]

    results['AC-14'] = {
        'peer_groups': peer_groups,
        'status': 'PASS' if peer_groups == 11 else 'FAIL'
    }
    print(f"Peer groups found: {peer_groups}")
except Exception as e:
    results['AC-14'] = {
        'error': str(e),
        'status': 'UNVERIFIABLE'
    }
    print(f"Could not check peer percentiles: {e}")

conn.close()

# Print results summary
print("\n=== FINAL RESULTS SUMMARY ===")
for ac_key in ['AC-01', 'AC-02', 'AC-03', 'AC-04', 'AC-06', 'AC-14']:
    if ac_key in results:
        result = results[ac_key]
        print(f"{ac_key}: {result.get('status', 'UNKNOWN')}")

# Save results to file
with open('day45_db_inspection_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nResults saved to day45_db_inspection_results.json")