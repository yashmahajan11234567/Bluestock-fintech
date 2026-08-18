import sqlite3, csv, math
from pathlib import Path
from collections import defaultdict

DB = 'db/nifty100.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

# AC-01
cur.execute('SELECT COUNT(*) FROM companies')
ac01 = cur.fetchone()[0]

# AC-02 - per canonical company by companies.id with normalized years
cur.execute('''
SELECT c.id,
       COUNT(DISTINCT pl.year) AS pl_years,
       COUNT(DISTINCT bs.year) AS bs_years,
       COUNT(DISTINCT cf.year) AS cf_years
FROM companies c
LEFT JOIN profitandloss pl ON pl.company_id = c.id
LEFT JOIN balancesheet bs ON bs.company_id = c.id
LEFT JOIN cashflow cf ON cf.company_id = c.id
GROUP BY c.id
ORDER BY c.id
''')
rows = cur.fetchall()
qualifying = [r for r in rows if r[1] >= 10 and r[2] >= 10 and r[3] >= 10]
non_qualifying = [r for r in rows if not (r[1] >= 10 and r[2] >= 10 and r[3] >= 10)]
threshold = math.ceil(ac01 * 0.90)
ac02 = 'PASS' if len(qualifying) >= threshold else 'FAIL'

# AC-03
cur.execute('PRAGMA foreign_key_check')
ac03_rows = cur.fetchall()
ac03 = 'PASS' if len(ac03_rows) == 0 else 'FAIL'

# AC-04
cur.execute('SELECT COUNT(*) FROM financial_ratios')
ac04 = cur.fetchone()[0]
ac04_status = 'PASS' if ac04 >= 1100 else 'FAIL'

# AC-16
csv_path = 'Data/output/pros_cons_generated.csv'
ac16 = None
ac16_detail = None
if not Path(csv_path).exists():
    ac16 = 'FAIL'
    ac16_detail = 'File missing'
else:
    with open(csv_path, newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
    companies = sorted({r['company_id'] for r in data})
    by_company = defaultdict(lambda: {'pro': [], 'con': []})
    for r in data:
        by_company[r['company_id']][r['type'].lower()].append(r)
    missing_pros = [c for c in companies if len(by_company[c]['pro']) < 1]
    missing_cons = [c for c in companies if len(by_company[c]['con']) < 1]
    all_have_both = not missing_pros and not missing_cons
    test_only = companies == ['TEST']
    ac16 = 'PASS' if len(companies) == ac01 and all_have_both and not test_only else 'FAIL'
    ac16_detail = f'companies={len(companies)}, qualify_both={sum(1 for c in companies if by_company[c]["pro"] and by_company[c]["con"])}, test_only={test_only}'

print('AC-01 companies:', ac01)
print('AC-02 qualifying:', len(qualifying), 'of', ac01, 'threshold', threshold, '=>', ac02)
print('AC-03 fk violations:', len(ac03_rows), '=>', ac03)
print('AC-04 financial_ratios:', ac04, '>=1100 =>', ac04_status)
print('AC-16:', ac16, ac16_detail)
print('NON-QUALIFYING companies:', non_qualifying)

conn.close()