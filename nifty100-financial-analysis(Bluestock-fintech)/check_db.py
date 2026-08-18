import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM companies WHERE id LIKE '%ULTRA%' OR id LIKE '%UNION%'")
print('=== COMPANIES WITH ULTRA/UNION ===')
for row in cursor.fetchall():
    print(row)

cursor.execute('SELECT id, company_name FROM companies ORDER BY id')
print('\n=== ALL COMPANIES ===')
for row in cursor.fetchall():
    print(row)

conn.close()