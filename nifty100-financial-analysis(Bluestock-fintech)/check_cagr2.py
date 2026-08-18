from src.screener.engine import load_screener_data
import warnings
warnings.filterwarnings('ignore')

df = load_screener_data()
print('TCS data:')
tcs = df[df['company_id'] == 'TCS']
print(f'compounded_sales_growth: {tcs["compounded_sales_growth"].values}')
print(f'compounded_profit_growth: {tcs["compounded_profit_growth"].values}')

print('\nINFY data:')
infy = df[df['company_id'] == 'INFY']
print(f'compounded_sales_growth: {infy["compounded_sales_growth"].values}')
print(f'compounded_profit_growth: {infy["compounded_profit_growth"].values}')

print('\nSample of companies with CAGR:')
cagr_cols = ['company_id', 'compounded_sales_growth', 'compounded_profit_growth']
sample = df[cagr_cols].dropna(subset=['compounded_sales_growth']).head(10)
print(sample.to_string())