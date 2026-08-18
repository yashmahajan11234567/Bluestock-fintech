import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cursor = conn.cursor()

# Count total companies
cursor.execute('SELECT COUNT(*) FROM companies;')
company_count = cursor.fetchone()[0]
print(f'Total companies: {company_count}')

# Count distinct companies in financial_ratios
cursor.execute('SELECT COUNT(DISTINCT company_id) FROM financial_ratios;')
fr_company_count = cursor.fetchone()[0]
print(f'Companies with financial ratios: {fr_company_count}')

# Show first 10 companies with their ratio counts
cursor.execute('''
    SELECT company_id, COUNT(*) as ratio_count
    FROM financial_ratios
    GROUP BY company_id
    ORDER BY company_id
    LIMIT 10;
''')
results = cursor.fetchall()
print('\nFirst 10 companies in financial_ratios:')
for row in results:
    print(f'  {row[0]}: {row[1]} ratios')

# Check if TEST company exists
cursor.execute("SELECT COUNT(*) FROM companies WHERE company_id = 'TEST';")
test_count = cursor.fetchone()[0]
print(f'\nTEST company exists: {test_count > 0}')

conn.close()