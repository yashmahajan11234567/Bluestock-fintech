import sqlite3
import os

# Find the database files first
db_files = []
for root, dirs, files in os.walk('.'):
    # Skip worktrees directories
    if '.claude/worktrees' in root.replace('\\\\', '/'):
        continue
    for file in files:
        if file.endswith('.db'):
            full_path = os.path.join(root, file)
            db_files.append(full_path)
            print(f'Found database: {full_path}')

print(f'\nTotal database files found: {len(db_files)}')

# Try to connect to each database and check
for db_path in db_files:
    print(f'\n--- Checking database: {db_path} ---')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check companies table
        cursor.execute('SELECT COUNT(*) FROM companies')
        company_count = cursor.fetchone()[0]
        print(f'Companies count: {company_count}')

        # Check other key tables
        for table in ['profitandloss', 'balancesheet', 'cashflow', 'financial_ratios', 'peer_percentiles']:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f'{table} count: {count}')
            except sqlite3.Error as e:
                print(f'{table} error: {e}')

        conn.close()
    except Exception as e:
        print(f'Error connecting to {db_path}: {e}')