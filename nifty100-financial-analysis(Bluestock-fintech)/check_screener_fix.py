from src.screener.engine import run_screener, get_quality_compounder_filters
import warnings
warnings.filterwarnings('ignore')

# Test with very restrictive filters to trigger the bug
filters = {
    'ROE': {'min': 30},
    'Debt to Equity': {'max': 0.5},
    'Free Cash Flow': {'min': 1000},
    'Revenue CAGR': {'min': 15}
}

print("Testing restrictive filters...")
try:
    result = run_screener(filters=filters)
    print(f'Result shape: {result.shape}')
    print(f'Columns: {result.columns.tolist()}')
    if len(result) > 0:
        print(result[['company_id', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr', 'compounded_sales_growth', 'composite_quality_score', 'sector_relative_score']].to_string())
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n\nTesting with original Quality Compounder filters...")
filters2 = get_quality_compounder_filters()
result2 = run_screener(filters=filters2)
print(f'Result shape: {result2.shape}')
if len(result2) > 0:
    print(result2[['company_id', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity', 'compounded_sales_growth', 'composite_quality_score', 'sector_relative_score']].to_string())

# Test with just 2 companies in different sectors
print("\n\nTest with 2 companies across 2 sectors...")
import pandas as pd
import numpy as np
from src.screener.engine import _winsorize_and_scale

def _compute_sector_score(group):
    roe_score = _winsorize_and_scale(group['return_on_equity_pct'], True)
    npm_score = _winsorize_and_scale(group['net_profit_margin_pct'], True)
    profitability = 0.6 * roe_score + 0.4 * npm_score

    fcf_score = _winsorize_and_scale(group['free_cash_flow_cr'], True)
    cfo_pat = group['cash_from_operations_cr'] / group['net_profit'].replace(0, np.nan)
    cfo_pat = cfo_pat.replace([np.inf, -np.inf], np.nan)
    cfo_pat_score = _winsorize_and_scale(cfo_pat, True)
    fcf_positive = (group['free_cash_flow_cr'] > 0).astype(float) * 100.0
    cash_quality = 0.5 * fcf_score + (1/3) * cfo_pat_score + (1/6) * fcf_positive

    revenue_cagr_score = _winsorize_and_scale(group['compounded_sales_growth'], True)
    pat_cagr_score = _winsorize_and_scale(group['compounded_profit_growth'], True)
    growth = 0.5 * revenue_cagr_score + 0.5 * pat_cagr_score

    de_score = _winsorize_and_scale(group['debt_to_equity'], False)
    ic_score = _winsorize_and_scale(group['interest_coverage'], True)
    leverage = (2/3) * de_score + (1/3) * ic_score

    composite = (0.35 * profitability + 0.30 * cash_quality +
               0.20 * growth + 0.15 * leverage)
    return composite

test_df2 = pd.DataFrame({
    'company_id': ['TCS', 'INFY'],
    'broad_sector': ['Information Technology', 'Information Technology'],
    'return_on_equity_pct': [50.0, 30.0],
    'net_profit_margin_pct': [20.0, 18.0],
    'free_cash_flow_cr': [1000.0, 800.0],
    'cash_from_operations_cr': [1200.0, 900.0],
    'net_profit': [500.0, 400.0],
    'compounded_sales_growth': [15.0, 14.0],
    'compounded_profit_growth': [12.0, 11.0],
    'debt_to_equity': [0.1, 0.2],
    'interest_coverage': [20.0, 15.0]
})

try:
    sector_scores = test_df2.groupby('broad_sector', group_keys=True).apply(
        _compute_sector_score, include_groups=False
    )
    print("Sector scores:")
    print(sector_scores)
    print("Type:", type(sector_scores))
    sector_scores = sector_scores.droplevel(0)
    print("After droplevel:")
    print(sector_scores)
    test_df2['sector_relative_score'] = sector_scores.reindex(test_df2.index)
    print("Success!")
    print(test_df2)
except Exception as e:
    import traceback
    traceback.print_exc()

# Test with 2 companies in DIFFERENT sectors
test_df3 = pd.DataFrame({
    'company_id': ['TCS', 'HDFCBANK'],
    'broad_sector': ['Information Technology', 'Financials'],
    'return_on_equity_pct': [50.0, 18.0],
    'net_profit_margin_pct': [20.0, 15.0],
    'free_cash_flow_cr': [1000.0, 500.0],
    'cash_from_operations_cr': [1200.0, 600.0],
    'net_profit': [500.0, 300.0],
    'compounded_sales_growth': [15.0, 10.0],
    'compounded_profit_growth': [12.0, 8.0],
    'debt_to_equity': [0.1, 5.0],
    'interest_coverage': [20.0, 2.0]
})

print("\n\nTest DF 3 (different sectors):")
try:
    sector_scores3 = test_df3.groupby('broad_sector', group_keys=True).apply(
        _compute_sector_score, include_groups=False
    )
    print("Sector scores:")
    print(sector_scores3)
    sector_scores3 = sector_scores3.droplevel(0)
    print("After droplevel:")
    print(sector_scores3)
    test_df3['sector_relative_score'] = sector_scores3.reindex(test_df3.index)
    print("Success!")
    print(test_df3)
except Exception as e:
    import traceback
    traceback.print_exc()