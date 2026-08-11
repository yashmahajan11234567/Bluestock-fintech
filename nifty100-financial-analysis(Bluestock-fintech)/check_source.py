import pandas as pd
df = pd.read_excel('Data/raw/analysis.xlsx', sheet_name='Analysis', header=1)
print('Shape:', df.shape)
print('Columns:', df.columns.tolist())
print()
for _, row in df.iterrows():
    print(f'=== {row["company_id"]} ===')
    for col in ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe']:
        val = row[col]
        if pd.notna(val):
            print(f'  {col}: {repr(str(val))}')
        else:
            print(f'  {col}: NaN')