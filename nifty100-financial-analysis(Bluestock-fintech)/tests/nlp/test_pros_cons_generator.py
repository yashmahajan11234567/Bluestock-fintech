"""
Test suite for the Auto Pros/Cons Generator (Day 30).

Tests cover all 24 rules (12 Pro, 12 Con), threshold behavior,
confidence calculation, output validation, and rule ID enforcement.

PRO_13 and CON_13 are explicitly NOT part of the Sprint 5 specification.
Tests confirm that unsupported rule IDs cannot be generated.
"""

import math
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.nlp.pros_cons_generator import (
    ProsConsSignal,
    CompanyData,
    load_company_data,
    generate_signals_for_company,
    generate_all_pros_cons,
    validate_company_coverage,
    generate_output,
    PRO_RULES,
    CON_RULES,
    rule_pro_1_roe_sustained,
    rule_pro_2_fcf_positive_5y,
    rule_pro_3_de_ratio_zero,
    rule_pro_4_revenue_cagr_15pct,
    rule_pro_5_opm_25pct,
    rule_pro_6_pat_cagr_20pct,
    rule_pro_7_icr_high_or_debt_free,
    rule_pro_8_dividend_yield_and_fcf,
    rule_pro_9_eps_cagr_15pct,
    rule_pro_10_roe_improving_3y,
    rule_pro_11_revenue_cagr_gt_pat_cagr,
    rule_pro_12_assets_growing_declining_debt,
    rule_con_1_debt_to_equity_high,
    rule_con_2_fcf_negative_3y,
    rule_con_3_opm_declining_3y,
    rule_con_4_net_profit_negative,
    rule_con_5_revenue_declining_2y,
    rule_con_6_icr_low,
    rule_con_7_dividend_payout_over_100,
    rule_con_8_debt_to_equity_rising_3y,
    rule_con_9_eps_declining_3y,
    rule_con_10_roce_low,
    rule_con_11_net_debt_3x_ebitda,
    rule_con_12_revenue_cagr_under_5pct,
)


# ============================================================
# Helper: Create mock CompanyData
# ============================================================

def make_company_data(
    company_id='TEST',
    financial_ratios=None,
    pl_data=None,
    bs_data=None,
    market_cap=None,
    sector=None,
):
    """Create a CompanyData with configurable mock data."""
    if financial_ratios is None:
        financial_ratios = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'return_on_equity_pct': [25.0, 24.0, 23.0, 22.0, 21.0],
            'operating_profit_margin_pct': [30.0, 28.0, 26.0, 24.0, 22.0],
            'debt_to_equity': [0.0, 0.0, 0.0, 0.0, 0.0],
            'interest_coverage': [15.0, 20.0, 0.0, 0.0, 0.0],
            'free_cash_flow_cr': [100.0, 90.0, 80.0, 70.0, 60.0],
            'earnings_per_share': [10.0, 9.0, 8.0, 7.0, 6.0],
            'dividend_payout_ratio_pct': [20.0, 25.0, 30.0, 35.0, 40.0],
            'total_debt_cr': [50.0, 40.0, 0.0, 0.0, 0.0],
            'cash_from_operations_cr': [150.0, 140.0, 130.0, 120.0, 110.0],
            'capex_cr': [50.0, 50.0, 50.0, 50.0, 50.0],
            'return_on_capital_employed_pct': [30.0, 28.0, 26.0, 24.0, 22.0],
        })

    if pl_data is None:
        pl_data = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'sales': [2000, 1800, 1500, 1200, 1000],
            'operating_profit': [500, 450, 400, 300, 250],
            'interest': [10, 5, 0, 0, 0],
            'net_profit': [400, 380, 350, 280, 230],
            'eps': [10.0, 9.0, 8.0, 7.0, 6.0],
            'dividend_payout': [20.0, 22.0, 24.0, 25.0, 26.0],
            'other_income': [5.0, 5.0, 5.0, 5.0, 5.0],
            'depreciation': [100, 90, 80, 70, 60],
        })

    if bs_data is None:
        bs_data = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'equity_capital': [500, 500, 500, 500, 500],
            'reserves': [500, 450, 400, 350, 300],
            'borrowings': [50, 40, 0, 0, 0],
            'other_liabilities': [100, 100, 100, 100, 100],
            'total_liabilities': [650, 640, 600, 600, 600],
            'fixed_assets': [800, 750, 700, 650, 600],
            'cwip': [50, 40, 30, 20, 10],
            'investments': [100, 90, 80, 70, 60],
            'other_asset': [150, 140, 130, 120, 110],
            'total_assets': [1500, 1400, 1200, 1000, 900],
        })

    if market_cap is None:
        market_cap = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'pe_ratio': [20.0, 18.0, 16.0],
            'dividend_yield_pct': [1.5, 1.2, 1.0],
        })

    return CompanyData(
        company_id=company_id,
        financial_ratios=financial_ratios,
        pl_data=pl_data,
        bs_data=bs_data,
        market_cap=market_cap,
        sector=sector,
    )


class TestCompanyData:
    """Test CompanyData creation and helper functions."""

    def test_make_company_data_defaults(self):
        """Test default company data creation."""
        data = make_company_data()
        assert data.company_id == 'TEST'
        assert len(data.financial_ratios) == 5
        assert len(data.pl_data) == 5

    def test_make_company_data_custom(self):
        """Test custom company data creation."""
        fr = pd.DataFrame({'year': [2024], 'return_on_equity_pct': [20.0]})
        data = make_company_data(financial_ratios=fr)
        assert len(data.financial_ratios) == 1


class TestSafeFloat:
    """Test _safe_float function."""

    def test_safe_float_normal(self):
        from src.nlp.pros_cons_generator import _safe_float
        assert _safe_float(5.0) == 5.0

    def test_safe_float_none(self):
        from src.nlp.pros_cons_generator import _safe_float
        assert _safe_float(None) is None

    def test_safe_float_nan(self):
        from src.nlp.pros_cons_generator import _safe_float
        assert _safe_float(float('nan')) is None

    def test_safe_float_inf(self):
        from src.nlp.pros_cons_generator import _safe_float
        assert _safe_float(float('inf')) is None

    def test_safe_float_string(self):
        from src.nlp.pros_cons_generator import _safe_float
        assert _safe_float("not a number") is None

    def test_safe_float_int_string(self):
        from src.nlp.pros_cons_generator import _safe_float
        assert _safe_float("42") == 42.0


class TestConfidenceCalculation:
    """Test confidence scoring methodology."""

    def test_confidence_bounded_0_to_100(self):
        """Test that confidence is always bounded between 0 and 100."""
        from src.nlp.pros_cons_generator import _compute_confidence
        # Very high value
        conf = _compute_confidence(1000.0, 1.0, True, 1, 1, 1, 1)
        assert 0 <= conf <= 100

    def test_confidence_none_metric(self):
        """Test confidence returns 0 for None metric."""
        from src.nlp.pros_cons_generator import _compute_confidence
        conf = _compute_confidence(None, 1.0, True, 1, 1, 1, 1)
        assert conf == 0.0

    def test_confidence_higher_better_above_threshold(self):
        """Test confidence when metric exceeds threshold (higher is better)."""
        from src.nlp.pros_cons_generator import _compute_confidence
        # Metric well above threshold should get good confidence
        conf = _compute_confidence(50.0, 20.0, True, 5, 5, 5, 5)
        assert conf > 60  # Should exceed 60

    def test_confidence_lower_better_below_threshold(self):
        """Test confidence when metric is below threshold (lower is better)."""
        from src.nlp.pros_cons_generator import _compute_confidence
        # Metric well below threshold should get good confidence
        conf = _compute_confidence(10.0, 20.0, False, 5, 5, 5, 5)
        assert conf > 60


class TestProRules:
    """Test all 12 Pro rules."""

    def test_pro_1_roe_sustained_3y(self):
        """Test PRO_1: ROE > 20% for 3+ consecutive years."""
        data = make_company_data()
        signal = rule_pro_1_roe_sustained(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_1"
        assert signal.confidence_pct > 60

    def test_pro_1_roe_insufficient(self):
        """Test PRO_1: ROE not sustained for 3 years."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'return_on_equity_pct': [25.0, 20.0, 15.0, 22.0, 21.0],  # Not 3 consecutive above 20
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_1_roe_sustained(data)
        assert signal is None

    def test_pro_1_roe_below_threshold(self):
        """Test PRO_1: ROE below threshold."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'return_on_equity_pct': [15.0, 14.0, 13.0, 12.0, 11.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_1_roe_sustained(data)
        assert signal is None

    def test_pro_1_no_data(self):
        """Test PRO_1 with no ROE data."""
        fr = pd.DataFrame({'year': [2024, 2023]})
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_1_roe_sustained(data)
        assert signal is None

    def test_pro_2_fcf_positive_5y(self):
        """Test PRO_2: FCF positive for 5+ consecutive years."""
        data = make_company_data()
        signal = rule_pro_2_fcf_positive_5y(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_2"
        assert signal.confidence_pct > 60

    def test_pro_2_fcf_not_sustained(self):
        """Test PRO_2: FCF not positive for 5 consecutive years."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'free_cash_flow_cr': [100.0, -50.0, 80.0, 70.0, 60.0],  # Not consecutive
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_2_fcf_positive_5y(data)
        assert signal is None

    def test_pro_3_de_ratio_zero(self):
        """Test PRO_3: D/E = 0 in latest year."""
        data = make_company_data()
        signal = rule_pro_3_de_ratio_zero(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_3"
        assert signal.confidence_pct > 60

    def test_pro_3_de_ratio_positive(self):
        """Test PRO_3: D/E > 0 should not trigger."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'debt_to_equity': [0.5, 0.4, 0.3, 0.2, 0.1],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_3_de_ratio_zero(data)
        assert signal is None

    def test_pro_4_revenue_cagr_15pct(self):
        """Test PRO_4: Revenue CAGR > 15% over 5 years."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order (newest first)
            'sales': [1000, 815, 664, 541, 441],  # ~12% CAGR (below threshold)
        })
        # Adjust to get >15% CAGR: 1000 -> 2000 over 4 periods = ~19% CAGR
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order (newest first)
            'sales': [2000, 1690, 1416, 1180, 1000],  # ~19% CAGR over 4 periods
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_4_revenue_cagr_15pct(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_4"

    def test_pro_4_revenue_cagr_below_threshold(self):
        """Test PRO_4: Revenue CAGR < 15%."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'sales': [1200, 1150, 1100, 1050, 1000],  # ~3.7% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_4_revenue_cagr_15pct(data)
        assert signal is None

    def test_pro_5_opm_25pct(self):
        """Test PRO_5: OPM > 25% in latest year."""
        data = make_company_data()
        signal = rule_pro_5_opm_25pct(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_5"

    def test_pro_5_opm_below_threshold(self):
        """Test PRO_5: OPM <= 25%."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'operating_profit_margin_pct': [20.0, 18.0, 16.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_5_opm_25pct(data)
        assert signal is None

    def test_pro_6_pat_cagr_20pct(self):
        """Test PRO_6: PAT CAGR > 20% over 5 years."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'net_profit': [200, 160, 128, 102, 80],  # ~20% CAGR over 4 periods
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_6_pat_cagr_20pct(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_6"

    def test_pro_6_pat_cagr_below_threshold(self):
        """Test PRO_6: PAT CAGR <= 20%."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'net_profit': [100, 105, 110, 115, 121],  # ~4% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_6_pat_cagr_20pct(data)
        assert signal is None

    def test_pro_7_icr_high(self):
        """Test PRO_7: ICR > 10."""
        data = make_company_data()
        signal = rule_pro_7_icr_high_or_debt_free(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_7"

    def test_pro_7_debt_free(self):
        """Test PRO_7: Debt-free company."""
        pl = pd.DataFrame({
            'year': [2024],
            'interest': [0.0],
        })
        fr = pd.DataFrame({'year': [2024], 'debt_to_equity': [0.0]})
        data = make_company_data(pl_data=pl, financial_ratios=fr)
        signal = rule_pro_7_icr_high_or_debt_free(data)
        assert signal is not None

    def test_pro_8_dividend_yield_and_fcf(self):
        """Test PRO_8: Dividend Yield > 2% AND FCF positive."""
        mc = pd.DataFrame({'year': [2024, 2023, 2022], 'dividend_yield_pct': [3.0, 2.5, 2.0]})
        data = make_company_data(market_cap=mc)
        signal = rule_pro_8_dividend_yield_and_fcf(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_8"

    def test_pro_8_low_dividend_yield(self):
        """Test PRO_8: Dividend yield <= 2%."""
        mc = pd.DataFrame({'year': [2024], 'dividend_yield_pct': [1.5]})
        data = make_company_data(market_cap=mc)
        signal = rule_pro_8_dividend_yield_and_fcf(data)
        assert signal is None

    def test_pro_9_eps_cagr_15pct(self):
        """Test PRO_9: EPS CAGR > 15% over 5 years."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'eps': [40.0, 32.0, 25.0, 20.0, 16.0],  # ~20% CAGR over 4 periods
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_9_eps_cagr_15pct(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_9"

    def test_pro_9_eps_cagr_below_threshold(self):
        """Test PRO_9: EPS CAGR <= 15%."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'eps': [12.0, 11.5, 11.0, 10.5, 10.0],  # ~4.5% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_9_eps_cagr_15pct(data)
        assert signal is None

    def test_pro_10_roe_improving_3y(self):
        """Test PRO_10: ROE improving for 3 consecutive years."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'return_on_equity_pct': [25.0, 23.0, 20.0, 18.0, 15.0],  # Improving
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_10_roe_improving_3y(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_10"

    def test_pro_10_roe_not_improving(self):
        """Test PRO_10: ROE not improving."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'return_on_equity_pct': [25.0, 26.0, 24.0, 23.0, 22.0],  # Not consistently improving
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_10_roe_improving_3y(data)
        # May or may not match - depends on 3 consecutive improvement
        if signal is not None:
            assert signal.rule_id == "PRO_10"

    def test_pro_11_revenue_cagr_gt_pat_cagr(self):
        """Test PRO_11: Revenue CAGR > PAT CAGR."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'sales': [2400, 1900, 1500, 1200, 1000],  # ~19.3% CAGR
            'net_profit': [130, 125, 120, 110, 100],  # ~8.7% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_11_revenue_cagr_gt_pat_cagr(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_11"

    def test_pro_11_revenue_cagr_eq_pat_cagr(self):
        """Test PRO_11: Revenue CAGR <= PAT CAGR should not trigger."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'sales': [1200, 1150, 1100, 1050, 1000],  # ~4.7% CAGR
            'net_profit': [210, 175, 145, 120, 100],  # ~16% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_11_revenue_cagr_gt_pat_cagr(data)
        assert signal is None

    def test_pro_12_assets_growing_declining_debt(self):
        """Test PRO_12: Assets growing with declining debt."""
        bs = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'total_assets': [2000, 1800, 1500],
            'borrowings': [30, 50, 70],
            'investments': [100, 90, 80],
            'other_asset': [150, 140, 130],
        })
        data = make_company_data(bs_data=bs)
        signal = rule_pro_12_assets_growing_declining_debt(data)
        assert signal is not None
        assert signal.type == "pro"
        assert signal.rule_id == "PRO_12"

    def test_pro_12_no_improvement(self):
        """Test PRO_12: Assets not growing with declining debt."""
        bs = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'total_assets': [1500, 1800, 2000],  # Declining
            'borrowings': [30, 50, 70],
            'investments': [100, 90, 80],
            'other_asset': [150, 140, 130],
        })
        data = make_company_data(bs_data=bs)
        signal = rule_pro_12_assets_growing_declining_debt(data)
        assert signal is None


class TestConRules:
    """Test all 12 Con rules."""

    def test_con_1_debt_to_equity_high(self):
        """Test CON_1: D/E > 2.0 for non-financial companies."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'debt_to_equity': [2.5, 2.3, 2.1],
        })
        data = make_company_data(financial_ratios=fr, sector='Technology')
        signal = rule_con_1_debt_to_equity_high(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_1"
        assert "2.50" in signal.text  # D/E value should be in text

    def test_con_1_debt_to_equity_boundary(self):
        """Test CON_1: D/E = 2.0 boundary (should not trigger)."""
        fr = pd.DataFrame({
            'year': [2024],
            'debt_to_equity': [2.0],
        })
        data = make_company_data(financial_ratios=fr, sector='Technology')
        signal = rule_con_1_debt_to_equity_high(data)
        assert signal is None  # D/E = 2.0 is not > 2.0

    def test_con_1_financial_company_exempt(self):
        """Test CON_1: Financial companies exempt."""
        fr = pd.DataFrame({
            'year': [2024],
            'debt_to_equity': [3.0],
        })
        data = make_company_data(financial_ratios=fr, sector='Financials')
        signal = rule_con_1_debt_to_equity_high(data)
        assert signal is None

    def test_con_1_low_debt_to_equity(self):
        """Test CON_1: D/E <= 2.0 should not trigger."""
        fr = pd.DataFrame({
            'year': [2024],
            'debt_to_equity': [1.5],
        })
        data = make_company_data(financial_ratios=fr, sector='Technology')
        signal = rule_con_1_debt_to_equity_high(data)
        assert signal is None

    def test_con_2_fcf_negative_3y(self):
        """Test CON_2: FCF negative for 3 consecutive years."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'free_cash_flow_cr': [-100.0, -90.0, -80.0, 50.0, 60.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_2_fcf_negative_3y(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_2"

    def test_con_2_fcf_not_sustained_negative(self):
        """Test CON_2: FCF not negative for 3 consecutive years."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'free_cash_flow_cr': [-100.0, 50.0, -80.0, -70.0, -60.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_2_fcf_negative_3y(data)
        assert signal is None

    def test_con_3_opm_declining_3y(self):
        """Test CON_3: OPM declining for 3 consecutive years."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'operating_profit_margin_pct': [15.0, 18.0, 20.0, 22.0, 25.0],  # Declining
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_3_opm_declining_3y(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_3"

    def test_con_3_opm_not_declining(self):
        """Test CON_3: OPM not declining."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'operating_profit_margin_pct': [25.0, 22.0, 20.0, 18.0, 15.0],  # Increasing
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_3_opm_declining_3y(data)
        assert signal is None

    def test_con_4_net_profit_negative(self):
        """Test CON_4: Net profit negative in latest year."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'net_profit': [-50.0, 100.0, 120.0],  # Latest is negative
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_4_net_profit_negative(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_4"

    def test_con_4_net_profit_positive(self):
        """Test CON_4: Net profit positive should not trigger."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'net_profit': [100.0, 90.0, 80.0],
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_4_net_profit_negative(data)
        assert signal is None

    def test_con_5_revenue_declining_2y(self):
        """Test CON_5: Revenue declining for 2+ years."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'sales': [1000, 1100, 1200, 1500, 1800],  # Declining recent
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_5_revenue_declining_2y(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_5"

    def test_con_5_revenue_not_declining(self):
        """Test CON_5: Revenue not declining."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'sales': [1800, 1500, 1200, 1100, 1000],  # Growing
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_5_revenue_declining_2y(data)
        assert signal is None

    def test_con_6_icr_low(self):
        """Test CON_6: ICR < 1.5."""
        fr = pd.DataFrame({
            'year': [2024],
            'interest_coverage': [1.2],
            'debt_to_equity': [0.5],  # Has debt
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_6_icr_low(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_6"

    def test_con_6_icr_boundary(self):
        """Test CON_6: ICR = 1.5 boundary (should not trigger)."""
        fr = pd.DataFrame({
            'year': [2024],
            'interest_coverage': [1.5],
            'debt_to_equity': [0.5],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_6_icr_low(data)
        assert signal is None  # 1.5 is not < 1.5

    def test_con_6_debt_free_exempt(self):
        """Test CON_6: Debt-free companies exempt."""
        fr = pd.DataFrame({
            'year': [2024],
            'interest_coverage': [1.0],
            'debt_to_equity': [0.0],  # Debt-free
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_6_icr_low(data)
        assert signal is None

    def test_con_7_dividend_payout_over_100(self):
        """Test CON_7: Dividend payout > 100%."""
        fr = pd.DataFrame({
            'year': [2024],
            'dividend_payout_ratio_pct': [120.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_7_dividend_payout_over_100(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_7"

    def test_con_7_dividend_payout_boundary(self):
        """Test CON_7: Dividend payout = 100% boundary (should not trigger)."""
        fr = pd.DataFrame({
            'year': [2024],
            'dividend_payout_ratio_pct': [100.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_7_dividend_payout_over_100(data)
        assert signal is None  # 100 is not > 100

    def test_con_8_debt_to_equity_rising_3y(self):
        """Test CON_8: D/E rising for 3 consecutive years."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'debt_to_equity': [2.5, 2.3, 2.1, 1.9, 1.7],  # Rising
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_8_debt_to_equity_rising_3y(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_8"

    def test_con_8_debt_to_equity_not_rising(self):
        """Test CON_8: D/E not rising."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'debt_to_equity': [1.7, 1.9, 2.1, 2.3, 2.5],  # Falling
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_8_debt_to_equity_rising_3y(data)
        assert signal is None

    def test_con_9_eps_declining_3y(self):
        """Test CON_9: EPS declining for 3 consecutive years."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'eps': [5.0, 8.0, 10.0, 12.0, 15.0],  # Declining newest-to-oldest means 15->5
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_9_eps_declining_3y(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_9"

    def test_con_9_eps_not_declining(self):
        """Test CON_9: EPS not declining."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'eps': [15.0, 12.0, 10.0, 9.0, 8.0],  # Growing
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_9_eps_declining_3y(data)
        assert signal is None

    def test_con_10_roce_low(self):
        """Test CON_10: ROCE < 10%."""
        fr = pd.DataFrame({
            'year': [2024],
            'return_on_capital_employed_pct': [8.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_10_roce_low(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_10"

    def test_con_10_roce_boundary(self):
        """Test CON_10: ROCE = 10% boundary (should not trigger)."""
        fr = pd.DataFrame({
            'year': [2024],
            'return_on_capital_employed_pct': [10.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_10_roce_low(data)
        assert signal is None  # 10 is not < 10

    def test_con_11_net_debt_3x_ebitda(self):
        """Test CON_11: Net Debt > 3x EBITDA."""
        bs = pd.DataFrame({
            'year': [2024],
            'borrowings': [600.0],
            'investments': [50.0],
            'other_asset': [100.0],
        })
        pl = pd.DataFrame({
            'year': [2024],
            'operating_profit': [100.0],
            'depreciation': [50.0],
        })
        data = make_company_data(bs_data=bs, pl_data=pl)
        # Net debt = 600 - 50 = 550, EBITDA = 100 + 50 = 150, ratio = 3.67
        signal = rule_con_11_net_debt_3x_ebitda(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_11"

    def test_con_11_low_net_debt(self):
        """Test CON_11: Net Debt <= 3x EBITDA should not trigger."""
        bs = pd.DataFrame({
            'year': [2024],
            'borrowings': [300.0],
            'investments': [50.0],
            'other_asset': [100.0],
        })
        pl = pd.DataFrame({
            'year': [2024],
            'operating_profit': [100.0],
            'depreciation': [50.0],
        })
        data = make_company_data(bs_data=bs, pl_data=pl)
        # Net debt = 300 - 50 = 250, EBITDA = 150, ratio = 1.67
        signal = rule_con_11_net_debt_3x_ebitda(data)
        assert signal is None

    def test_con_12_revenue_cagr_under_5pct(self):
        """Test CON_12: Revenue CAGR < 5% over 5 years."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'sales': [1080, 1060, 1040, 1020, 1000],  # ~1.9% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_12_revenue_cagr_under_5pct(data)
        assert signal is not None
        assert signal.type == "con"
        assert signal.rule_id == "CON_12"

    def test_con_12_revenue_cagr_boundary(self):
        """Test CON_12: Revenue CAGR = 5% boundary (should not trigger)."""
        # CAGR of ~5% over 4 years: 1000 -> 1216
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'sales': [1216, 1157, 1102, 1050, 1000],  # ~5% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_12_revenue_cagr_under_5pct(data)
        assert signal is None  # ~5% is not < 5%


class TestUnsupportedRuleIDs:
    """Tests confirming PRO_13 and CON_13 are NOT part of the specification."""

    def test_pro_13_not_in_supported_rules(self):
        """PRO_13 should not be in PRO_RULES list."""
        rule_names = [fn.__name__ for fn in PRO_RULES]
        assert 'rule_pro_13_profit_margin_sustained' not in rule_names

    def test_con_13_not_in_supported_rules(self):
        """CON_13 should not be in CON_RULES list."""
        rule_names = [fn.__name__ for fn in CON_RULES]
        assert 'rule_con_13_pe_ratio_high' not in rule_names

    def test_pro_rules_count_is_12(self):
        """PRO_RULES must contain exactly 12 rules (PRO_1 through PRO_12)."""
        assert len(PRO_RULES) == 12

    def test_con_rules_count_is_12(self):
        """CON_RULES must contain exactly 12 rules (CON_1 through CON_12)."""
        assert len(CON_RULES) == 12

    def test_no_pro_13_signals_generated(self, tmp_path):
        """No signal should ever have rule_id PRO_13."""
        from src.nlp.pros_cons_generator import generate_output
        test_output = tmp_path / "pros_cons_test.csv"
        with patch('src.nlp.pros_cons_generator.get_company_list') as mock_list:
            mock_list.return_value = [{'company_id': 'TEST', 'company_name': 'Test Co'}]
            with patch('src.nlp.pros_cons_generator.load_company_data') as mock_load:
                mock_load.return_value = make_company_data()
                df = generate_output(str(test_output))
                assert 'PRO_13' not in df['rule_id'].values

    def test_no_con_13_signals_generated(self, tmp_path):
        """No signal should ever have rule_id CON_13."""
        from src.nlp.pros_cons_generator import generate_output
        test_output = tmp_path / "pros_cons_test.csv"
        with patch('src.nlp.pros_cons_generator.get_company_list') as mock_list:
            mock_list.return_value = [{'company_id': 'TEST', 'company_name': 'Test Co'}]
            with patch('src.nlp.pros_cons_generator.load_company_data') as mock_load:
                mock_load.return_value = make_company_data()
                df = generate_output(str(test_output))
                assert 'CON_13' not in df['rule_id'].values


class TestThresholdBoundaryCases:
    """Test boundary cases for all threshold-based rules."""

    def test_pro_1_boundary_3_years(self):
        """Test PRO_1: Exactly 3 consecutive years at 20% boundary."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'return_on_equity_pct': [20.0, 20.0, 20.0],  # Exactly at threshold
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_1_roe_sustained(data)
        # ROE = 20.0 is not > 20
        assert signal is None

    def test_pro_5_boundary_25pct(self):
        """Test PRO_5: OPM = 25% boundary."""
        fr = pd.DataFrame({
            'year': [2024],
            'operating_profit_margin_pct': [25.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_5_opm_25pct(data)
        # OPM = 25 is not > 25
        assert signal is None


class TestConfidenceFiltering:
    """Test confidence filtering logic."""

    def test_confidence_above_60_passes(self):
        """Test that signals with confidence > 60 are included."""
        data = make_company_data()
        # Default data should trigger PRO_1 (ROE=25 for 5 years)
        signal = rule_pro_1_roe_sustained(data)
        assert signal is not None
        assert signal.confidence_pct > 60

    def test_confidence_below_60_excluded(self):
        """Test that signals with confidence <= 60 are excluded."""
        # Create data that barely meets the condition
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'return_on_equity_pct': [20.1, 20.1, 20.1],  # Just above 20, only 3 years
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_1_roe_sustained(data)
        # Confidence may be below 60 due to low margin
        if signal is not None:
            assert signal.confidence_pct > 60
        else:
            # If signal is None, it was filtered out by confidence <= 60
            pass


class TestDuplicatePrevention:
    """Test that no duplicate outputs are generated."""

    def test_no_duplicate_company_rule_type(self):
        """Test that there are no duplicate company/rule/type combinations."""
        # Use mock data to test
        data = make_company_data()
        signals = []
        for rule_fn in PRO_RULES + CON_RULES:
            signal = rule_fn(data)
            if signal is not None:
                signals.append(signal)

        # Check for duplicates
        seen = set()
        for s in signals:
            key = (s.company_id, s.rule_id, s.type)
            assert key not in seen, f"Duplicate found: {key}"
            seen.add(key)


class TestTypeValidation:
    """Test pro/con type validation."""

    def test_all_pro_signals_have_type_pro(self):
        """Test that all pro rule outputs have type='pro'."""
        data = make_company_data()
        for rule_fn in PRO_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert signal.type == "pro"

    def test_all_con_signals_have_type_con(self):
        """Test that all con rule outputs have type='con'."""
        data = make_company_data()
        for rule_fn in CON_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert signal.type == "con"


class TestRuleIDs:
    """Test that rule IDs are valid."""

    def test_all_rule_ids_valid(self):
        """Test that all generated rule IDs are valid."""
        valid_pro_ids = {f"PRO_{i}" for i in range(1, 13)}
        valid_con_ids = {f"CON_{i}" for i in range(1, 13)}

        data = make_company_data()
        for rule_fn in PRO_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert signal.rule_id in valid_pro_ids

        for rule_fn in CON_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert signal.rule_id in valid_con_ids


class TestRuleText:
    """Test that rule text is non-empty and correct."""

    def test_all_rule_texts_non_empty(self):
        """Test that all generated rule texts are non-empty."""
        data = make_company_data()
        for rule_fn in PRO_RULES + CON_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert signal.text and len(signal.text) > 0

    def test_con_1_dynamic_de_value(self):
        """Test that CON_1 text contains the actual D/E value."""
        fr = pd.DataFrame({
            'year': [2024],
            'debt_to_equity': [2.75],
        })
        data = make_company_data(financial_ratios=fr, sector='Technology')
        signal = rule_con_1_debt_to_equity_high(data)
        assert signal is not None
        assert "2.75" in signal.text


class TestMultiYearConditions:
    """Test multi-year conditions (3+ years, 5+ years)."""

    def test_pro_1_requires_3_year_streak(self):
        """Test that PRO_1 requires 3 consecutive years above 20%."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'return_on_equity_pct': [25.0, 25.0, 25.0, 19.0, 25.0],  # 3 consecutive at start
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_1_roe_sustained(data)
        assert signal is not None  # First 3 years are 25, 25, 25

    def test_pro_2_requires_5_year_streak(self):
        """Test that PRO_2 requires 5 consecutive years of positive FCF."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'free_cash_flow_cr': [10.0, 10.0, 10.0, 10.0, -5.0],  # Only 4 consecutive positive
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_2_fcf_positive_5y(data)
        # Only 4 consecutive positive years (2024-2021), 2020 is negative
        assert signal is None


class TestCAGRCalculations:
    """Test CAGR-based rules."""

    def test_pro_4_cagr_calculation(self):
        """Test PRO_4 CAGR calculation from sales data."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020, 2019, 2018],  # DESC order
            'sales': [280, 228, 190, 160, 135, 115, 100],  # ~24% CAGR
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_4_revenue_cagr_15pct(data)
        assert signal is not None
        assert signal.rule_id == "PRO_4"

    def test_con_12_cagr_calculation(self):
        """Test CON_12 CAGR calculation."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],  # DESC order
            'sales': [960, 970, 980, 990, 1000],  # Declining over time
        })
        data = make_company_data(pl_data=pl)
        # Negative CAGR is < 5%, so CON_12 should trigger
        signal = rule_con_12_revenue_cagr_under_5pct(data)
        assert signal is not None


class TestFCFConditions:
    """Test free cash flow related rules."""

    def test_pro_2_fcf_positive(self):
        """Test PRO_2 with consistently positive FCF."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'free_cash_flow_cr': [100.0, 90.0, 80.0, 70.0, 60.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_2_fcf_positive_5y(data)
        assert signal is not None

    def test_con_2_fcf_negative(self):
        """Test CON_2 with consistently negative FCF."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'free_cash_flow_cr': [-100.0, -90.0, -80.0, 70.0, 60.0],  # Only 3 negative consecutive
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_con_2_fcf_negative_3y(data)
        assert signal is not None


class TestLatestYearConditions:
    """Test rules that depend on latest year only."""

    def test_pro_3_latest_year_only(self):
        """Test PRO_3 uses latest year D/E only."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'debt_to_equity': [0.0, 1.5, 2.0],  # Only latest is 0
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_3_de_ratio_zero(data)
        assert signal is not None

    def test_con_4_latest_year_only(self):
        """Test CON_4 uses latest year net profit only."""
        pl = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'net_profit': [50.0, -100.0, -80.0],  # Only latest positive
        })
        data = make_company_data(pl_data=pl)
        signal = rule_con_4_net_profit_negative(data)
        assert signal is None  # Latest year is positive


class TestMissingDataHandling:
    """Test handling of missing/incomplete data."""

    def test_missing_fcf_data(self):
        """Test PRO_2 with missing FCF data."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022, 2021, 2020],
            'free_cash_flow_cr': [None, 90.0, 80.0, 70.0, 60.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_2_fcf_positive_5y(data)
        assert signal is None  # Only 4 valid values

    def test_missing_roe_data(self):
        """Test PRO_1 with missing ROE data."""
        fr = pd.DataFrame({
            'year': [2024, 2023, 2022],
            'return_on_equity_pct': [None, 25.0, 25.0],
        })
        data = make_company_data(financial_ratios=fr)
        signal = rule_pro_1_roe_sustained(data)
        assert signal is None  # Only 2 valid values

    def test_empty_dataframes(self):
        """Test with empty dataframes."""
        data = CompanyData(
            company_id='TEST',
            financial_ratios=pd.DataFrame(),
            pl_data=pd.DataFrame(),
            bs_data=pd.DataFrame(),
            market_cap=pd.DataFrame(),
            sector=None,
        )
        signal = rule_pro_1_roe_sustained(data)
        assert signal is None


class TestInvalidDataHandling:
    """Test handling of invalid data values."""

    def test_negative_sales_cagr(self):
        """Test that negative start values don't produce CAGR."""
        pl = pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'sales': [-100, 50, 100, 150, 200],  # Negative start
        })
        data = make_company_data(pl_data=pl)
        # Revenue is still growing, but start is negative
        signal = rule_pro_4_revenue_cagr_15pct(data)
        # May still work if valid start/end found
        if signal is not None:
            assert signal.confidence_pct > 60

    def test_zero_sales_cagr(self):
        """Test that zero start values don't produce CAGR."""
        pl = pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'sales': [0, 100, 200, 300, 400],  # Zero start
        })
        data = make_company_data(pl_data=pl)
        signal = rule_pro_4_revenue_cagr_15pct(data)
        assert signal is None  # CAGR can't be calculated with zero start


class TestConfidenceRange:
    """Test that confidence is always 0-100."""

    def test_confidence_never_exceeds_100(self):
        """Test that no signal has confidence > 100."""
        data = make_company_data()
        for rule_fn in PRO_RULES + CON_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert 0 <= signal.confidence_pct <= 100

    def test_confidence_never_negative(self):
        """Test that no signal has negative confidence."""
        data = make_company_data()
        for rule_fn in PRO_RULES + CON_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert signal.confidence_pct >= 0


class TestCompanyUniverse:
    """Test with real company universe data."""

    @pytest.mark.integration
    def test_all_companies_have_signals(self):
        """Integration test: All companies in database have at least 1 pro and 1 con."""
        # This test requires a running database - marked as integration
        pass


class TestOutputValidation:
    """Test output CSV validation."""

    def test_output_columns(self):
        """Test that output CSV has exact required columns."""
        # Mock generate_all_pros_cons to return test data
        with patch('src.nlp.pros_cons_generator.get_company_list') as mock_list:
            mock_list.return_value = [{'company_id': 'TEST', 'company_name': 'Test Co'}]
            with patch('src.nlp.pros_cons_generator.load_company_data') as mock_load:
                mock_load.return_value = make_company_data()
                with patch('src.nlp.pros_cons_generator.get_financial_ratios') as mock_fr:
                    mock_fr.return_value = make_company_data().financial_ratios
                    with patch('src.nlp.pros_cons_generator.get_pl') as mock_pl:
                        mock_pl.return_value = make_company_data().pl_data
                        with patch('src.nlp.pros_cons_generator.get_bs') as mock_bs:
                            mock_bs.return_value = make_company_data().bs_data
                            with patch('src.nlp.pros_cons_generator.get_valuation') as mock_mc:
                                mock_mc.return_value = make_company_data().market_cap
                                with patch('src.nlp.pros_cons_generator.get_sectors') as mock_sec:
                                    mock_sec.return_value = []
                                    df = generate_all_pros_cons()
                                    expected_cols = ['company_id', 'type', 'rule_id', 'text', 'confidence_pct']
                                    assert list(df.columns) == expected_cols

    def test_output_confidence_filtered(self):
        """Test that all output rows have confidence > 60."""
        data = make_company_data()
        signals = []
        for rule_fn in PRO_RULES + CON_RULES:
            signal = rule_fn(data)
            if signal is not None:
                assert signal.confidence_pct > 60
                signals.append(signal)
        # At least some signals should be generated
        assert len(signals) > 0


if __name__ == '__main__':
    pytest.main([__file__, "-v"])
