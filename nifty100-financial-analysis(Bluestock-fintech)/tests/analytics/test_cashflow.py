"""
Tests for src/analytics/cashflow.py — Cash Flow KPI computations.

Covers normal calculations, edge cases, None inputs, and boundary conditions.
"""

import sys
from pathlib import Path
from math import isclose

import pytest

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import the analytics module directly using importlib to avoid package conflicts
import importlib.util
cashflow_path = Path(__file__).parents[2] / "src" / "analytics" / "cashflow.py"
spec = importlib.util.spec_from_file_location("analytics.cashflow", cashflow_path)
analytics_cashflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_cashflow)

operating_cashflow_ratio = analytics_cashflow.operating_cashflow_ratio
cash_conversion_ratio = analytics_cashflow.cash_conversion_ratio
free_cash_flow = analytics_cashflow.free_cash_flow
fcf_status = analytics_cashflow.fcf_status
cashflow_quality = analytics_cashflow.cashflow_quality


# =========================================================================
# operating_cashflow_ratio
# =========================================================================


class TestOperatingCashflowRatio:
    """Tests for operating_cashflow_ratio()."""

    def test_normal_calculation(self):
        """OCF 200 on sales 1000 -> 0.2."""
        result = operating_cashflow_ratio(200, 1000)
        assert isclose(result, 0.2)

    def test_negative_ocf(self):
        """Negative operating cash flow produces negative ratio."""
        result = operating_cashflow_ratio(-50, 1000)
        assert isclose(result, -0.05)

    def test_zero_ocf(self):
        """Zero operating cash flow produces 0.0 ratio."""
        result = operating_cashflow_ratio(0, 1000)
        assert isclose(result, 0.0)

    def test_sales_zero(self):
        """Zero sales returns None to avoid division by zero."""
        assert operating_cashflow_ratio(200, 0) is None

    def test_sales_negative(self):
        """Negative sales returns None."""
        assert operating_cashflow_ratio(200, -100) is None

    def test_ocf_none(self):
        """None operating_cashflow returns None."""
        assert operating_cashflow_ratio(None, 1000) is None

    def test_sales_none(self):
        """None sales returns None."""
        assert operating_cashflow_ratio(200, None) is None

    def test_both_none(self):
        """Both None returns None."""
        assert operating_cashflow_ratio(None, None) is None

    def test_float_inputs(self):
        """Float inputs work correctly."""
        result = operating_cashflow_ratio(150.0, 500.0)
        assert isclose(result, 0.3)


# =========================================================================
# cash_conversion_ratio
# =========================================================================


class TestCashConversionRatio:
    """Tests for cash_conversion_ratio()."""

    def test_normal_calculation(self):
        """OCF 200, net profit 100 -> 2.0."""
        result = cash_conversion_ratio(200, 100)
        assert isclose(result, 2.0)

    def test_negative_ocf(self):
        """Negative OCF produces negative ratio."""
        result = cash_conversion_ratio(-50, 100)
        assert isclose(result, -0.5)

    def test_negative_net_profit(self):
        """Negative net profit produces negative ratio."""
        result = cash_conversion_ratio(200, -100)
        assert isclose(result, -2.0)

    def test_both_negative(self):
        """Both negative produces positive ratio."""
        result = cash_conversion_ratio(-50, -100)
        assert isclose(result, 0.5)

    def test_zero_net_profit(self):
        """Zero net profit returns None to avoid division by zero."""
        assert cash_conversion_ratio(200, 0) is None

    def test_ocf_none(self):
        """None operating_cashflow returns None."""
        assert cash_conversion_ratio(None, 100) is None

    def test_net_profit_none(self):
        """None net_profit returns None."""
        assert cash_conversion_ratio(200, None) is None

    def test_both_none(self):
        """Both None returns None."""
        assert cash_conversion_ratio(None, None) is None


# =========================================================================
# free_cash_flow
# =========================================================================


class TestFreeCashFlow:
    """Tests for free_cash_flow()."""

    def test_positive_fcf(self):
        """OCF 500, Capex 200 -> 300."""
        result = free_cash_flow(500, 200)
        assert isclose(result, 300.0)

    def test_zero_fcf(self):
        """OCF 200, Capex 200 -> 0."""
        result = free_cash_flow(200, 200)
        assert isclose(result, 0.0)

    def test_negative_fcf(self):
        """OCF 100, Capex 300 -> -200."""
        result = free_cash_flow(100, 300)
        assert isclose(result, -200.0)

    def test_ocf_none(self):
        """None operating_cashflow returns None."""
        assert free_cash_flow(None, 200) is None

    def test_capex_none(self):
        """None capital_expenditure returns None."""
        assert free_cash_flow(500, None) is None

    def test_both_none(self):
        """Both None returns None."""
        assert free_cash_flow(None, None) is None


# =========================================================================
# fcf_status
# =========================================================================


class TestFCFStatus:
    """Tests for fcf_status()."""

    def test_positive(self):
        """Positive FCF returns 'Positive'."""
        assert fcf_status(100.0) == "Positive"
        assert fcf_status(0.1) == "Positive"
        assert fcf_status(1000) == "Positive"

    def test_zero(self):
        """Zero FCF returns 'Neutral'."""
        assert fcf_status(0.0) == "Neutral"
        assert fcf_status(0) == "Neutral"

    def test_negative(self):
        """Negative FCF returns 'Negative'."""
        assert fcf_status(-50.0) == "Negative"
        assert fcf_status(-0.1) == "Negative"
        assert fcf_status(-1000) == "Negative"

    def test_none(self):
        """None FCF returns None."""
        assert fcf_status(None) is None


# =========================================================================
# cashflow_quality
# =========================================================================


class TestCashflowQuality:
    """Tests for cashflow_quality()."""

    def test_excellent(self):
        """CCR >= 1.2 returns 'Excellent'."""
        assert cashflow_quality(1.2) == "Excellent"
        assert cashflow_quality(1.5) == "Excellent"
        assert cashflow_quality(2.0) == "Excellent"
        assert cashflow_quality(10.0) == "Excellent"

    def test_good(self):
        """CCR >= 1.0 and < 1.2 returns 'Good'."""
        assert cashflow_quality(1.0) == "Good"
        assert cashflow_quality(1.1) == "Good"
        assert cashflow_quality(1.19) == "Good"
        assert cashflow_quality(1.1999) == "Good"

    def test_average(self):
        """CCR >= 0.8 and < 1.0 returns 'Average'."""
        assert cashflow_quality(0.8) == "Average"
        assert cashflow_quality(0.9) == "Average"
        assert cashflow_quality(0.99) == "Average"
        assert cashflow_quality(0.9999) == "Average"

    def test_weak(self):
        """CCR < 0.8 returns 'Weak'."""
        assert cashflow_quality(0.79) == "Weak"
        assert cashflow_quality(0.5) == "Weak"
        assert cashflow_quality(0.0) == "Weak"
        assert cashflow_quality(-0.5) == "Weak"
        assert cashflow_quality(-1.0) == "Weak"

    def test_none(self):
        """None CCR returns None."""
        assert cashflow_quality(None) is None