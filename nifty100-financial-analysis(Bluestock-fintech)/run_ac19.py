import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path('.')
DB_PATH = BASE_DIR / 'db' / 'nifty100.db'
OUTPUT_DIR = BASE_DIR / 'Data' / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV = OUTPUT_DIR / 'ac19_validation.csv'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

failures = []

# Get table names
tables = [row[0] for row in cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')]
print('Tables:', tables)

# DQ-01: Primary key uniqueness
for table in tables:
    try:
        query = f'SELECT id, company_id, COUNT(*) as cnt FROM {table} GROUP BY id, company_id HAVING cnt > 1'
        rows = cursor.execute(query).fetchall()
        for row in rows:
            pk_value, company_id, count = row
            failures.append({
                'company_id': company_id,
                'field': f'{table}.id',
                'issue': f'Duplicate primary key: {pk_value} appears {count} times',
                'severity': 'CRITICAL'
            })
    except Exception as e:
        pass

# DQ-02: Composite key uniqueness
tables_columns = [
    ("profitandloss", "company_id", "year"),
    ("balancesheet", "company_id", "year"),
    ("cashflow", "company_id", "year"),
    ("financial_ratios", "company_id", "year"),
    ("documents", "company_id", "Year")
]
for table, col1, col2 in tables_columns:
    try:
        query = f'SELECT {col1}, {col2}, COUNT(*) as cnt FROM {table} GROUP BY {col1}, {col2} HAVING cnt > 1'
        rows = cursor.execute(query).fetchall()
        for row in rows:
            val1, val2, count = row
            failures.append({
                'company_id': val1,
                'field': f'{table}.{col1},{col2}',
                'issue': f'Duplicate composite key ({col1}={val1}, {col2}={val2}) appears {count} times',
                'severity': 'CRITICAL'
            })
    except Exception as e:
        pass

# DQ-03: Foreign key integrity
company_ids = set()
for row in cursor.execute('SELECT id FROM companies'):
    company_ids.add(row[0])

fk_tables = ["profitandloss", "balancesheet", "cashflow", "analysis", "documents", "prosandcons", "sectors", "financial_ratios", "stock_prices"]
for table in fk_tables:
    if company_ids:
        placeholders = ",".join(["?"] * len(company_ids))
        query = f"SELECT company_id, id FROM {table} WHERE company_id NOT IN ({placeholders})"
        rows = cursor.execute(query, tuple(company_ids)).fetchall()
    else:
        rows = cursor.execute(f"SELECT company_id, id FROM {table}").fetchall()
    for row in rows:
        company_id, row_id = row
        failures.append({
            'company_id': company_id,
            'field': f'{table}.company_id',
            'issue': f'Foreign key company_id={company_id} does not exist in companies table (row id: {row_id})',
            'severity': 'CRITICAL'
        })

# DQ-04: Balance sheet equation
try:
    query = 'SELECT company_id, id, total_assets, fixed_assets, cwip, investments, other_asset, total_liabilities, borrowings, other_liabilities, equity_capital, reserves FROM balancesheet'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, total_assets, fixed_assets, cwip, investments, other_asset, total_liabilities, borrowings, other_liabilities, equity_capital, reserves = row
        calculated_assets = (fixed_assets or 0) + (cwip or 0) + (investments or 0) + (other_asset or 0)
        calculated_liabilities = (borrowings or 0) + (other_liabilities or 0)
        tolerance = 0.01
        if abs(total_assets - calculated_assets) > tolerance:
            failures.append({
                'company_id': company_id,
                'field': 'balancesheet.total_assets',
                'issue': f'Total assets mismatch: expected {calculated_assets:.2f}, got {total_assets:.2f}',
                'severity': 'WARNING'
            })
        if abs(total_liabilities - calculated_liabilities) > tolerance:
            failures.append({
                'company_id': company_id,
                'field': 'balancesheet.total_liabilities',
                'issue': f'Total liabilities mismatch: expected {calculated_liabilities:.2f}, got {total_liabilities:.2f}',
                'severity': 'WARNING'
            })
        if abs(total_assets - (total_liabilities + (equity_capital or 0) + (reserves or 0))) > tolerance:
            failures.append({
                'company_id': company_id,
                'field': 'balancesheet.balance_sheet_equation',
                'issue': f'Balance sheet equation does not hold: assets={total_assets:.2f}, liabilities+equity={(total_liabilities + (equity_capital or 0) + (reserves or 0)):.2f}',
                'severity': 'WARNING'
            })
except Exception as e:
    print(f'Error DQ-04: {e}')

# DQ-05: Operating profit margin
try:
    query = 'SELECT company_id, id, operating_profit, sales, opm_percentage FROM profitandloss WHERE sales IS NOT NULL AND sales != 0'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, operating_profit, sales, opm_percentage = row
        if operating_profit is None or sales is None or opm_percentage is None:
            continue
        calculated_opm = (operating_profit / sales) * 100.0
        if abs(opm_percentage - calculated_opm) > 0.01:
            failures.append({
                'company_id': company_id,
                'field': 'profitandloss.opm_percentage',
                'issue': f'OPM mismatch: expected {calculated_opm:.2f}%, got {opm_percentage:.2f}%',
                'severity': 'WARNING'
            })
except Exception as e:
    print(f'Error DQ-05: {e}')

# DQ-06: Positive sales
try:
    query = 'SELECT company_id, id, sales FROM profitandloss WHERE sales < 0'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, sales = row
        failures.append({
            'company_id': company_id,
            'field': 'profitandloss.sales',
            'issue': f'Sales is negative: {sales}',
            'severity': 'WARNING'
        })
except Exception as e:
    pass

# DQ-07: Positive total assets
try:
    query = 'SELECT company_id, id, total_assets FROM balancesheet WHERE total_assets <= 0'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, total_assets = row
        failures.append({
            'company_id': company_id,
            'field': 'balancesheet.total_assets',
            'issue': f'Total assets is non-positive: {total_assets}',
            'severity': 'WARNING'
        })
except Exception as e:
    pass

# DQ-08: Net cash flow consistency
try:
    query = 'SELECT company_id, id, operating_activity, investing_activity, financing_activity, net_cash_flow FROM cashflow'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, operating_activity, investing_activity, financing_activity, net_cash_flow = row
        total = (0 if operating_activity is None else operating_activity) + \
                (0 if investing_activity is None else investing_activity) + \
                (0 if financing_activity is None else financing_activity)
        if net_cash_flow is None:
            continue
        if abs(net_cash_flow - total) > 0.01:
            failures.append({
                'company_id': company_id,
                'field': 'cashflow.net_cash_flow',
                'issue': f'Net cash flow mismatch: expected {total:.2f}, got {net_cash_flow:.2f}',
                'severity': 'WARNING'
            })
except Exception as e:
    pass

# DQ-09: Dividend payout validation
try:
    query = 'SELECT pl.company_id, pl.id, pl.dividend_payout, fr.dividend_payout_ratio_pct FROM profitandloss pl JOIN financial_ratios fr ON pl.company_id = fr.company_id AND pl.year = fr.year WHERE pl.dividend_payout IS NOT NULL AND fr.dividend_payout_ratio_pct IS NOT NULL'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, pl_id, div_payout, div_ratio = row
        if abs(div_payout - div_ratio) > 0.01:
            failures.append({
                'company_id': company_id,
                'field': 'profitandloss.dividend_payout',
                'issue': f'Dividend payout mismatch: profitandloss={div_payout}, financial_ratios={div_ratio}',
                'severity': 'WARNING'
            })
except Exception as e:
    pass

# DQ-10: URL validation
try:
    query = 'SELECT company_id, id, Annual_Report FROM documents WHERE Annual_Report IS NOT NULL AND Annual_Report != \'\''
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, url = row
        if not (url.startswith("http://") or url.startswith("https://")):
            failures.append({
                'company_id': company_id,
                'field': 'documents.Annual_Report',
                'issue': 'Invalid URL format: must start with http:// or https://',
                'severity': 'WARNING'
            })
except Exception as e:
    pass

# DQ-11: Year validation
import datetime
current_year = datetime.datetime.now().year
min_year = 1900
max_year = current_year + 1
tables_columns = [
    ("profitandloss", "year"),
    ("balancesheet", "year"),
    ("cashflow", "year"),
    ("financial_ratios", "year"),
    ("documents", "Year")
]
for table, column in tables_columns:
    try:
        query = f'SELECT company_id, id, {column} FROM {table} WHERE {column} IS NOT NULL AND ({column} < {min_year} OR {column} > {max_year})'
        rows = cursor.execute(query).fetchall()
        for row in rows:
            company_id, row_id, year_val = row
            failures.append({
                'company_id': company_id,
                'field': f'{table}.{column}',
                'issue': f'Year {year_val} is outside expected range [{min_year}, {max_year}]',
                'severity': 'INFO'
            })
    except Exception as e:
        pass

# DQ-12: Duplicate stock prices
try:
    query = 'SELECT company_id, date, COUNT(*) as cnt FROM stock_prices GROUP BY company_id, date HAVING cnt > 1'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, date_val, count = row
        failures.append({
            'company_id': company_id,
            'field': 'stock_prices.company_id,date',
            'issue': f'Duplicate stock price for company_id={company_id}, date={date_val} (occurs {count} times)',
            'severity': 'CRITICAL'
        })
except Exception as e:
    pass

# DQ-13: EPS sign consistency
try:
    query = 'SELECT company_id, id, eps, net_profit FROM profitandloss WHERE eps IS NOT NULL AND net_profit IS NOT NULL'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, eps, net_profit = row
        if (eps < 0 and net_profit > 0) or (eps > 0 and net_profit < 0):
            failures.append({
                'company_id': company_id,
                'field': 'profitandloss.eps',
                'issue': f'EPS sign ({eps}) does not match net profit sign ({net_profit})',
                'severity': 'WARNING'
            })
except Exception as e:
    pass

# DQ-14: Tax percentage validation
try:
    query = 'SELECT company_id, id, tax_percentage FROM profitandloss WHERE tax_percentage IS NOT NULL AND (tax_percentage < 0 OR tax_percentage > 100)'
    rows = cursor.execute(query).fetchall()
    for row in rows:
        company_id, row_id, tax_pct = row
        failures.append({
            'company_id': company_id,
            'field': 'profitandloss.tax_percentage',
            'issue': f'Tax percentage out of range [0,100]: {tax_pct}',
            'severity': 'WARNING'
        })
except Exception as e:
    pass

# DQ-15: Dataset coverage
try:
    company_count = cursor.execute('SELECT COUNT(*) FROM companies').fetchone()[0]
    fact_tables = ["profitandloss", "balancesheet", "cashflow", "financial_ratios"]
    for table in fact_tables:
        distinct_count = cursor.execute(f'SELECT COUNT(DISTINCT company_id) FROM {table}').fetchone()[0]
        if distinct_count != company_count:
            missing = cursor.execute(f'SELECT c.id FROM companies c WHERE c.id NOT IN (SELECT DISTINCT company_id FROM {table})').fetchall()
            for m in missing:
                failures.append({
                    'company_id': m[0],
                    'field': f'{table}.company_id',
                    'issue': f'Missing data for company in {table}',
                    'severity': 'INFO'
                })
except Exception as e:
    pass

# DQ-16: Critical nulls
critical_columns = {
    "companies": ["id", "company_name"],
    "profitandloss": ["company_id", "year", "sales", "net_profit"],
    "balancesheet": ["company_id", "year", "total_assets"],
    "cashflow": ["company_id", "year", "net_cash_flow"],
    "analysis": ["company_id"],
    "documents": ["company_id", "Year", "Annual_Report"],
    "prosandcons": ["company_id"],
    "sectors": ["company_id"],
    "financial_ratios": ["company_id", "year"],
    "stock_prices": ["company_id", "date", "close_price"]
}
for table, columns in critical_columns.items():
    if table not in tables:
        continue
    for col in columns:
        try:
            if table == "companies":
                query = f'SELECT id, {col} FROM {table} WHERE {col} IS NULL'
                rows = cursor.execute(query).fetchall()
                for row in rows:
                    company_id, value = row
                    failures.append({
                        'company_id': company_id,
                        'field': f'{table}.{col}',
                        'issue': f'Critical column {col} is NULL',
                        'severity': 'CRITICAL'
                    })
            else:
                query = f'SELECT company_id, id, {col} FROM {table} WHERE {col} IS NULL'
                rows = cursor.execute(query).fetchall()
                for row in rows:
                    company_id, row_id, value = row
                    failures.append({
                        'company_id': company_id,
                        'field': f'{table}.{col}',
                        'issue': f'Critical column {col} is NULL',
                        'severity': 'CRITICAL'
                    })
        except Exception as e:
            pass

print(f'Total failures found: {len(failures)}')

df = pd.DataFrame(failures)
if len(failures) > 0:
    df = df[['company_id', 'field', 'issue', 'severity']]
    df.to_csv(OUTPUT_CSV, index=False)
    print(f'Saved to {OUTPUT_CSV}')
    print(df.head(10))
else:
    df = pd.DataFrame(columns=['company_id', 'field', 'issue', 'severity'])
    df.to_csv(OUTPUT_CSV, index=False)
    print('No issues found')

conn.close()