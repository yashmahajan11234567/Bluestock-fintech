from src.screener.engine import run_screener
import warnings

# Test with very restrictive filters to trigger the bug
# The bug occurs when filtered_df has few companies across sectors
# Quality Compounder gave 21 companies, let me try to get fewer

# Test with filter that might produce only 1-2 companies
filters = {
    'ROE': {'min': 30},  # Very high ROE
    'Debt to Equity': {'max': 0.5},
    'Free Cash Flow': {'min': 1000},
    'Revenue CAGR': {'min': 15}
}

print("Testing restrictive filters...")
try:
    result = run_screener(filters=filters)
    print(f'Result shape: {result.shape}')
    if len(result) > 0:
        print(result[['company_id', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr', 'compounded_sales_growth', 'composite_quality_score', 'sector_relative_score']].to_string())
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n\nTesting with original Quality Compounder filters (which gave 21)...")
filters2 = {'ROE': {'min': 15}, 'Debt to Equity': {'max': 1}, 'Free Cash Flow': {'min': 0}, 'Revenue CAGR': {'min': 10}}
result2 = run_screener(filters=filters2)
print(f'Result shape: {result2.shape}')
if len(result2) > 0:
    print(result2[['company_id', 'broad_sector', 'sector_relative_score']].to_string())

# Also test the sector scoring logic in isolation
print("\n\nTesting sector scoring with edge cases...")
import pandas as pd
import numpy as np

def _winsorize_and_scale(series, higher_is_better=True):
    s = pd.to_numeric(series, errors='coerce')
    nan = s.isna()
    valid = s[~nan]
    if valid.empty:
        return pd.Series(np.nan, index=series.index)
    p10, p90 = valid.quantile([0.10, 0.90])
    s = s.clip(lower=p10, upper=p90)
    mn, mx = s.min(), s.max()
    if mx == mn:
        res = pd.Series(50.0, index=series.index)
        res[nan] = np.nan
    else:
        res = (s - mn) / (mx - mn) * 100.0
        res[nan] = np.nan
    if not higher_is_better:
        res = 100.0 - res
    return res

# Test with a single company
test_df = pd.DataFrame({
    'company_id': ['TCS'],
    'broad_sector': ['Information Technology'],
    'return_on_equity_pct': [50.0],
    'net_profit_margin_pct': [20.0],
    'free_cash_flow_cr': [1000.0],
    'cash_from_operations_cr': [1200.0],
    'net_profit': [500.0],
    'compounded_sales_growth': [15.0],
    'compounded_profit_growth': [12.0],
    'debt_to_equity': [0.1],
    'interest_coverage': [20.0]
})

print("Test DF:")
print(test_df)

try:
    sector_scores = test_df.groupby("broad_sector", group_keys=False).apply(
        lambda g: (0.35 * (0.6 * _winsorize_and_scale(g["return_on_equity_pct"], True) +
                                   0.4 * _winsorize_and_scale(g["net_profit_margin_pct"], True)) +
                          0.30 * (0.5 * _winsorize_and_scale(g["free_cash_flow_cr"], True) +
                           (1/3) * _winsorize_and_scale(g["cash_from_operations_cr"] / g["net_profit"].replace(0, np.nan), True) +
                           (1/6) * (g["free_cash_flow_cr"] > 0).astype(float) * 100.0) +
                          0.20 * (0.5 * _winsorize_and_scale(g["compounded_sales_growth"], True) +
                                   0.5 * _winsorize_and_scale(g["compounded_profit_growth"], True)) +
                          0.15 * ((2/3) * _winsorize_and_scale(g["debt_to_equity"], False) +
                                   (1/3) * _winsorize_and_scale(g["interest_coverage"], True)))
    )
    print("Sector scores:")
    print(sector_scores)
    print("Type:", type(sector_scores))
    print("Values:", sector_scores.values)
    print("Length:", len(sector_scores.values))
    test_df["sector_relative_score"] = sector_scores.values
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()

# Test with 2 companies in different sectors
test_df2 = pd.DataFrame({
    'company_id': ['TCS', 'INFY'],
    'broad_sector': ['Information Technology', 'Information Technology'],  # Same sector
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

print("\n\nTest DF 2 (same sector):")
print(test_df2)

try:
    sector_scores2 = test_df2.groupby("broad_sector", group_keys=False).apply(
        lambda g: (0.35 * (0.6 * _winsorize_and_scale(g["return_on_equity_pct"], True) +
                                   0.4 * _winsorize_and_scale(g["net_profit_margin_pct"], True)) +
                          0.30 * (0.5 * _winsorize_and_scale(g["free_cash_flow_cr"], True) +
                           (1/3) * _winsorize_and_scale(g["cash_from_operations_cr"] / g["net_profit"].replace(0, np.nan), True) +
                           (1/6) * (g["free_cash_flow_cr"] > 0).astype(float) * 100.0) +
                          0.20 * (0.5 * _winsorize_and_scale(g["compounded_sales_growth"], True) +
                                   0.5 * _winsorize_and_scale(g["compounded_profit_growth"], True)) +
                          0.15 * ((2/3) * _winsorize_and_scale(g["debt_to_equity"], False) +
                                   (1/3) * _winsorize_and_scale(g["interest_coverage"], True)))
    )
    print("Sector scores:")
    print(sector_scores2)
    test_df2["sector_relative_score"] = sector_scores2.values
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()

# Test with 2 companies in DIFFERENT sectors
test_df3 = pd.DataFrame({
    'company_id': ['TCS', 'HDFCBANK'],
    'broad_sector': ['Information Technology', 'Financials'],  # DIFFERENT sectors
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
print(test_df3)

try:
    sector_scores3 = test_df3.groupby("broad_sector", group_keys=False).apply(
        lambda g: (0.35 * (0.6 * _winsorize_and_scale(g["return_on_equity_pct"], True) +
                                   0.4 * _winsorize_and_scale(g["net_profit_margin_pct"], True)) +
                          0.30 * (0.5 * _winsorize_and_scale(g["free_cash_flow_cr"], True) +
                           (1/3) * _winsorize_and_scale(g["cash_from_operations_cr"] / g["net_profit"].replace(0, np.nan), True) +
                           (1/6) * (g["free_cash_flow_cr"] > 0).astype(float) * 100.0) +
                          0.20 * (0.5 * _winsorize_and_scale(g["compounded_sales_growth"], True) +
                                   0.5 * _winsorize_and_scale(g["compounded_profit_growth"], True)) +
                          0.15 * ((2/3) * _winsorize_and_scale(g["debt_to_equity"], False) +
                                   (1/3) * _winsorize_and_scale(g["interest_coverage"], True)))
    )
    print("Sector scores:")
    print(sector_scores3)
    print("Type:", type(sector_scores3))
    print("Values:", sector_scores3.values)
    print("Length:", len(sector_scores3.values))
    test_df3["sector_relative_score"] = sector_scores3.values
    print("Success! Result:")
    print(test_df3)
except Exception as e:
    import traceback
    traceback.print_exc()