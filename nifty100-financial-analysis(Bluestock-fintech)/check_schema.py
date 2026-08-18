import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='financial_ratios'")
print('financial_ratios CREATE:')
for row in cursor.fetchall():
    print(row)

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='companies'")
print('\ncompanies CREATE:')
for row in cursor.fetchall():
    print(row)

conn.close()