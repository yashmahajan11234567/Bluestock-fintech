import csv
from collections import defaultdict

path = 'Data/output/pros_cons_generated.csv'
with open(path, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

companies = sorted({r['company_id'] for r in rows})
by_company = defaultdict(lambda: {'pro': [], 'con': []})
for r in rows:
    by_company[r['company_id']][r['type'].lower()].append(r)

print('Companies:', companies)
print('Company count:', len(companies))
print('Pro/con summary:')
for c in companies:
    print(c, 'pros=', len(by_company[c]['pro']), 'cons=', len(by_company[c]['con']))
print('Missing pros:', [c for c in companies if not by_company[c]['pro']])
print('Missing cons:', [c for c in companies if not by_company[c]['con']])
print('TEST-only held rows:', [r for r in rows if r['company_id'] == 'TEST'])