import pandas as pd
import sqlite3

# Load from database
conn = sqlite3.connect('db/nifty100.db')
pl = pd.read_sql("SELECT company_id, year, sales, net_profit FROM profitandloss WHERE company_id = 'TCS' ORDER BY year", conn)
conn.close()

print('TCS P&L data from DB:')
print(pl.to_string())

# Convert year to int
def parse_year(y):
    if isinstance(y, str):
        import re
        m = re.search(r'(\d{4})', y)
        return int(m.group(1)) if m else 0
    return int(y) if y else 0

pl['_year_int'] = pl['year'].apply(parse_year)
pl = pl[pl['_year_int'] > 0].sort_values('_year_int')
print('\nWith _year_int:')
print(pl[['_year_int', 'sales', 'net_profit']].to_string())

# Calculate CAGR manually
sales = pd.to_numeric(pl['sales'], errors='coerce').dropna()
profits = pd.to_numeric(pl['net_profit'], errors='coerce').dropna()
years = pl['_year_int'].values

print(f'\nSales: {sales.tolist()}')
print(f'Profits: {profits.tolist()}')
print(f'Years: {years.tolist()}')

if len(sales) >= 2:
    start_sales = sales.iloc[0]
    end_sales = sales.iloc[-1]
    n_years = years[-1] - years[0]
    sales_cagr = ((end_sales / start_sales) ** (1/n_years) - 1) * 100
    print(f'Sales CAGR: {sales_cagr:.4f}%')

if len(profits) >= 2:
    start_profit = profits.iloc[0]
    end_profit = profits.iloc[-1]
    n_years = years[-1] - years[0]
    profit_cagr = ((end_profit / start_profit) ** (1/n_years) - 1) * 100
    print(f'Profit CAGR: {profit_cagr:.4f}%')