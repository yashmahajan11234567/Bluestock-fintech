import sys
sys.path.append('src')
from screener.engine import load_screener_data
import pandas as pd
import os

print('=== Testing actual load_screener_data function ===')

# Call the actual function
df = load_screener_data()
print(f'Final dataframe shape: {df.shape}')

# Check CAGR columns
cagr_cols = ['compounded_sales_growth', 'compounded_profit_growth']
for col in cagr_cols:
    if col in df.columns:
        non_null = df[col].notna().sum()
        null_count = df[col].isna().sum()
        print(f'{col}: {non_null} non-null, {null_count} null')
        if non_null > 0:
            print(f'  Sample values: {df[col].dropna().head(3).tolist()}')
        else:
            print(f'  ALL NULL!')
    else:
        print(f'{col}: COLUMN NOT FOUND!')

# Let's also check what happens inside the function by replicating it with debug prints
print('\\n=== Debugging inside load_screener_data ===')
base_path = os.path.join(os.path.dirname('src/screener/engine.py'), '..', '..', 'Data', 'raw')

# 1. Load companies
companies = pd.read_excel(os.path.join(base_path, 'companies.xlsx'))
companies = companies.rename(columns={'id': 'company_id'})
print(f'1. Companies loaded: {companies.shape}')

# 2. Load sectors
sectors = pd.read_excel(os.path.join(base_path, 'sectors.xlsx'))
print(f'2. Sectors loaded: {sectors.shape}')

# 3. Merge companies + sectors
df = pd.merge(companies, sectors, on='company_id', how='left')
print(f'3. After companies+sectors merge: {df.shape}')

# 4. Load financial ratios
fin_ratio = pd.read_excel(os.path.join(base_path, 'financial_ratios.xlsx'))
def _parse_year_to_int(y):
    if isinstance(y, str):
        import re
        m = re.search(r'\b(\d{4})\b', y)
        return int(m.group(1)) if m else 0
    elif isinstance(y, (int, float,)):
        return int(y)
    return 0
fin_ratio['_year_int'] = fin_ratio['year'].apply(_parse_year_to_int)
fin_ratio = fin_ratio.sort_values(['company_id', '_year_int'], ascending=[True, False])
fin_ratio = fin_ratio.drop_duplicates(subset=['company_id'], keep='first')
fin_ratio = fin_ratio.drop(columns=['_year_int'])
print(f'4. Financial ratios processed: {fin_ratio.shape}')

# 5. Merge with financial ratios
df = pd.merge(df, fin_ratio, on='company_id', how='left')
print(f'5. After +fin_ratio merge: {df.shape}')

# 6. Load market cap
market_cap = pd.read_excel(os.path.join(base_path, 'market_cap.xlsx'))
market_cap = market_cap.sort_values(['company_id', 'year'], ascending=[True, False])
market_cap = market_cap.drop_duplicates(subset=['company_id'], keep='first')
print(f'6. Market cap loaded: {market_cap.shape}')

# 7. Merge with market cap
df = pd.merge(df, market_cap, on='company_id', how='left')
print(f'7. After +market_cap merge: {df.shape}')

# 8. Load and prepare profitandloss
profitandloss = pd.read_excel(os.path.join(base_path, 'profitandloss.xlsx'), header=1)
if 'id' in profitandloss.columns:
    profitandloss = profitandloss.drop(columns=['id'])
print(f'8. Profitandloss loaded: {profitandloss.shape}')

# Calculate CAGR from FULL profitandloss (all years)
pl_full = profitandloss.copy()
pl_full['_year_int'] = pl_full['year'].apply(_parse_year_to_int)
pl_full = pl_full.sort_values(['company_id', '_year_int'])
print(f'8a. Profitandloss with _year_int: {pl_full.shape}')

# Helper functions
def _to_float(value):
    try:
        v = pd.to_numeric(value, errors='coerce')
        return v if not pd.isna(v) else None
    except Exception:
        return None

def _calculate_cagr_value(start_val, end_val, n_years):
    if start_val is None or end_val is None or n_years <= 0:
        return None
    if start_val == 0:
        return None
    return ((end_val / start_val) ** (1 / n_years) - 1) * 100.0

def _calculate_cagr(group):
    # group is a DataFrame for one company with columns: year, sales, net_profit, _year_int
    # Exclude rows with invalid year (year_int <= 0) for CAGR calculation (e.g., TTM)
    group = group[group['_year_int'] > 0].copy()
    if len(group) < 2:
        return pd.Series({'compounded_sales_growth': None, 'compounded_profit_growth': None})
    # Sort by year_int for consistent ordering
    group = group.sort_values('_year_int')
    years = group['_year_int'].tolist()
    sales = group['sales'].apply(_to_float).tolist()
    net_profits = group['net_profit'].apply(_to_float).tolist()
    # Build lists of (year, value) for sales and net_profit where value is not None and > 0
    sales_pairs = [(y, s) for y, s in zip(years, sales) if s is not None and s > 0]
    net_profit_pairs = [(y, s) for y, s in zip(years, net_profits) if s is not None and s > 0]
    sales_cagr = None
    if len(sales_pairs) >= 2:
        start_year, start_val = sales_pairs[0]
        end_year, end_val = sales_pairs[-1]
        n_years = end_year - start_year
        if n_years > 0:
            sales_cagr = _calculate_cagr_value(start_val, end_val, n_years)
    net_profit_cagr = None
    if len(net_profit_pairs) >= 2:
        start_year, start_val = net_profit_pairs[0]
        end_year, end_val = net_profit_pairs[-1]
        n_years = end_year - start_year
        if n_years > 0:
            net_profit_cagr = _calculate_cagr_value(start_val, end_val, n_years)
    return pd.Series({
        'compounded_sales_growth': sales_cagr,
        'compounded_profit_growth': net_profit_cagr
    })

# We need to apply this to each company_id group
print(f'9. About to calculate CAGR for {pl_full["company_id"].nunique()} companies...')
cagr_df = pl_full.groupby('company_id').apply(_calculate_cagr, include_groups=False).reset_index()
print(f'   CAGR dataframe shape: {cagr_df.shape}')
print(f'   CAGR dataframe sample:')
print(cagr_df.head())

# Now, we want the latest year's profitandloss data for merging (for sales, net_profit, etc.)
# profitandloss already has the latest year's data (because we sorted and dropped duplicates keeping first? Wait, we did keep='first' after sorting by year ascending? Actually, we sorted by year ascending and then dropped duplicates keeping first -> that gives the earliest year. We want the latest year.
# Let's recompute the latest year's profitandloss data:
pl_latest = profitandloss.copy()
print(f'   Before processing pl_latest: {pl_latest.shape}')
if 'year' in pl_latest.columns:
    pl_latest['_year_int'] = pl_latest['year'].apply(_parse_year_to_int)
    print(f'   After adding _year_int: {pl_latest.shape}')
    pl_latest = pl_latest.sort_values(['company_id', '_year_int'], ascending=[True, False])
    print(f'   After first sort ascending: {pl_latest.shape}')
    pl_latest = pl_latest.drop_duplicates(subset=['company_id'], keep='first')  # keep the latest because we sorted ascending? Wait, we sorted ascending, so the latest year is at the end. We want to keep the last duplicate. So we should do keep='last'.
    print(f'   After drop_duplicates keep="first": {pl_latest.shape}')
    # Let's fix: sort ascending, then keep='last' gets the latest year.
    pl_latest = pl_latest.sort_values(['company_id', '_year_int'], ascending=[True, False])
    print(f'   After second sort ascending: {pl_latest.shape}')
    pl_latest = pl_latest.drop_duplicates(subset=['company_id'], keep='last')
    print(f'   After drop_duplicates keep="last": {pl_latest.shape}')
    pl_latest = pl_latest.drop(columns=['_year_int'])
    print(f'   After dropping _year_int: {pl_latest.shape}')
else:
    pl_latest = pl_latest.drop_duplicates(subset=['company_id'], keep='last')
print(f'9a. Final pl_latest shape: {pl_latest.shape}')

# Show what we got for a few companies
print('   Sample of pl_latest data:')
print(pl_latest[['company_id', 'year', 'sales', 'net_profit']].head())

# 10. Merge latest profitandloss (for columns like sales, net_profit, etc.)
df = pd.merge(df, pl_latest, on='company_id', how='left')
print(f'10. After +pl_latest merge: {df.shape}')

# 11. Merge CAGR data (overwrite the CAGR columns if they exist from profitandloss? They don't, but we will have the columns from cagr_df)
print(f'11. Before +cagr_df merge: {df.shape}')
print(f'    About to merge with cagr_df of shape: {cagr_df.shape}')
df = pd.merge(df, cagr_df, on='company_id', how='left')
print(f'11. After +cagr_df merge: {df.shape}')

# Check final CAGR columns
if 'compounded_sales_growth' in df.columns:
    non_null = df['compounded_sales_growth'].notna().sum()
    null_count = df['compounded_sales_growth'].isna().sum()
    print(f'12. compounded_sales_growth: {non_null} non-null, {null_count} null')
    if non_null > 0:
        print(f'   Sample values: {df["compounded_sales_growth"].dropna().head().tolist()}')
    else:
        print(f'   ALL NULL!')
else:
    print(f'12. compounded_sales_growth COLUMN MISSING!')

if 'compounded_profit_growth' in df.columns:
    non_null = df['compounded_profit_growth'].notna().sum()
    null_count = df['compounded_profit_growth'].isna().sum()
    print(f'12. compounded_profit_growth: {non_null} non-null, {null_count} null')
    if non_null > 0:
        print(f'   Sample values: {df["compounded_profit_growth"].dropna().head().tolist()}')
    else:
        print(f'   ALL NULL!')
else:
    print(f'12. compounded_profit_growth COLUMN MISSING!')

# Let's also check what happened to the original profitandloss columns
print(f'\\nChecking if we still have sales/net_profit data:')
if 'sales' in df.columns:
    abb_sales = df[df['company_id'] == 'ABB']['sales'].iloc[0] if len(df[df['company_id'] == 'ABB']) > 0 else 'NOT FOUND'
    print(f'ABB sales: {abb_sales} (should be 5849 from latest year)')
if 'net_profit' in df.columns:
    abb_net_profit = df[df['company_id'] == 'ABB']['net_profit'].iloc[0] if len(df[df['company_id'] == 'ABB']) > 0 else 'NOT FOUND'
    print(f'ABB net_profit: {abb_net_profit} (should be 1201 from latest year)')