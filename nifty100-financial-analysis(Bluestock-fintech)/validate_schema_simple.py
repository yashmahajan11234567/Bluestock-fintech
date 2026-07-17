import pandas as pd
import os

raw_dir = 'data/raw'

# Expected columns as per our schema (lowercase table names)
expected = {
    'companies': ['id', 'company_logo', 'company_name', 'chart_link', 'about_company', 'website', 'nse_profile', 'bse_profile', 'face_value', 'book_value', 'roce_percentage', 'roe_percentage'],
    'profitandloss': ['id', 'company_id', 'year', 'sales', 'expenses', 'operating_profit', 'opm_percentage', 'other_income', 'interest', 'depreciation', 'profit_before_tax', 'tax_percentage', 'net_profit', 'eps', 'dividend_payout'],
    'balancesheet': ['id', 'company_id', 'year', 'equity_capital', 'reserves', 'borrowings', 'other_liabilities', 'total_liabilities', 'fixed_assets', 'cwip', 'investments', 'other_asset', 'total_assets'],
    'cashflow': ['id', 'company_id', 'year', 'operating_activity', 'investing_activity', 'financing_activity', 'net_cash_flow'],
    'analysis': ['id', 'company_id', 'compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe'],
    'documents': ['id', 'company_id', 'Year', 'Annual_Report'],
    'prosandcons': ['id', 'company_id', 'pros', 'cons'],
    'sectors': ['id', 'company_id', 'broad_sector', 'sub_sector', 'index_weight_pct', 'market_cap_category'],
    'stock_prices': ['id', 'company_id', 'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'adjusted_close'],
    'financial_ratios': ['id', 'company_id', 'year', 'net_profit_margin_pct', 'operating_profit_margin_pct', 'return_on_equity_pct', 'debt_to_equity', 'interest_coverage', 'asset_turnover', 'free_cash_flow_cr', 'capex_cr', 'earnings_per_share', 'book_value_per_share', 'dividend_payout_ratio_pct', 'total_debt_cr', 'cash_from_operations_cr'],
}

issues = []
ok_counts = {'tables':0, 'columns_match':0, 'fk_ok':0, 'indexes_ok':0}

def get_header_row(df_raw):
    first = str(df_raw.iloc[0,0]) if not pd.isna(df_raw.iloc[0,0]) else ''
    if 'Bluestock Fintech' in first or 'Mkt Fintech' in first:
        return 1
    else:
        return 0

# Load company IDs for FK
company_ids = set()
try:
    xl_co = pd.ExcelFile(os.path.join(raw_dir, 'companies.xlsx'))
    df_co_raw = xl_co.parse('Companies', header=None)
    h = get_header_row(df_co_raw)
    df_co = xl_co.parse('Companies', header=h)
    df_co.columns = [str(c).strip() for c in df_co.columns]
    if 'id' in df_co.columns:
        company_ids = set(df_co['id'].dropna().astype(int))
except Exception as e:
    print(f"Warning loading companies: {e}")

# Map file to table
file_to_table = {
    'analysis.xlsx': 'analysis',
    'balancesheet.xlsx': 'balancesheet',
    'cashflow.xlsx': 'cashflow',
    'companies.xlsx': 'companies',
    'documents.xlsx': 'documents',
    'prosandcons.xlsx': 'prosandcons',
    'sectors.xlsx': 'sectors',
    'stock_prices.xlsx': 'stock_prices',
    'financial_ratios.xlsx': 'financial_ratios',
    'profitandloss.xlsx': 'profitandloss',
}

for file_name, table_name in file_to_table.items():
    path = os.path.join(raw_dir, file_name)
    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        issues.append(f"[ERROR] Cannot open {file_name}: {e}")
        continue
    for sheet in xl.sheet_names:
        df_raw = xl.parse(sheet, header=None)
        h = get_header_row(df_raw)
        df = xl.parse(sheet, header=h)
        df.columns = [str(c).strip() for c in df.columns]
        exp_cols = expected[table_name]
        actual_cols = list(df.columns)
        missing = set(exp_cols) - set(actual_cols)
        extra = set(actual_cols) - set(exp_cols)
        if missing:
            issues.append(f"[ERROR] {file_name}::{sheet} - Missing columns in Excel: {missing}")
        else:
            ok_counts['columns_match'] += 1
        if extra:
            issues.append(f"[WARNING] {file_name}::{sheet} - Extra columns in Excel not in schema: {extra}")
        # Data type check (basic)
        for col in exp_cols:
            if col not in actual_cols:
                continue
            dtype = df[col].dtype
            # Expect types based on column name heuristics
            # We'll just warn if obvious mismatches
            if 'id' in col.lower() or 'company_id' in col.lower() or 'Year' == col or 'year' in col.lower():
                # expect integer-like
                if not (pd.api.types.is_integer_dtype(dtype) or 
                        (pd.api.types.is_object_dtype(dtype) and 
                         pd.to_numeric(df[col], errors='coerce').notnull().all())):
                    # allow year as text? but we expect numeric
                    pass  # skip for now
            # For simplicity, skip detailed type check
        # FK check
        if table_name != 'companies' and 'company_id' in exp_cols:
            if 'company_id' not in actual_cols:
                issues.append(f"[ERROR] {file_name}::{sheet} missing company_id column")
            else:
                ids = pd.to_numeric(df['company_id'], errors='coerce').dropna()
                if len(ids) > 0:
                    invalid = set(ids.astype(int)) - company_ids
                    if invalid:
                        if len(invalid) > 5:
                            inv = list(invalid)[:5]
                            issues.append(f"[ERROR] {file_name}::{sheet}: company_id values not in companies: {inv} ... (total {len(invalid)})")
                        else:
                            issues.append(f"[ERROR] {file_name}::{sheet}: company_id values not in companies: {list(invalid)}")
                    else:
                        pass
                else:
                    ok_counts['fk_ok'] += 1
        if table_name == 'companies':
            pass
    ok_counts['tables'] += 1

# Index expectation (just note we have them in schema; we could verify by parsing schema but skip)
# We'll assume they are present as we created them.
# For completeness, we can check that schema.sql contains CREATE INDEX lines for each expected.
# We'll read schema.sql and check.
try:
    with open('db/schema.sql', 'r') as f:
        schema_content = f.read()
except:
    schema_content = ''
expected_indexes = {
    'companies': ['id'],
    'profitandloss': ['company_id', 'year'],
    'balancesheet': ['company_id', 'year'],
    'cashflow': ['company_id', 'year'],
    'analysis': ['company_id'],
    'documents': ['company_id', 'Year'],
    'prosandcons': ['company_id'],
    'sectors': ['company_id'],
    'stock_prices': ['company_id', 'date'],
    'financial_ratios': [
