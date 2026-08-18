import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path('.')
DB_PATH = BASE_DIR / 'db' / 'nifty100.db'
OUTPUT_DIR = BASE_DIR / 'Data' / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV = OUTPUT_DIR / 'ac19_validation.csv'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Quick test - just check primary key uniqueness
failures = []
tables = [row[0] for row in cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')]
print('Tables:', tables)

for table in tables:
    query = f'SELECT id, company_id, COUNT(*) as cnt FROM {table} GROUP BY id, company_id HAVING cnt > 1'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        pk_value, company_id, count = row
        failures.append({
            'company_id': company_id,
            'field': f'{table}.id',
            'issue': f'Duplicate primary key: {pk_value} appears {count} times',
            'severity': 'CRITICAL'
        })

print(f'Found {len(failures)} primary key issues')
df = pd.DataFrame(failures)
if len(failures) > 0:
    df = df[['company_id', 'field', 'issue', 'severity']]
    df.to_csv(OUTPUT_CSV, index=False)
    print(f'Saved to {OUTPUT_CSV}')
    print(df.head())
else:
    df = pd.DataFrame(columns=['company_id', 'field', 'issue', 'severity'])
    df.to_csv(OUTPUT_CSV, index=False)
    print('No issues found')