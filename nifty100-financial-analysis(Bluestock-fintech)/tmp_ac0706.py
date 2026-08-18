import sqlite3
from pathlib import Path

conn = sqlite3.connect('db/nifty100.db')
cur = conn.cursor()

# AC-05 spot-check sample
cur.execute('''
SELECT pl.company_id,
       COUNT(DISTINCT pl.year) AS pl_years,
       COUNT(DISTINCT bs.year) AS bs_years,
       COUNT(DISTINCT cf.year) AS cf_years,
       MAX(pl.year) AS pl_max_year,
       MIN(pl.year) AS pl_min_year
FROM profitandloss pl
JOIN balancesheet bs ON bs.company_id = pl.company_id
JOIN cashflow cf ON cf.company_id = pl.company_id
GROUP BY pl.company_id
ORDER BY pl_years DESC
LIMIT 5
''')
ac05 = cur.fetchall()
print('AC-05 samples:', ac05)

# AC-06 ROE for 5 required companies
required = ['HDFCBANK', 'TCS', 'RELIANCE', 'INFY', 'SBIN']
cur.execute('''
SELECT p.company_id,
       SUM(CASE WHEN p.year = bs.year THEN p.net_profit ELSE 0 END) as net_profit,
       SUM(CASE WHEN p.year = bs.year THEN bs.equity_capital + bs.reserves ELSE 0 END) as equity
FROM profitandloss p
JOIN balancesheet bs ON bs.company_id = p.company_id
WHERE p.company_id IN ('HDFCBANK','TCS','RELIANCE','INFY','SBIN')
GROUP BY p.company_id
''')
ac06 = cur.fetchall()
print('AC-06 spot-check:', ac06)

# AC-07 endpoint path
print('AC-07: check router path manually later')

# AC-12 endpoint path

conn.close()

# AC-10 checks - reports/tearsheets PDFs
papers = Path('reports/tearsheets').glob('*.pdf')
below_threshold = [p.name for p in papers if p.stat().st_size < 31_072]
print('Below-threshold PDFs:', len(below_threshold), below_threshold[:20])