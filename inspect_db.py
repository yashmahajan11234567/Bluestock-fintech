import sqlite3
import os

# Connect to database
db_path = 'nifty100-financial-analysis(Bluestock-fintech)/db/nifty100.db'
print(f'Checking database: {db_path}')
print(f'Exists: {os.path.exists(db_path)}')
if os.path.exists(db_path):
    print(f'Size: {os.path.getsize(db_path)} bytes')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table names
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print(f'Table count: {len(tables)}')
for table in tables:
    print(f'  - {table[0]}')

# Check balancesheet structure
print('\nBalancesheet table:')
cursor.execute('PRAGMA table_info(balancesheet)')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Check balancesheet year values
print('\nBalancesheet year analysis:')
cursor.execute('SELECT COUNT(*) FROM balancesheet')
total_rows = cursor.fetchone()[0]
print(f'Total rows: {total_rows}')

cursor.execute('SELECT COUNT(*) FROM balancesheet WHERE year IS NULL')
null_years = cursor.fetchone()[0]
print(f'NULL years: {null_years} ({null_years/total_rows*100:.1f}%)')

cursor.execute('SELECT COUNT(DISTINCT year) FROM balancesheet WHERE year IS NOT NULL')
unique_years = cursor.fetchone()[0]
print(f'Unique non-NULL years: {unique_years}')

# Sample some year values
print('\nSample year values from balancesheet:')
cursor.execute('SELECT company_id, year FROM balancesheet WHERE year IS NOT NULL LIMIT 5')
samples = cursor.fetchall()
for sample in samples:
    print(f'  Company: {sample[0]}, Year: {sample[1]}')

# Check profitandloss year values
print('\nProfitandloss year analysis:')
cursor.execute('SELECT COUNT(*) FROM profitandloss')
total_pnl = cursor.fetchone()[0]
print(f'Total rows: {total_pnl}')

cursor.execute('SELECT COUNT(*) FROM profitandloss WHERE year IS NULL')
null_pnl = cursor.fetchone()[0]
print(f'NULL years: {null_pnl} ({null_pnl/total_pnl*100:.1f}%)')

conn.close()