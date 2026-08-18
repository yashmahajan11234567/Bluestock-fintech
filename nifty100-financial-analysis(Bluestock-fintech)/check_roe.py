import sqlite3
conn = sqlite3.connect('db/nifty100.db')
cursor = conn.cursor()
for cid in ['TCS', 'INFY', 'HDFCBANK', 'RELIANCE', 'ICICIBANK']:
    # Get latest non-NULL ROE
    cursor.execute('SELECT return_on_equity_pct FROM financial_ratios WHERE company_id = ? AND return_on_equity_pct IS NOT NULL ORDER BY year DESC LIMIT 1', (cid,))
    row = cursor.fetchone()
    print(f'{cid} latest ROE: {row[0] if row else "N/A"}')