import pandas as pd
import os

raw_dir = 'data/raw'

def header_row(df_raw):
    first = str(df_raw.iloc[0,0]) if not pd.isna(df_raw.iloc[0,0]) else ''
    if 'Bluestock Fintech' in first or 'Mkt Fintech' in first:
        return 1
    else:
        return 0

# companies
co_path = os.path.join(raw_dir, 'companies.xlsx')
xl = pd.ExcelFile(co_path)
df_co_raw = xl.parse('Companies', header=None)
h_co = header_row(df_co_raw)
df_co = xl.parse('Companies', header=h_co)
df_co.columns = [str(c).strip() for c in df_co.columns]
print('=== companies.id (first 10) ===')
print(df_co['id'].head(10).tolist())
print('Total unique:', df_co['id'].nunique())
print()

files = [
    ('analysis.xlsx', 'Analysis'),
    ('balancesheet.xlsx', 'Balance Sheet'),
    ('cashflow.xlsx', 'Cash Flow'),
    ('profitandloss.xlsx', 'Profit & Loss'),
    ('documents.xlsx', 'Documents'),
    ('prosandcons.xlsx', 'Pros & Cons'),
    ('sectors.xlsx', 'Sheet1'),
    ('stock_prices.xlsx', 'Sheet1'),
    ('financial_ratios.xlsx', 'Sheet1'),
]

for fname, sheet in files:
    path = os.path.join(raw_dir, fname)
    xl = pd.ExcelFile(path)
    df_raw = xl.parse(sheet, header=None)
    h = header_row(df_raw)
    df = xl.parse(sheet, header=h)
    df.columns = [str(c).strip() for c in df.columns]
    if 'company_id' in df.columns:
        print(f'=== {fname}::{sheet} company_id (first 10) ===')
        vals = df['company_id'].head(10).tolist()
        print(vals)
        # also show type sample
        print('Sample type:', type(df['company_id'].iloc[0]) if len(df) > 0 else 'empty')
        # check if numeric
        try:
            numeric = pd.to_numeric(df['company_id'], errors='coerce')
            num_notnull = numeric.notnull().sum()
            print(f'Numeric convertible: {num_notnull}/{len(df)}')
        except:
            pass
        print()
    else:
        print(f'=== {fname}::{sheet} NO company_id column ===')
        print()

# Also look at companies table maybe there is also a numeric id column? Not present.
print('=== companies table columns ===')
print(df_co.columns.tolist())
print()
