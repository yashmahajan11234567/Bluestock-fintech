import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cur = conn.cursor()
for table in ['companies', 'profitandloss', 'balancesheet', 'cashflow', 'financial_ratios', 'prosandcons', 'peer_groups']:
    cur.execute(f'PRAGMA table_info({table})')
    cols = cur.fetchall()
    print('\n', table)
    for col in cols:
        print(' ', col)
conn.close()