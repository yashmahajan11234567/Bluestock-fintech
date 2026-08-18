import sys
sys.path.append('src')
import pandas as pd
import os

print('=== Verifying the bug ===')
base_path = os.path.join('src', 'screener', '..', '..', 'Data', 'raw')

# Load the data exactly as the function does
profitandloss = pd.read_excel(os.path.join(base_path, 'profitandloss.xlsx'), header=1)
if 'id' in profitandloss.columns:
    profitandloss = profitandloss.drop(columns=['id'])

print(f'Original profitandloss shape: {profitandloss.shape}')
print(f'Original company_id count: {profitandloss["company_id"].nunique()}')

# Check how many years we have for a sample company
sample_company = profitandloss[profitandloss['company_id'] == 'TCS']
print(f'TCS rows in original data: {len(sample_company)}')
if len(sample_company) > 0:
    print(f'TCS years in original data: {sorted(sample_company["year"].unique())}')

# NOW simulate what the ACTUAL function does:
# Step 1: Modify profitandloss for latest year tracking (lines 41-47)
if 'year' in profitandloss.columns:
    def _parse_year_to_int(y):
        if isinstance(y, str):
            import re
            m = re.search(r'\b(\d{4})\b', y)
            return int(m.group(1)) if m else 0
        elif isinstance(y, (int, float,)):
            return int(y)
        return 0
    profitandloss['_year_int'] = profitandloss['year'].apply(_parse_year_to_int)
    profitandloss = profitandloss.sort_values(['company_id', '_year_int'], ascending=[True, False])
    profitandloss = profitandloss.drop_duplicates(subset=['company_id'], keep='first')
    profitandloss = profitandloss.drop(columns=['_year_int'])

print(f'After modification for latest year tracking:')
print(f'Modified profitandloss shape: {profitandloss.shape}')
print(f'Modified company_id count: {profitandloss["company_id"].nunique()}')

# Check TCS now
sample_company_modified = profitandloss[profitandloss['company_id'] == 'TCS']
print(f'TCS rows after modification: {len(sample_company_modified)}')
if len(sample_company_modified) > 0:
    print(f'TCS year after modification: {sample_company_modified["year"].iloc[0] if "year" in sample_company_modified.columns else "YEAR COLUMN GONE"}')

# Step 2: Now make pl_full COPY (line 50 in actual function)
pl_full = profitandloss.copy()  # This is the BUG - copying already modified data!

print(f'\\npl_full shape (copied after modification): {pl_full.shape}')
print(f'pl_full company_id count: {pl_full["company_id"].nunique()}')

# Check TCS in pl_full
sample_company_plfull = pl_full[pl_full['company_id'] == 'TCS']
print(f'TCS rows in pl_full: {len(sample_company_plfull)}')
if len(sample_company_plfull) > 0:
    print(f'TCS year in pl_full: {sample_company_plfull["year"].iloc[0] if "year" in sample_company_plfull.columns else "YEAR COLUMN GONE"}')

# This explains why CAGR is NULL - we only have ONE year per company!
print(f'\\n=== THE BUG ===')
print(f'pl_full only has {pl_full["company_id"].nunique()} companies but each with only 1 year!')
print(f'CAGR needs at least 2 years of data per company to calculate.')
print(f'The fix is to copy pl_full BEFORE modifying profitandloss for latest year tracking.')

# Let's verify what the CORRECT approach would be:
print(f'\\n=== CORRECT APPROACH ===')
profitandloss_correct = pd.read_excel(os.path.join(base_path, 'profitandloss.xlsx'), header=1)
if 'id' in profitandloss_correct.columns:
    profitandloss_correct = profitandloss_correct.drop(columns=['id'])

# FIRST: Make pl_full copy for CAGR (BEFORE any modifications)
pl_full_correct = profitandloss_correct.copy()
print(f'Correct pl_full shape: {pl_full_correct.shape}')
print(f'Correct pl_full company_id count: {pl_full_correct["company_id"].nunique()}')

# Check TCS in correct pl_full
sample_company_correct = pl_full_correct[pl_full_correct['company_id'] == 'TCS']
print(f'TCS rows in correct pl_full: {len(sample_company_correct)}')
if len(sample_company_correct) > 0:
    print(f'TCS years in correct pl_full: {sorted(sample_company_correct["year"].unique())}')

# NOW: Modify profitandloss for latest year tracking
if 'year' in profitandloss_correct.columns:
    def _parse_year_to_int(y):
        if isinstance(y, str):
            import re
            m = re.search(r'\b(\d{4})\b', y)
            return int(m.group(1)) if m else 0
        elif isinstance(y, (int, float,)):
            return int(y)
        return 0
    profitandloss_correct['_year_int'] = profitandloss_correct['year'].apply(_parse_year_to_int)
    profitandloss_correct = profitandloss_correct.sort_values(['company_id', '_year_int'], ascending=[True, False])
    profitandloss_correct = profitandloss_correct.drop_duplicates(subset=['company_id'], keep='first')
    profitandloss_correct = profitandloss_correct.drop(columns=['_year_int'])

print(f'After modification for latest year tracking (correct way):')
print(f'Modified profitandloss shape: {profitandloss_correct.shape}')
print(f'Modified company_id count: {profitandloss_correct["company_id"].nunique()}')

sample_company_modified_correct = profitandloss_correct[profitandloss_correct['company_id'] == 'TCS']
print(f'TCS rows after modification (correct): {len(sample_company_modified_correct)}')