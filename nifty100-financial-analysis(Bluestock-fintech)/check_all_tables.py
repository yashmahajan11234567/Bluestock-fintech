import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cursor = conn.cursor()

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;")
for row in cursor.fetchall():
    print(f'=== {row[0]} ===')
    print(row[1])
    print()

conn.close()