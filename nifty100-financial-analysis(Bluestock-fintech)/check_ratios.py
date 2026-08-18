import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cursor = conn.cursor()

# Check duplicates in financial_ratios
cursor.execute('''
SELECT company_id, year, COUNT(*) as cnt
FROM financial_ratios
GROUP BY company_id, year
HAVING COUNT(*) > 1
''')
rows = cursor.fetchall()
print(f'Total duplicate company/year pairs: {len(rows)}')
total_extra = sum(r[2] - 1 for r in rows)
print(f'Total extra rows from duplicates: {total_extra}')

# Expected count without duplicates
cursor.execute('SELECT COUNT(*) FROM (SELECT DISTINCT company_id, year FROM financial_ratios)')
distinct_pairs = cursor.fetchone()[0]
print(f'Distinct company/year pairs: {distinct_pairs}')
print(f'Total rows: 3532')
print(f'Multiplication factor: {3532 / distinct_pairs:.2f}x')

conn.close()