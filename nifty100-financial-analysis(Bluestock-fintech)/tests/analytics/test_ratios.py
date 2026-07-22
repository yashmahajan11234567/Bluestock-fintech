"""
Tests for src/analytics/ratios.py â€” profitability ratio computations.

Covers normal calculation, zero denominator, None input, negative equity,
and non-positive denominator for each function.
"""

import sys
from pathlib import Path
from math import isclose

import pytest

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import the analytics module directly using importlib to avoid package conflicts
import importlib.util
analytics_path = Path(__file__).parents[2] / "src" / "analytics" / "ratios.py"
spec = importlib.util.spec_from_file_location("analytics.ratios", analytics_path)
analytics_ratios = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_ratios)

net_profit_margin = analytics_ratios.net_profit_margin
operating_profit_margin = analytics_ratios.operating_profit_margin
return_on_equity = analytics_ratios.return_on_equity
return_on_capital_employed = analytics_ratios.return_on_capital_employed
return_on_assets = analytics_ratios.return_on_assets
debt_to_equity = analytics_ratios.debt_to_equity
interest_coverage_ratio = analytics_ratios.interest_coverage_ratio
interest_coverage_label = analytics_ratios.interest_coverage_label
interest_coverage_warning = analytics_ratios.interest_coverage_warning
high_leverage_flag = analytics_ratios.high_leverage_flag
net_debt = analytics_ratios.net_debt
asset_turnover = analytics_ratios.asset_turnover

# =========================================================================
# net_profit_margin
# =========================================================================


class TestNetProfitMargin:
    """Tests for net_profit_margin()."""

    def test_normal_calculation(self):
        """Net profit of 200 on sales of 1000 gives 20%."""
        result = net_profit_margin(200, 1000)
        assert isclose(result, 20.0)

    def test_negative_net_profit(self):
        """A negative net profit produces a negative margin."""
        result = net_profit_margin(-50, 1000)
        assert isclose(result, -5.0)

    def test_zero_net_profit(self):
        """Net profit of 0 gives 0% margin."""
        result = net_profit_margin(0, 1000)
        assert isclose(result, 0.0)

    def test_sales_is_zero(self):
        """Zero sales returns None to avoid division by zero."""
        assert net_profit_margin(200, 0) is None

    def test_sales_is_none(self):
        """None sales returns None."""
        assert net_profit_margin(200, None) is None

    def test_net_profit_is_none(self):
        """None net_profit returns None."""
        assert net_profit_margin(None, 1000) is None

    def test_both_none(self):
        """Both arguments None returns None."""
        assert net_profit_margin(None, None) is None

    def test_float_inputs(self):
        """Float arguments produce correct margin."""
        result = net_profit_margin(50.0, 250.0)
        assert isclose(result, 20.0)


# =========================================================================
# operating_profit_margin
# =========================================================================


class TestOperatingProfitMargin:
    """Tests for operating_profit_margin()."""

    def test_normal_calculation(self):
        """Operating profit of 200 on sales of 1000 gives 20%."""
        result = operating_profit_margin(200, 1000)
        assert isclose(result, 20.0)

    def test_zero_operating_profit(self):
        """Operating profit of 0 gives 0% margin."""
        result = operating_profit_margin(0, 1000)
        assert isclose(result, 0.0)

    def test_sales_is_zero(self):
        """Zero sales returns None."""
        assert operating_profit_margin(200, 0) is None

    def test_sales_is_none(self):
        """None sales returns None."""
        assert operating_profit_margin(200, None) is None

    def test_operating_profit_is_none(self):
        """None operating_profit returns None."""
        assert operating_profit_margin(None, 1000) is None

    def test_both_none(self):
        """Both arguments None returns None."""
        assert operating_profit_margin(None, None) is None

    def test_negative_operating_profit(self):
        """Negative operating profit produces a negative margin."""
        result = operating_profit_margin(-30, 500)
        assert isclose(result, -6.0)


# =========================================================================
# return_on_equity
# =========================================================================


class TestReturnOnEquity:
    """Tests for return_on_equity()."""

    def test_normal_calculation(self):
        """Net profit 200, equity 100, reserves 200 â†’ 66.67% ROE."""
        result = return_on_equity(200, 100, 200)
        assert isclose(result, 200 / 300 * 100)

    def test_no_reserves(self):
        """Reserves of 0 still works."""
        result = return_on_equity(50, 100, 0)
        assert isclose(result, 50.0)

    def test_zero_equity_returns_none(self):
        """Total equity of 0 returns None."""
        assert return_on_equity(200, 0, 0) is None

    def test_negative_equity_returns_none(self):
        """Negative total equity (equity_capital + reserves <= 0) returns None."""
        assert return_on_equity(200, 100, -200) is None

    def test_all_none(self):
        """All None inputs returns None."""
        assert return_on_equity(None, None, None) is None

    def test_net_profit_none(self):
        """None net_profit returns None."""
        assert return_on_equity(None, 100, 200) is None

    def test_equity_capital_none(self):
        """None equity_capital returns None."""
        assert return_on_equity(200, None, 200) is None

    def test_reserves_none(self):
        """None reserves returns None."""
        assert return_on_equity(200, 100, None) is None

    def test_negative_net_profit(self):
        """Negative net profit produces negative ROE."""
        result = return_on_equity(-50, 100, 200)
        assert isclose(result, -50 / 300 * 100)


# =========================================================================
# return_on_capital_employed
# =========================================================================


class TestReturnOnCapitalEmployed:
    """Tests for return_on_capital_employed()."""

    def test_normal_calculation(self):
        """EBIT 300, equity 100, reserves 200, borrowings 50 â†’ ~85.71%."""
        result = return_on_capital_employed(300, 100, 200, 50)
        assert isclose(result, 300 / 350 * 100)

    def test_zero_borrowings(self):
        """Borrowings of 0 still produces a valid result."""
        result = return_on_capital_employed(200, 100, 200, 0)
        assert isclose(result, 200 / 300 * 100)

    def test_denominator_zero(self):
        """All equity components zero returns None."""
        assert return_on_capital_employed(300, 0, 0, 0) is None

    def test_denominator_negative(self):
        """Negative capital employed (borrowings large negative) returns None."""
        assert return_on_capital_employed(300, 100, 200, -400) is None

    def test_ebit_none(self):
        """None ebit returns None."""
        assert return_on_capital_employed(None, 100, 200, 50) is None

    def test_equity_capital_none(self):
        """None equity_capital returns None."""
        assert return_on_capital_employed(300, None, 200, 50) is None

    def test_reserves_none(self):
        """None reserves returns None."""
        assert return_on_capital_employed(300, 100, None, 50) is None

    def test_borrowings_none(self):
        """None borrowings returns None."""
        assert return_on_capital_employed(300, 100, 200, None) is None

    def test_all_none(self):
        """All None inputs returns None."""
        assert return_on_capital_employed(None, None, None, None) is None

    def test_negative_ebit(self):
        """Negative EBIT produces a negative ROCE."""
        result = return_on_capital_employed(-100, 100, 200, 50)
        assert isclose(result, -100 / 350 * 100)


# =========================================================================
# return_on_assets
# =========================================================================


class TestReturnOnAssets:
    """Tests for return_on_assets()."""

    def test_normal_calculation(self):
        """Net profit 200, total assets 1000 â†’ 20% ROA."""
        result = return_on_assets(200, 1000)
        assert isclose(result, 20.0)

    def test_zero_net_profit(self):
        """Net profit of 0 gives 0% ROA."""
        result = return_on_assets(0, 1000)
        assert isclose(result, 0.0)

    def test_negative_net_profit(self):
        """Negative net profit produces negative ROA."""
        result = return_on_assets(-50, 1000)
        assert isclose(result, -5.0)

    def test_total_assets_is_zero(self):
        """Zero total_assets returns None."""
        assert return_on_assets(200, 0) is None

    def test_total_assets_is_none(self):
        """None total_assets returns None."""
        assert return_on_assets(200, None) is None

    def test_net_profit_is_none(self):
        """None net_profit returns None."""
        assert return_on_assets(None, 1000) is None

    def test_both_none(self):
        """Both arguments None returns None."""
        assert return_on_assets(None, None) is None

    def test_float_inputs(self):
        """Float arguments produce correct ROA."""
        result = return_on_assets(50.0, 500.0)
        assert isclose(result, 10.0)


# =========================================================================
# debt_to_equity
# =========================================================================


class TestDebtToEquity:
    """Tests for debt_to_equity()."""

    def test_normal_calculation(self):
        """Borrowings 100, equity 200, reserves 300 â†’ 0.2 D/E."""
        result = debt_to_equity(100, 200, 300)
        assert isclose(result, 0.2)

    def test_zero_borrowings(self):
        """Zero borrowings returns 0.0."""
        result = debt_to_equity(0, 100, 200)
        assert isclose(result, 0.0)

    def test_negative_borrowings(self):
        """Negative borrowings produces negative D/E."""
        result = debt_to_equity(-50, 100, 200)
        assert isclose(result, -50 / 300)

    def test_denominator_zero(self):
        """Zero total equity returns None."""
        assert debt_to_equity(100, 0, 0) is None

    def test_denominator_negative(self):
        """Negative total equity returns None."""
        assert debt_to_equity(100, 50, -100) is None

    def test_borrowings_none(self):
        """None borrowings returns None."""
        assert debt_to_equity(None, 100, 200) is None

    def test_equity_capital_none(self):
        """None equity_capital returns None."""
        assert debt_to_equity(100, None, 200) is None

    def test_reserves_none(self):
        """None reserves returns None."""
        assert debt_to_equity(100, 100, None) is None

    def test_all_none(self):
        """All None inputs returns None."""
        assert debt_to_equity(None, None, None) is None


# =========================================================================
# interest_coverage_ratio
# =========================================================================


class TestInterestCoverageRatio:
    """Tests for interest_coverage_ratio()."""

    def test_normal_calculation(self):
        """OP 200, OI 50, interest 50 â†’ 5.0."""
        result = interest_coverage_ratio(200, 50, 50)
        assert isclose(result, 5.0)

    def test_positive_negative_operating_profit(self):
        """OP -100, OI 200, interest 50 â†’ 2.0."""
        result = interest_coverage_ratio(-100, 200, 50)
        assert isclose(result, 2.0)

    def test_negative_other_income(self):
        """OP 200, OI -50, interest 50 â†’ 3.0."""
        result = interest_coverage_ratio(200, -50, 50)
        assert isclose(result, 3.0)

    def test_negative_both(self):
        """OP -100, OI -50, interest 50 â†’ -3.0."""
        result = interest_coverage_ratio(-100, -50, 50)
        assert isclose(result, -3.0)

    def test_interest_zero(self):
        """Zero interest returns None."""
        assert interest_coverage_ratio(200, 50, 0) is None

    def test_interest_none(self):
        """None interest returns None."""
        assert interest_coverage_ratio(200, 50, None) is None

    def test_operating_profit_none(self):
        """None operating_profit returns None."""
        assert interest_coverage_ratio(None, 50, 50) is None

    def test_other_income_none(self):
        """None other_income returns None."""
        assert interest_coverage_ratio(200, None, 50) is None


# =========================================================================
# interest_coverage_label
# =========================================================================


class TestInterestCoverageLabel:
    """Tests for interest_coverage_label()."""

    def test_interest_zero(self):
        """Zero interest returns 'Debt Free'."""
        assert interest_coverage_label(0) == "Debt Free"

    def test_interest_none(self):
        """None interest returns 'Debt Free'."""
        assert interest_coverage_label(None) == "Debt Free"

    def test_interest_positive(self):
        """Positive interest returns None."""
        assert interest_coverage_label(50) is None

    def test_interest_negative(self):
        """Negative interest returns None."""
        assert interest_coverage_label(-10) is None


# =========================================================================
# interest_coverage_warning
# =========================================================================


class TestInterestCoverageWarning:
    """Tests for interest_coverage_warning()."""

    def test_below_threshold(self):
        """ICR below 1.5 returns True."""
        assert interest_coverage_warning(1.0) is True
        assert interest_coverage_warning(1.49) is True
        assert interest_coverage_warning(0.5) is True
        assert interest_coverage_warning(-1.0) is True

    def test_at_threshold(self):
        """ICR at 1.5 returns False."""
        assert interest_coverage_warning(1.5) is False

    def test_above_threshold(self):
        """ICR above 1.5 returns False."""
        assert interest_coverage_warning(2.0) is False
        assert interest_coverage_warning(5.0) is False

    def test_none_icr(self):
        """None ICR returns False."""
        assert interest_coverage_warning(None) is False


# =========================================================================
# high_leverage_flag
# =========================================================================


class TestHighLeverageFlag:
    """Tests for high_leverage_flag()."""

    def test_non_financial_high_de(self):
        """Non-financial sector with D/E > 5 returns True."""
        assert high_leverage_flag(6.0, "Technology") is True
        assert high_leverage_flag(5.1, "Industrials") is True

    def test_financial_sector_exempt(self):
        """Financials sector is exempt even with high D/E."""
        assert high_leverage_flag(6.0, "Financials") is False
        assert high_leverage_flag(10.0, "FINANCIALS") is False
        assert high_leverage_flag(10.0, "financials") is False
        assert high_leverage_flag(10.0, "Financial Services") is False

    def test_below_threshold(self):
        """D/E <= 5 returns False regardless of sector."""
        assert high_leverage_flag(5.0, "Technology") is False
        assert high_leverage_flag(4.0, "Technology") is False

    def test_none_dti(self):
        """None D/E returns False."""
        assert high_leverage_flag(None, "Technology") is False

    def test_none_sector(self):
        """None sector returns False."""
        assert high_leverage_flag(6.0, None) is False

    def test_empty_sector(self):
        """Empty sector returns False (treated as non-financial)."""
        assert high_leverage_flag(6.0, "") is True


# =========================================================================
# net_debt
# =========================================================================


class TestNetDebt:
    """Tests for net_debt()."""

    def test_normal_calculation(self):
        """Borrowings 1000, investments 200 â†’ 800.0."""
        result = net_debt(1000, 200)
        assert isclose(result, 800.0)

    def test_net_cash_position(self):
        """Borrowings 200, investments 1000 â†’ -800.0 (net cash)."""
        result = net_debt(200, 1000)
        assert isclose(result, -800.0)

    def test_zero_borrowings(self):
        """Zero borrowings returns negative investments."""
        result = net_debt(0, 500)
        assert isclose(result, -500.0)

    def test_zero_investments(self):
        """Zero investments returns borrowings."""
        result = net_debt(500, 0)
        assert isclose(result, 500.0)

    def test_borrowings_none(self):
        """None borrowings returns None."""
        assert net_debt(None, 200) is None

    def test_investments_none(self):
        """None investments returns None."""
        assert net_debt(1000, None) is None

    def test_both_none(self):
        """Both None returns None."""
        assert net_debt(None, None) is None


# =========================================================================
# asset_turnover
# =========================================================================


class TestAssetTurnover:
    """Tests for asset_turnover()."""

    def test_normal_calculation(self):
        """Sales 1000, assets 500 â†’ 2.0."""
        result = asset_turnover(1000, 500)
        assert isclose(result, 2.0)

    def test_zero_sales(self):
        """Zero sales returns 0.0."""
        result = asset_turnover(0, 500)
        assert isclose(result, 0.0)

    def test_negative_sales(self):
        """Negative sales produces negative turnover."""
        result = asset_turnover(-100, 500)
        assert isclose(result, -0.2)

    def test_assets_zero(self):
        """Zero assets returns None."""
        assert asset_turnover(1000, 0) is None

    def test_assets_negative(self):
        """Negative assets returns None."""
        assert asset_turnover(1000, -500) is None

    def test_assets_none(self):
        """None assets returns None."""
        assert asset_turnover(1000, None) is None

    def test_sales_none(self):
        """None sales returns None."""
        assert asset_turnover(None, 500) is None

    def test_both_none(self):
        """Both None returns None."""
        assert asset_turnover(None, None) is None

    def test_float_inputs(self):
        """Float inputs work correctly."""
        result = asset_turnover(1000.0, 250.0)
        assert isclose(result, 4.0)
