"""
Integration tests for src/analytics/pipeline.py — Financial Ratios Pipeline.

Verifies that the pipeline correctly computes all metrics from raw financial data
and that NULL values are handled correctly.
"""

import sys
from pathlib import Path

import pytest

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import the analytics module directly using importlib to avoid package conflicts
import importlib.util
pipeline_path = Path(__file__).parents[2] / "src" / "analytics" / "pipeline.py"
spec = importlib.util.spec_from_file_location("analytics.pipeline", pipeline_path)
analytics_pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_pipeline)

calculate_financial_metrics = analytics_pipeline.calculate_financial_metrics


class TestFinancialMetricsPipeline:
    """Tests for calculate_financial_metrics()."""

    def sample_financial_data(self) -> dict:
        """Return a realistic sample financial data dictionary."""
        return {
            # Profit & Loss data
            "net_profit": 500_00,
            "sales": 2000_00,
            "operating_profit": 600_00,
            "other_income": 50_00,
            "interest": 100_00,

            # Balance Sheet data
            "equity_capital": 500_00,
            "reserves": 1500_00,
            "borrowings": 2000_00,
            "total_assets": 5000_00,
            "investments": 300_00,

            # Cash Flow data
            "operating_cashflow": 700_00,
            "capital_expenditure": 200_00,

            # Growth data (for CAGR)
            "revenue_start": 1000_00,
            "revenue_end": 2000_00,
            "revenue_years": 5,

            # Sector for leverage flag
            "broad_sector": "Technology",
        }

    def test_returns_dict(self):
        """Returned object should be a dictionary."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        assert isinstance(result, dict)

    def test_expected_top_level_keys_exist(self):
        """All five top-level category keys should exist."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        expected_keys = [
            "profitability",
            "leverage",
            "growth",
            "cash_flow",
            "capital_allocation",
        ]
        for key in expected_keys:
            assert key in result, f"Missing top-level key: {key}"

    def test_profitability_keys_exist(self):
        """All profitability keys should exist in result['profitability']."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        prof = result["profitability"]

        assert "net_profit_margin" in prof
        assert "operating_profit_margin" in prof
        assert "roe" in prof
        assert "roce" in prof
        assert "roa" in prof

    def test_leverage_keys_exist(self):
        """All leverage keys should exist in result['leverage']."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        lev = result["leverage"]

        assert "debt_to_equity" in lev
        assert "interest_coverage_ratio" in lev
        assert "interest_coverage_label" in lev
        assert "interest_coverage_warning" in lev
        assert "high_leverage_flag" in lev
        assert "net_debt" in lev
        assert "asset_turnover" in lev

    def test_growth_keys_exist(self):
        """All growth keys should exist in result['growth']."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        gr = result["growth"]

        assert "revenue_cagr" in gr
        assert "cagr_grade" in gr
        assert "growth_bucket" in gr
        assert "growth_score" in gr
        assert "is_high_growth" in gr
        assert "is_negative_growth" in gr
        assert "is_multibagger_growth" in gr

    def test_cash_flow_keys_exist(self):
        """All cash flow keys should exist in result['cash_flow']."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        cf = result["cash_flow"]

        assert "operating_cashflow_ratio" in cf
        assert "cash_conversion_ratio" in cf
        assert "free_cash_flow" in cf
        assert "fcf_status" in cf
        assert "cashflow_quality" in cf

    def test_capital_allocation_keys_exist(self):
        """All capital allocation keys should exist in result['capital_allocation']."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        ca = result["capital_allocation"]

        assert "capital_allocation_category" in ca
        assert "capital_score" in ca
        assert "is_capital_efficient" in ca
        assert "needs_capital_review" in ca

    def test_profitability_values_correct(self):
        """Profitability metrics should match expected calculations."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        prof = result["profitability"]

        # net_profit_margin = (500 / 2000) * 100 = 25%
        assert prof["net_profit_margin"] == 25.0

        # operating_profit_margin = (600 / 2000) * 100 = 30%
        assert prof["operating_profit_margin"] == 30.0

        # ROE = 500 / (500 + 1500) * 100 = 25%
        assert prof["roe"] == 25.0

        # ROCE = (operating_profit + other_income) / (equity + reserves + borrowings) * 100
        # EBIT = 600 + 50 = 650
        # Capital employed = 500 + 1500 + 2000 = 4000
        # ROCE = 650 / 4000 * 100 = 16.25%
        assert prof["roce"] == 16.25

        # ROA = (500 / 5000) * 100 = 10%
        assert prof["roa"] == 10.0

    def test_leverage_values_correct(self):
        """Leverage metrics should match expected calculations."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        lev = result["leverage"]

        # debt_to_equity = 2000 / (500 + 1500) = 1.0
        assert lev["debt_to_equity"] == 1.0

        # interest_coverage = (600 + 50) / 100 = 6.5
        assert lev["interest_coverage_ratio"] == 6.5

        # interest_coverage_label = "Debt Free" (interest > 0, but function returns "Debt Free" if interest is None or 0... wait)
        # interest_coverage_label returns "Debt Free" if interest is None or 0, else None
        # interest_expense = 100 (> 0), so label should be None
        # Wait, the test output shows 'Debt Free' - let me check the function
        # Actually interest_coverage_label(interest) returns "Debt Free" if interest is None or 0, else None
        # Here interest = 100, so label should be None

        assert lev["interest_coverage_label"] is None

        # interest_coverage_warning = False (6.5 >= 1.5)
        assert lev["interest_coverage_warning"] is False

        # high_leverage_flag = False (D/E = 1.0 <= 5, sector not financial)
        assert lev["high_leverage_flag"] is False

        # net_debt = 200000 - 30000 = 170000
        assert lev["net_debt"] == 170000.0

        # asset_turnover = 2000 / 5000 = 0.4
        assert lev["asset_turnover"] == 0.4

    def test_growth_values_correct(self):
        """Growth metrics should match expected calculations."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        gr = result["growth"]

        # revenue_cagr = ((2000/1000)^(1/5) - 1) * 100 = (2^0.2 - 1) * 100 ≈ 14.87%
        assert gr["revenue_cagr"] is not None
        assert round(gr["revenue_cagr"], 2) == 14.87

        # cagr_grade for ~14.87% = "Healthy" (10 <= 14.87 < 20)
        assert gr["cagr_grade"] == "Healthy"

        # growth_bucket for ~14.87% = "Moderate" (10 <= 14.87 < 20)
        assert gr["growth_bucket"] == "Moderate"

        # growth_score for ~14.87% = 2 (10 <= 14.87 < 20)
        assert gr["growth_score"] == 2

        # is_high_growth = False (14.87 < 20)
        assert gr["is_high_growth"] is False

        # is_negative_growth = False (14.87 >= 0)
        assert gr["is_negative_growth"] is False

        # is_multibagger_growth = False (14.87 < 25)
        assert gr["is_multibagger_growth"] is False

    def test_cash_flow_values_correct(self):
        """Cash flow metrics should match expected calculations."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        cf = result["cash_flow"]

        # operating_cashflow_ratio = 700 / 2000 = 0.35
        assert cf["operating_cashflow_ratio"] == 0.35

        # cash_conversion_ratio = 700 / 500 = 1.4
        assert cf["cash_conversion_ratio"] == 1.4

        # free_cash_flow = 70000 - 20000 = 50000
        assert cf["free_cash_flow"] == 50000.0

        # fcf_status = "Positive" (500 > 0)
        assert cf["fcf_status"] == "Positive"

        # cashflow_quality = "Excellent" (1.4 >= 1.2)
        assert cf["cashflow_quality"] == "Excellent"

    def test_capital_allocation_values_correct(self):
        """Capital allocation metrics should match expected calculations."""
        data = self.sample_financial_data()
        result = calculate_financial_metrics(data)
        ca = result["capital_allocation"]

        # ROE = 25%, ROCE = 16.25%, CCR = 1.4
        # capital_allocation_category:
        # ROE >= 20, ROCE >= 15, CCR >= 1.0 -> "Good"
        # Not "Excellent" because ROCE (16.25) < 20
        assert ca["capital_allocation_category"] == "Good"

        # capital_score for "Good" = 4
        assert ca["capital_score"] == 4

        # is_capital_efficient for "Good" = True
        assert ca["is_capital_efficient"] is True

        # needs_capital_review for "Good" = False
        assert ca["needs_capital_review"] is False

    def test_none_inputs_propagate(self):
        """None inputs should result in None/False outputs where appropriate."""
        data = self.sample_financial_data()
        data_missing = data.copy()
        data_missing["net_profit"] = None

        result = calculate_financial_metrics(data_missing)
        prof = result["profitability"]
        ca = result["capital_allocation"]

        # Net profit margin should be None
        assert prof["net_profit_margin"] is None

        # ROE should be None
        assert prof["roe"] is None

        # ROCE should be computed from EBIT (operating_profit + other_income),
        # which is still present even when net_profit is None.
        # ROCE = (600 + 50) / (500 + 1500 + 2000) * 100 = 650/4000*100 = 16.25
        assert prof["roce"] == 16.25

        # ROA should be None
        assert prof["roa"] is None

        # Capital allocation should be None (missing ROE/ROCE)
        assert ca["capital_allocation_category"] is None
        assert ca["capital_score"] == 0

    def test_zero_sales_handled(self):
        """Zero sales should not cause division errors."""
        data = self.sample_financial_data()
        data["sales"] = 0

        result = calculate_financial_metrics(data)
        prof = result["profitability"]
        lev = result["leverage"]
        cf = result["cash_flow"]

        # Ratios with sales in denominator should be None
        assert prof["net_profit_margin"] is None
        assert prof["operating_profit_margin"] is None
        # asset_turnover returns 0.0 for sales=0 (the function guards
        # sales is None, not sales == 0)
        assert lev["asset_turnover"] == 0.0
        assert cf["operating_cashflow_ratio"] is None

    def test_missing_growth_data_handled(self):
        """Missing growth data should result in None/Unknown for growth metrics."""
        data = self.sample_financial_data()
        del data["revenue_start"]
        del data["revenue_end"]
        del data["revenue_years"]

        result = calculate_financial_metrics(data)
        gr = result["growth"]

        assert gr["revenue_cagr"] is None
        assert gr["cagr_grade"] is None
        assert gr["growth_bucket"] == "Unknown"
        assert gr["growth_score"] == 0
        assert gr["is_high_growth"] is False
        assert gr["is_negative_growth"] is False
        assert gr["is_multibagger_growth"] is False

    def test_missing_cash_flow_data_handled(self):
        """Missing cash flow data should result in None for cash flow metrics."""
        data = self.sample_financial_data()
        del data["operating_cashflow"]
        del data["capital_expenditure"]

        result = calculate_financial_metrics(data)
        cf = result["cash_flow"]

        assert cf["operating_cashflow_ratio"] is None
        assert cf["cash_conversion_ratio"] is None
        assert cf["free_cash_flow"] is None
        # fcf_status of None returns None
        assert cf["fcf_status"] is None
        # cashflow_quality of None returns None
        assert cf["cashflow_quality"] is None