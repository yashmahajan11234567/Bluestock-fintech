import sys
sys.path.append('src')
import pandas as pd
import os

print('=== Diagnosing CAGR NULL issue ===')
base_path = os.path.join('src', 'screener', '..', '..', 'Data', 'raw')

# Let's manually walk through the exact steps in load_screener_data but with extensive debugging
print('Step-by-step replication of load_screener_data:')

# 1. Load companies
companies = pd.read_excel(os.path.join(base_path, 'companies.xlsx'))
companies = companies.rename(columns={'id': 'company_id'})
print(f'1. Companies: {companies.shape}')
print(f'   Company IDs sample: {companies["company_id"].head().tolist()}')

# 2. Load sectors
sectors = pd.read_excel(os.path.join(base_path, 'sectors.xlsx'))
print(f'2. Sectors: {sectors.shape}')

# 3. Merge companies + sectors
df = pd.merge(companies, sectors, on='company_id', how='left')
print(f'3. After companies+sectors: {df.shape}')

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
print(f'4. Financial ratios: {fin_ratio.shape}')

# 5. Merge with financial ratios
df = pd.merge(df, fin_ratio, on='company_id', how='left')
print(f'5. After +fin_ratio: {df.shape}')

# 6. Load market cap
market_cap = pd.read_excel(os.path.join(base_path, 'market_cap.xlsx'))
market_cap = market_cap.sort_values(['company_id', 'year'], ascending=[True, False])
market_cap = market_cap.drop_duplicates(subset=['company_id'], keep='first')
print(f'6. Market cap: {market_cap.shape}')

# 7. Merge with market cap
df = pd.merge(df, market_cap, on='company_id', how='left')
print(f'7. After +market_cap: {df.shape}')

# 8. Load and prepare profitandloss
profitandloss = pd.read_excel(os.path.join(base_path, 'profitandloss.xlsx'), header=1)
if 'id' in profitandloss.columns:
    profitandloss = profitandloss.drop(columns=['id'])
print(f'8. Profitandloss raw: {profitandloss.shape}')

# Calculate CAGR from FULL profitandloss (all years)
pl_full = profitandloss.copy()
pl_full['_year_int'] = pl_full['year'].apply(_parse_year_to_int)
pl_full = pl_full.sort_values(['company_id', '_year_int'])
print(f'8a. Profitandloss with _year_int: {pl_full.shape}')

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

# 9. Calculate CAGR
print('9. Calculating CAGR...')
cagr_df = pl_full.groupby('company_id').apply(_calculate_cagr, include_groups=False).reset_index()
print(f'   CAGR dataframe shape: {cagr_df.shape}')
print(f'   CAGR dataframe columns: {list(cagr_df.columns)}')
print(f'   Sample CAGR values:')
print(cagr_df.head(10))
print(f'   Number of non-null sales CAGR: {cagr_df["compounded_sales_growth"].notna().sum()}')
print(f'   Number of non-null profit CAGR: {cagr_df["compounded_profit_growth"].notna().sum()}')

# 10. Prepare latest year's profitandloss
pl_latest = profitandloss.copy()
pl_latest['_year_int'] = pl_latest['year'].apply(_parse_year_to_int)
pl_latest = pl_latest.sort_values(['company_id', '_year_int'], ascending=[True, False])
pl_latest = pl_latest.drop_duplicates(subset=['company_id'], keep='first')
pl_latest = pl_latest.sort_values(['company_id', '_year_int'], ascending=[True, False])
pl_latest = pl_latest.drop_duplicates(subset=['company_id'], keep='last')
pl_latest = pl_latest.drop(columns=['_year_int'])
print(f'10. Latest profitandloss: {pl_latest.shape}')

# 11. Merge with pl_latest
df = pd.merge(df, pl_latest, on='company_id', how='left')
print(f'11. After +pl_latest: {df.shape}')

# 12. Merge with cagr_df
print(f'12. Before +cagr_df: {df.shape}')
print(f'   About to merge with cagr_df of shape: {cagr_df.shape}')
print(f'   cagr_df company_ids sample: {cagr_df["company_id"].head().tolist()}')
print(f'   df company_ids sample before merge: {df["company_id"].head().tolist()}')

# Check for potential merge issues
print(f'   Unique company_ids in df before merge: {df["company_id"].nunique()}')
print(f'   Unique company_ids in cagr_df: {cagr_df["company_id"].nunique()}')

# Check if company_id types match
print(f'   df company_id dtype: {df["company_id"].dtype}')
print(f'   cagr_df company_id dtype: {cagr_df["company_id"].dtype}')

df = pd.merge(df, cagr_df, on='company_id', how='left')
print(f'12. After +cagr_df: {df.shape}')

# 13. Check final CAGR columns
if 'compounded_sales_growth' in df.columns:
    non_null = df['compounded_sales_growth'].notna().sum()
    null_count = df['compounded_sales_growth'].isna().sum()
    print(f'13. compounded_sales_growth: {non_null} non-null, {null_count} null')
    if non_null > 0:
        print(f'   Sample values: {df["compounded_sales_growth"].dropna().head().tolist()}')
    else:
        print(f'   ALL NULL!')
else:
    print(f'13. compounded_sales_growth COLUMN MISSING!')

if 'compounded_profit_growth' in df.columns:
    non_null = df['compounded_profit_growth'].notna().sum()
    null_count = df['compounded_profit_growth'].isna().sum()
    print(f'13. compounded_profit_growth: {non_null} non-null, {null_count} null')
    if non_null > 0:
        print(f'   Sample values: {df["compounded_profit_growth"].dropna().head().tolist()}')
    else:
        print(f'   ALL NULL!')
else:
    print(f'13. compounded_profit_growth COLUMN MISSING!')

# Let's also check what's in the dataframe for a specific company we know should have data
print(f'\\nChecking for TCS in final dataframe:')
tcs_rows = df[df['company_id'] == 'TCS']
if len(tcs_rows) > 0:
    tcs_row = tcs_rows.iloc[0]
    print(f'   TCS found!')
    print(f'   ROE: {tcs_row.get("return_on_equity_pct", "MISSING")}')
    print(f'   Sales CAGR: {tcs_row.get("compounded_sales_growth", "MISSING")}')
    print(f'   Profit CAGR: {tcs_row.get("compounded_profit_growth", "MISSING")}')
else:
    print(f'   TCS NOT FOUND!')

# Let's check what CAGR values we calculated manually for TCS
print(f'\\nChecking manual CAGR calculation for TCS:')
tcs_pl = pl_full[pl_full['company_id'] == 'TCS'].copy()
if len(tcs_pl) > 0:
    print(f'   TCS profitandloss rows: {len(tcs_pl)}')
    print(f'   TCS years: {sorted(tcs_pl["_year_int"].unique())}')
    tcs_sales = tcs_pl['sales'].apply(_to_float).tolist()
    tcs_profits = tcs_pl['net_profit'].apply(_to_float).tolist()
    print(f'   TCS sales values: {tcs_sales}')
    print(f'   TCS profit values: {tcs_profits}')

    # Manual calculation
    sales_pairs = [(y, s) for y, s in zip(tcs_pl['_year_int'].tolist(), tcs_sales) if s is not None and s > 0]
    net_profit_pairs = [(y, s) for y, s in zip(tcs_pl['_year_int'].tolist(), tcs_profits) if s is not None and s > 0]
    print(f'   TCS sales pairs: {sales_pairs}')
    print(f'   TCS profit pairs: {net_profit_pairs}')

    if len(sales_pairs) >= 2:
        start_year, start_val = sales_pairs[0]
        end_year, end_val = sales_pairs[-1]
        n_years = end_year - start_year
        if n_years > 0:
            manual_sales_cagr = _calculate_cagr_value(start_val, end_val, n_years)
            print(f'   Manual TCS sales CAGR: {manual_sales_cagr}')
        else:
            print(f'   Not enough years for sales CAGR')
    else:
        print(f'   Not enough sales data points for CAGR')

    if len(net_profit_pairs) >= 2:
        start_year, start_val = net_profit_pairs[0]
        end_year, end_val = net_profit_pairs[-1]
        n_years = end_year - start_year
        if n_years > 0:
            manual_profit_cagr = _calculate_cagr_value(start_val, end_val, n_years)
            print(f'   Manual TCS profit CAGR: {manual_profit_cagr}')
        else:
            print(f'   Not enough years for profit CAGR')
    else:
        print(f'   Not enough profit data points for CAGR')
else:
    print(f'   TCS not found in profitandloss!')

# Let's check the actual function's output for comparison
print(f'\\n=== Comparing with actual function ===')
from screener.engine import load_screener_data
actual_df = load_screener_data()
print(f'Actual function dataframe shape: {actual_df.shape}')
if 'compounded_sales_growth' in actual_df.columns:
    actual_non_null = actual_df['compounded_sales_growth'].notna().sum()
    actual_null = actual_df['compounded_sales_growth'].isna().sum()
    print(f'Actual compounded_sales_growth: {actual_non_null} non-null, {actual_null} null')
else:
    print('Actual compounded_sales_growth COLUMN MISSING!')

if 'compounded_profit_growth' in actual_df.columns:
    actual_non_null = actual_df['compounded_profit_growth'].notna().sum()
    actual_null = actual_df['compounded_profit_growth'].isna().sum()
    print(f'Actual compounded_profit_growth: {actual_non_null} non-null, {actual_null} null')
else:
    print('Actual compounded_profit_growth COLUMN MISSING!')

# Check TCS in actual function output
print(f'\\nTCS in actual function output:')
tcs_actual = actual_df[actual_df['company_id'] == 'TCS']
if len(tcs_actual) > 0:
    tcs_actual_row = tcs_actual.iloc[0]
    print(f'   TCS found in actual output!')
    print(f'   Sales CAGR: {tcs_actual_row.get("compounded_sales_growth", "MISSING")}')
    print(f'   Profit CAGR: {tcs_actual_row.get("compounded_profit_growth", "MISSING")}')
else:
    print(f'   TCS NOT FOUND in actual output!')