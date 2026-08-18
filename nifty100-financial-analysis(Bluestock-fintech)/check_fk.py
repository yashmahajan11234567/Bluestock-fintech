import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_key_list(financial_ratios);")
print('FK LIST financial_ratios:')
for row in cursor.fetchall():
    print(row)

cursor.execute("PRAGMA index_list(financial_ratios);")
print('\nINDEX LIST financial_ratios:')
for row in cursor.fetchall():
    print(row)

conn.close()