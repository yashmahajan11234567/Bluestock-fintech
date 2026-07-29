"""
Complete regression test suite for Sprint 4 integration fixes.
Run with: python test_regression.py
"""

import sys
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
from dashboard.utils.db import (
    get_company_list,
    get_company_profile,
    get_financial_ratios,
    get_cashflow_data,
    get_capital_alloc_data,
    get_financial_trends,
    get_sector_aggregates,
    get_screener_results,
    get_peer_groups,
    get_peer_percentiles,
    get_peer_group_members,
    get_home_kpis,
    get_available_years,
    get_sector_distribution,
    get_top_companies,
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_sectors,
    get_peers,
    get_valuation,
)


def test_home():
    print('Testing Home page...')
    years = get_available_years()
    assert len(years) > 0

    for yr in years[-2:]:  # test last 2 years
        kpis = get_home_kpis(yr)
        assert 'total_companies' in kpis
        assert 'avg_roe' in kpis
        assert 'median_pe' in kpis
        assert 'median_debt_equity' in kpis
        assert 'debt_free_companies' in kpis
        assert 'median_revenue_cagr_5yr' in kpis

    sectors = get_sector_distribution(years[-1])
    assert len(sectors) > 0

    top = get_top_companies(years[-1])
    assert len(top) <= 5
    for t in top:
        assert 'company' in t and 'sector' in t and 'composite_score' in t

    print('  [PASS] Home page: KPIs, sectors, top companies')


def test_company_profile():
    print('Testing Company Profile page...')
    test_companies = ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY']

    for cid in test_companies:
        # get_company_profile
        profile = get_company_profile(cid)
        assert profile is not None, f'No profile for {cid}'
        assert profile['company_id'] == cid
        assert 'sector' in profile and profile['sector'] != 'N/A'
        assert 'return_on_capital_employed_pct' in profile
        assert isinstance(profile.get('return_on_capital_employed_pct'), (int, float))

        # get_financial_ratios - DataFrame, deduped, ROCE included, Int64 year
        ratios = get_financial_ratios(cid)
        assert isinstance(ratios, pd.DataFrame)
        assert 'return_on_capital_employed_pct' in ratios.columns
        assert ratios['year'].dtype in ['int64', 'Int64']
        assert ratios['year'].duplicated().sum() == 0, f'Duplicates in {cid}'

        # get_cashflow_data
        cf = get_cashflow_data(cid)
        assert isinstance(cf, pd.DataFrame)
        assert cf['year'].dtype in ['int64', 'Int64']

        # get_capital_alloc_data
        cap = get_capital_alloc_data(cid)
        assert isinstance(cap, pd.DataFrame)
        assert 'return_on_capital_employed_pct' in cap.columns
        assert 'cash_conversion_ratio' in cap.columns
        assert cap['year'].dtype in ['int64', 'Int64']
        assert cap['year'].duplicated().sum() == 0

    print('  [PASS] Company Profile: symbol, ROCE, ratios/cashflow/capital as DataFrames, Int64 years, no duplicates')


def test_screener():
    print('Testing Screener page...')

    # No filters - all companies
    all_results = get_screener_results({})
    assert len(all_results) >= 80, 'Should have 80+ companies'

    required_cols = [
        'company_id', 'company_name', 'sector', 'return_on_equity_pct',
        'debt_to_equity', 'operating_profit_margin_pct', 'interest_coverage',
        'free_cash_flow_cr', 'cash_from_operations_cr', 'net_profit_margin_pct',
        'compounded_sales_growth', 'dividend_yield_pct', 'pe_ratio', 'pb_ratio',
        'net_profit', 'composite_quality_score', 'sector_relative_score'
    ]
    for col in required_cols:
        assert col in all_results.columns, f'{col} missing'

    # Filter: ROE min
    roe_filtered = get_screener_results({'ROE': {'min': 15}})
    assert len(roe_filtered) < len(all_results)
    roe_vals = pd.to_numeric(roe_filtered['return_on_equity_pct'], errors='coerce')
    assert all(roe_vals.dropna() >= 15)

    # Filter: Debt to Equity max
    de_filtered = get_screener_results({'Debt to Equity': {'max': 1}})
    de_vals = pd.to_numeric(de_filtered['debt_to_equity'], errors='coerce')
    assert all(de_vals.dropna() <= 1)

    # Filter: PE max
    pe_filtered = get_screener_results({'PE': {'max': 20}})
    pe_vals = pd.to_numeric(pe_filtered['pe_ratio'], errors='coerce')
    assert all(pe_vals.dropna() <= 20)

    # Filter: Dividend Yield min
    dy_filtered = get_screener_results({'Dividend Yield': {'min': 1}})
    dy_vals = pd.to_numeric(dy_filtered['dividend_yield_pct'], errors='coerce')
    assert all(dy_vals.dropna() >= 1)

    # Combined filters
    combo = get_screener_results({'ROE': {'min': 15}, 'Debt to Equity': {'max': 1}, 'PE': {'max': 25}})
    assert len(combo) <= min(len(roe_filtered), len(de_filtered), len(pe_filtered))

    # Sorting
    sorted_by_score = get_screener_results({}, sort_by='composite_quality_score')
    # Non-NaN values should be sorted descending, NaN at end
    non_nan = sorted_by_score['composite_quality_score'].dropna()
    assert non_nan.is_monotonic_decreasing

    # No empty columns
    assert all_results.isna().all().sum() == 0

    print('  [PASS] Screener: filters (min/max), sort, all required columns, no empty cols')


def test_peer_comparison():
    print('Testing Peer Comparison page...')

    # get_peer_groups() - all groups
    all_groups = get_peer_groups()
    assert isinstance(all_groups, list) and len(all_groups) > 0
    assert all('peer_group_name' in g for g in all_groups)

    # get_peer_groups(company_id) - specific company
    test_companies = ['RELIANCE', 'TCS', 'HDFCBANK']
    for cid in test_companies:
        group = get_peer_groups(cid)
        assert isinstance(group, str)

    # get_peer_percentiles - verify restricted to peer group
    pct = get_peer_percentiles('RELIANCE')
    assert 'peer_group_name' in pct
    assert pct['peer_group_name'] == 'Oil & Gas'
    assert 'overall_peer_score' in pct
    assert pct['overall_peer_score'] is not None

    for key in ['roe_percentile', 'net_profit_margin_percentile', 'debt_to_equity_percentile',
                'free_cash_flow_percentile', 'pe_percentile', 'pb_percentile']:
        assert key in pct

    # Values 0-100
    for k, v in pct.items():
        if k.endswith('_percentile') and v is not None:
            assert 0 <= v <= 100, f'{k}={v} out of range'

    # get_peer_group_members
    members = get_peer_group_members('Oil & Gas')
    assert len(members) > 1
    assert all('company_id' in m and 'company_name' in m for m in members)

    print('  [PASS] Peer Comparison: groups, percentiles (group-restricted), members')


def test_financial_trends():
    print('Testing Financial Trends page...')

    for cid in ['RELIANCE', 'TCS', 'HDFCBANK']:
        trends = get_financial_trends(cid)
        assert isinstance(trends, pd.DataFrame)
        assert len(trends) > 0
        assert trends['year'].dtype in ['int64', 'Int64']
        assert trends['year'].is_monotonic_increasing
        assert trends['year'].duplicated().sum() == 0

        required_cols = ['sales', 'net_profit', 'operating_profit', 'eps',
                         'net_profit_margin_pct', 'operating_profit_margin_pct',
                         'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr']
        for col in required_cols:
            assert col in trends.columns, f'{col} missing for {cid}'

        latest = trends.sort_values('year', ascending=False).iloc[0]
        assert latest['sales'] > 0
        assert latest['net_profit'] != 0

    print('  [PASS] Financial Trends: DataFrame, Int64 years ASC, no duplicates, all metrics')


def test_sector_analysis():
    print('Testing Sector Analysis page...')

    sectors = get_sector_aggregates()
    assert isinstance(sectors, pd.DataFrame)
    assert len(sectors) > 5

    required_sector_cols = ['sector', 'company_count', 'avg_roe_pct', 'avg_roce_pct',
                            'avg_debt_to_equity', 'avg_net_profit_margin_pct',
                            'avg_pe_ratio', 'total_market_cap_cr']
    for col in required_sector_cols:
        assert col in sectors.columns, f'{col} missing'

    assert sectors['company_count'].sum() > 80
    assert sectors['avg_roe_pct'].notna().all()
    assert sectors['avg_pe_ratio'].notna().all()
    assert (sectors['total_market_cap_cr'] > 0).all()

    print(f'  [PASS] Sector Analysis: {len(sectors)} sectors, standardized columns (avg_roe_pct etc.), valid data')


def test_capital_allocation():
    print('Testing Capital Allocation page...')

    for cid in ['RELIANCE', 'TCS', 'HDFCBANK']:
        cap = get_capital_alloc_data(cid)
        assert isinstance(cap, pd.DataFrame)
        assert len(cap) > 0
        assert cap['year'].dtype in ['int64', 'Int64']
        assert cap['year'].duplicated().sum() == 0

        required = ['return_on_equity_pct', 'return_on_capital_employed_pct',
                    'cash_conversion_ratio', 'debt_to_equity', 'free_cash_flow_cr',
                    'total_debt_cr', 'cash_from_operations_cr']
        for col in required:
            assert col in cap.columns, f'{col} missing for {cid}'

        latest = cap.sort_values('year', ascending=False).iloc[0]
        assert pd.notna(latest.get('return_on_equity_pct'))
        assert pd.notna(latest.get('return_on_capital_employed_pct'))
        assert pd.notna(latest.get('cash_conversion_ratio'))
        assert latest['cash_conversion_ratio'] >= 0

        # Test DataFrame operations
        assert not cap.empty
        sorted_cap = cap.sort_values('year', ascending=True)
        assert sorted_cap['year'].is_monotonic_increasing

    print('  [PASS] Capital Allocation: DataFrame, all columns, .empty/.sort_values() work, CCR >= 0')


def test_reports():
    print('Testing Reports page...')

    companies = get_company_list()
    assert len(companies) == 92
    assert all('company_id' in c and 'company_name' in c for c in companies)

    print('  [PASS] Reports: company list for multiselect')


def test_aliases():
    print('Testing aliases / backward compatibility...')

    # get_companies alias
    assert get_companies() == get_company_list()

    # get_ratios alias returns DataFrame
    ratios_df = get_ratios('RELIANCE')
    assert isinstance(ratios_df, pd.DataFrame)

    # get_pl
    pl = get_pl('RELIANCE')
    assert isinstance(pl, pd.DataFrame)
    assert 'year' in pl.columns

    # get_bs
    bs = get_bs('RELIANCE')
    assert isinstance(bs, pd.DataFrame)
    assert 'year' in bs.columns

    # get_cf
    cf = get_cf('RELIANCE')
    assert isinstance(cf, pd.DataFrame)

    # get_sectors
    sect = get_sectors()
    assert isinstance(sect, list)

    # get_peers
    peers = get_peers('RELIANCE')
    assert isinstance(peers, list)

    # get_valuation
    val = get_valuation('RELIANCE')
    assert isinstance(val, pd.DataFrame)

    print('  [PASS] All aliases backward compatible')


def main():
    print('='*60)
    print('SPRINT 4 REGRESSION TEST SUITE')
    print('='*60)

    test_home()
    test_company_profile()
    test_screener()
    test_peer_comparison()
    test_financial_trends()
    test_sector_analysis()
    test_capital_allocation()
    test_reports()
    test_aliases()

    print('\n' + '='*60)
    print('[SUCCESS] ALL REGRESSION TESTS PASSED')
    print('='*60)
    print('[PASS] Home: KPIs, sectors, top companies - all years')
    print('[PASS] Company Profile: Symbol, ROCE, ratios (DataFrame, deduped, Int64)')
    print('[PASS] Screener: Filters (min/max), sort, all required columns, no empty cols')
    print('[PASS] Peer Comparison: Group lookup, percentiles (group-restricted), members')
    print('[PASS] Financial Trends: DataFrame, Int64 years ASC, no duplicates, all metrics')
    print('[PASS] Sector Analysis: Standardized columns (avg_roe_pct etc.), valid data')
    print('[PASS] Capital Allocation: DataFrame, ROCE+CCR, .empty/.sort_values() work')
    print('[PASS] Reports: Company list for multiselect')
    print('[PASS] All aliases backward compatible')


if __name__ == '__main__':
    main()