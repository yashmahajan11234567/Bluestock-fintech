"""Diagnostic script for coverage gaps in pros/cons generator."""
import pandas as pd
from src.nlp.pros_cons_generator import (
    load_company_data,
    rule_pro_1_roe_sustained, rule_pro_2_fcf_positive_5y, rule_pro_3_de_ratio_zero,
    rule_pro_4_revenue_cagr_15pct, rule_pro_5_opm_25pct, rule_pro_6_pat_cagr_20pct,
    rule_pro_7_icr_high_or_debt_free, rule_pro_8_dividend_yield_and_fcf,
    rule_pro_9_eps_cagr_15pct, rule_pro_10_roe_improving_3y,
    rule_pro_11_revenue_cagr_gt_pat_cagr, rule_pro_12_assets_growing_declining_debt,
    rule_con_1_debt_to_equity_high, rule_con_2_fcf_negative_3y, rule_con_3_opm_declining_3y,
    rule_con_4_net_profit_negative, rule_con_5_revenue_declining_2y, rule_con_6_icr_low,
    rule_con_7_dividend_payout_over_100, rule_con_8_debt_to_equity_rising_3y,
    rule_con_9_eps_declining_3y, rule_con_10_roce_low, rule_con_11_net_debt_3x_ebitda,
    rule_con_12_revenue_cagr_under_5pct,
)

PRO_RULES = [
    ('PRO_1', rule_pro_1_roe_sustained),
    ('PRO_2', rule_pro_2_fcf_positive_5y),
    ('PRO_3', rule_pro_3_de_ratio_zero),
    ('PRO_4', rule_pro_4_revenue_cagr_15pct),
    ('PRO_5', rule_pro_5_opm_25pct),
    ('PRO_6', rule_pro_6_pat_cagr_20pct),
    ('PRO_7', rule_pro_7_icr_high_or_debt_free),
    ('PRO_8', rule_pro_8_dividend_yield_and_fcf),
    ('PRO_9', rule_pro_9_eps_cagr_15pct),
    ('PRO_10', rule_pro_10_roe_improving_3y),
    ('PRO_11', rule_pro_11_revenue_cagr_gt_pat_cagr),
    ('PRO_12', rule_pro_12_assets_growing_declining_debt),
]

CON_RULES = [
    ('CON_1', rule_con_1_debt_to_equity_high),
    ('CON_2', rule_con_2_fcf_negative_3y),
    ('CON_3', rule_con_3_opm_declining_3y),
    ('CON_4', rule_con_4_net_profit_negative),
    ('CON_5', rule_con_5_revenue_declining_2y),
    ('CON_6', rule_con_6_icr_low),
    ('CON_7', rule_con_7_dividend_payout_over_100),
    ('CON_8', rule_con_8_debt_to_equity_rising_3y),
    ('CON_9', rule_con_9_eps_declining_3y),
    ('CON_10', rule_con_10_roce_low),
    ('CON_11', rule_con_11_net_debt_3x_ebitda),
    ('CON_12', rule_con_12_revenue_cagr_under_5pct),
]

companies = ['SBIN', 'BRITANNIA', 'BEL', 'HINDUNILVR']

for c in companies:
    data = load_company_data(c)
    print(f"=== {c} (sector: {data.sector}) ===")

    # Show available data
    if not data.financial_ratios.empty:
        years = sorted(data.financial_ratios["year"].dropna().tolist())
        print(f"  FR years: {years}")
    if not data.pl_data.empty:
        years = sorted(data.pl_data["year"].dropna().tolist())
        print(f"  PL years: {years}")
    print(f"  BS rows: {len(data.bs_data)}")
    if not data.market_cap.empty:
        years = sorted(data.market_cap["year"].dropna().tolist())
        print(f"  MC years: {years}")

    # Run all PRO rules
    print("  PRO rules:")
    for rid, fn in PRO_RULES:
        try:
            result = fn(data)
            if result:
                print(f"    {rid}: TRUE (conf={result.confidence_pct}, text={result.text[:60]}...)")
            else:
                print(f"    {rid}: FALSE")
        except Exception as e:
            print(f"    {rid}: ERROR - {e}")

    print("  CON rules:")
    for rid, fn in CON_RULES:
        try:
            result = fn(data)
            if result:
                print(f"    {rid}: TRUE (conf={result.confidence_pct}, text={result.text[:60]}...)")
            else:
                print(f"    {rid}: FALSE")
        except Exception as e:
            print(f"    {rid}: ERROR - {e}")
    print()
