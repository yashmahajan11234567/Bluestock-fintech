import sqlite3
import pandas as pd
DB_PATH = r'C:\Users\hitoy\Downloads\Bluestock_fintech\nifty100-financial-analysis(Bluestock-fintech)\db\nifty100.db'
conn = sqlite3.connect(DB_PATH)

# Get the schema of the profit and loss table
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='profitandloss'")
schema = cursor.fetchone()
if schema:
    print('Profit and Loss table schema:')
    print(schema[0])
else:
    print('Table not found')

# Get sample data
print('\nSample data from profitandloss:')
df = pd.read_sql_query("SELECT * FROM profitandloss LIMIT 3", conn)
print(df.head())

conn.close()