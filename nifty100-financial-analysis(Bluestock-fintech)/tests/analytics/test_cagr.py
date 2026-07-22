"""
Tests for src/analytics/cagr.py — CAGR computations.

Covers normal calculation, zero growth, declining company, invalid inputs,
and all edge cases for each function.
"""

import sys
from pathlib import Path
from math import isclose

import pytest

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import the analytics module directly using importlib to avoid package conflicts
import importlib.util
cagr_path = Path(__file__).parents[2] / "src" / "analytics" / "cagr.py"
spec = importlib.util.spec_from_file_location("analytics.cagr", cagr_path)
analytics_cagr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_cagr)

calculate_cagr = analytics_cagr.calculate_cagr
cagr_direction = analytics_cagr.cagr_direction
is_high_growth = analytics_cagr.is_high_growth
is_negative_growth = analytics_cagr.is_negative_growth
cagr_grade = analytics_cagr.cagr_grade
growth_score = analytics_cagr.growth_score
is_multibagger_growth = analytics_cagr.is_multibagger_growth
growth_bucket = analytics_cagr.growth_bucket


# =========================================================================
# calculate_cagr
# =========================================================================


class TestCalculateCAGR:
    """Tests for calculate_cagr()."""

    def test_normal_calculation_growing(self):
        """Start 100, end 200, 5 years -> ~14.87%."""
        result = calculate_cagr(100, 200, 5)
        assert isclose(result, 14.869835499703506)

    def test_normal_calculation_multi_year_growth(self):
        """Start 1000, end 2000, 10 years -> 7.177%."""
        result = calculate_cagr(1000, 2000, 10)
        assert isclose(result, 7.177346253629313)

    def test_zero_growth(self):
        """Start 100, end 100, 10 years -> 0.0%."""
        result = calculate_cagr(100, 100, 10)
        assert isclose(result, 0.0)

    def test_declining_company(self):
        """Start 200, end 100, 4 years -> -15.91%."""
        result = calculate_cagr(200, 100, 4)
        assert isclose(result, -15.910358474627903)

    def test_start_value_zero(self):
        """Start value 0 returns None."""
        assert calculate_cagr(0, 100, 5) is None

    def test_start_value_negative(self):
        """Negative start value returns None."""
        assert calculate_cagr(-100, 200, 5) is None

    def test_end_value_negative(self):
        """Negative end value returns None."""
        assert calculate_cagr(100, -50, 5) is None

    def test_years_zero(self):
        """Years = 0 returns None."""
        assert calculate_cagr(100, 200, 0) is None

    def test_years_negative(self):
        """Negative years returns None."""
        assert calculate_cagr(100, 200, -5) is None

    def test_start_value_none(self):
        """None start value returns None."""
        assert calculate_cagr(None, 200, 5) is None

    def test_end_value_none(self):
        """None end value returns None."""
        assert calculate_cagr(100, None, 5) is None

    def test_years_none(self):
        """None years returns None."""
        assert calculate_cagr(100, 200, None) is None

    def test_all_none(self):
        """All None returns None."""
        assert calculate_cagr(None, None, None) is None

    def test_float_inputs(self):
        """Float inputs work correctly."""
        result = calculate_cagr(100.0, 200.0, 5.0)
        assert isclose(result, 14.869835499703506)

    def test_one_year_growth(self):
        """One year growth equals simple return % change."""
        result = calculate_cagr(100, 120, 1)
        assert isclose(result, 20.0)

    def test_fractional_years(self):
        """Fractional years work correctly."""
        result = calculate_cagr(100, 121, 2)  # 2 years, 10% CAGR -> 121
        assert isclose(result, 10.0)


# =========================================================================
# cagr_direction
# =========================================================================


class TestCAGRDirection:
    """Tests for cagr_direction()."""

    def test_growing(self):
        """Positive CAGR returns 'Growing'."""
        assert cagr_direction(15.5) == "Growing"
        assert cagr_direction(0.1) == "Growing"
        assert cagr_direction(20.0) == "Growing"
        assert cagr_direction(100.0) == "Growing"

    def test_flat(self):
        """Zero CAGR returns 'Flat'."""
        assert cagr_direction(0) == "Flat"
        assert cagr_direction(0.0) == "Flat"

    def test_declining(self):
        """Negative CAGR returns 'Declining'."""
        assert cagr_direction(-5.2) == "Declining"
        assert cagr_direction(-0.1) == "Declining"
        assert cagr_direction(-50.0) == "Declining"

    def test_none_returns_none(self):
        """None CAGR returns None."""
        assert cagr_direction(None) is None


# =========================================================================
# is_high_growth
# =========================================================================


class TestIsHighGrowth:
    """Tests for is_high_growth()."""

    def test_above_20(self):
        """CAGR > 20 returns True."""
        assert is_high_growth(25.0) is True
        assert is_high_growth(50.0) is True
        assert is_high_growth(100.0) is True

    def test_exactly_20(self):
        """CAGR exactly 20 returns True."""
        assert is_high_growth(20.0) is True
        assert is_high_growth(20) is True

    def test_below_20(self):
        """CAGR < 20 returns False."""
        assert is_high_growth(15.0) is False
        assert is_high_growth(0.0) is False
        assert is_high_growth(-5.0) is False

    def test_none_returns_false(self):
        """None CAGR returns False."""
        assert is_high_growth(None) is False


# =========================================================================
# is_negative_growth
# =========================================================================


class TestIsNegativeGrowth:
    """Tests for is_negative_growth()."""

    def test_positive(self):
        """Positive CAGR returns False."""
        assert is_negative_growth(5.0) is False
        assert is_negative_growth(0.1) is False
        assert is_negative_growth(20.0) is False

    def test_zero(self):
        """Zero CAGR returns False."""
        assert is_negative_growth(0.0) is False
        assert is_negative_growth(0) is False

    def test_negative(self):
        """Negative CAGR returns True."""
        assert is_negative_growth(-5.0) is True
        assert is_negative_growth(-0.1) is True
        assert is_negative_growth(-50.0) is True

    def test_none_returns_false(self):
        """None CAGR returns False."""
        assert is_negative_growth(None) is False


# =========================================================================
# cagr_grade
# =========================================================================


class TestCAGRGrade:
    """Tests for cagr_grade()."""

    def test_exceptional(self):
        """CAGR >= 30 returns 'Exceptional'."""
        assert cagr_grade(30.0) == "Exceptional"
        assert cagr_grade(35.0) == "Exceptional"
        assert cagr_grade(50.0) == "Exceptional"

    def test_high(self):
        """CAGR >= 20 and < 30 returns 'High'."""
        assert cagr_grade(20.0) == "High"
        assert cagr_grade(25.0) == "High"
        assert cagr_grade(29.999) == "High"

    def test_healthy(self):
        """CAGR >= 10 and < 20 returns 'Healthy'."""
        assert cagr_grade(10.0) == "Healthy"
        assert cagr_grade(15.0) == "Healthy"
        assert cagr_grade(19.999) == "Healthy"

    def test_stable(self):
        """CAGR >= 0 and < 10 returns 'Stable'."""
        assert cagr_grade(0.0) == "Stable"
        assert cagr_grade(5.0) == "Stable"
        assert cagr_grade(9.999) == "Stable"

    def test_negative(self):
        """CAGR < 0 returns 'Negative'."""
        assert cagr_grade(-0.1) == "Negative"
        assert cagr_grade(-5.0) == "Negative"
        assert cagr_grade(-50.0) == "Negative"

    def test_none_returns_none(self):
        """None CAGR returns None."""
        assert cagr_grade(None) is None


# =========================================================================
# growth_score
# =========================================================================


class TestGrowthScore:
    """Tests for growth_score()."""

    def test_none_returns_zero(self):
        """None CAGR returns 0."""
        assert growth_score(None) == 0

    def test_negative_returns_zero(self):
        """Negative CAGR returns 0."""
        assert growth_score(-0.1) == 0
        assert growth_score(-5.0) == 0
        assert growth_score(-20.0) == 0

    def test_zero_to_ten(self):
        """CAGR 0 to < 10 returns 1."""
        assert growth_score(0.0) == 1
        assert growth_score(5.0) == 1
        assert growth_score(9.999) == 1

    def test_ten_to_twenty(self):
        """CAGR 10 to < 20 returns 2."""
        assert growth_score(10.0) == 2
        assert growth_score(15.0) == 2
        assert growth_score(19.999) == 2

    def test_twenty_to_thirty(self):
        """CAGR 20 to < 30 returns 3."""
        assert growth_score(20.0) == 3
        assert growth_score(25.0) == 3
        assert growth_score(29.999) == 3

    def test_thirty_plus(self):
        """CAGR >= 30 returns 4."""
        assert growth_score(30.0) == 4
        assert growth_score(40.0) == 4
        assert growth_score(50.0) == 4


# =========================================================================
# is_multibagger_growth
# =========================================================================


class TestIsMultibaggerGrowth:
    """Tests for is_multibagger_growth()."""

    def test_above_25(self):
        """CAGR >= 25 returns True."""
        assert is_multibagger_growth(25.0) is True
        assert is_multibagger_growth(40.0) is True
        assert is_multibagger_growth(50.0) is True

    def test_below_25(self):
        """CAGR < 25 returns False."""
        assert is_multibagger_growth(24.9) is False
        assert is_multibagger_growth(20.0) is False
        assert is_multibagger_growth(0.0) is False
        assert is_multibagger_growth(-5.0) is False

    def test_none_returns_false(self):
        """None CAGR returns False."""
        assert is_multibagger_growth(None) is False


# =========================================================================
# growth_bucket
# =========================================================================


class TestGrowthBucket:
    """Tests for growth_bucket()."""

    def test_unknown(self):
        """None CAGR returns 'Unknown'."""
        assert growth_bucket(None) == "Unknown"

    def test_negative(self):
        """CAGR < 0 returns 'Negative'."""
        assert growth_bucket(-0.1) == "Negative"
        assert growth_bucket(-5.0) == "Negative"
        assert growth_bucket(-20.0) == "Negative"

    def test_slow(self):
        """CAGR 0 to < 10 returns 'Slow'."""
        assert growth_bucket(0.0) == "Slow"
        assert growth_bucket(5.0) == "Slow"
        assert growth_bucket(9.999) == "Slow"

    def test_moderate(self):
        """CAGR 10 to < 20 returns 'Moderate'."""
        assert growth_bucket(10.0) == "Moderate"
        assert growth_bucket(15.0) == "Moderate"
        assert growth_bucket(19.999) == "Moderate"

    def test_fast(self):
        """CAGR 20 to < 30 returns 'Fast'."""
        assert growth_bucket(20.0) == "Fast"
        assert growth_bucket(25.0) == "Fast"
        assert growth_bucket(29.999) == "Fast"

    def test_hyper_growth(self):
        """CAGR >= 30 returns 'Hyper Growth'."""
        assert growth_bucket(30.0) == "Hyper Growth"
        assert growth_bucket(40.0) == "Hyper Growth"
        assert growth_bucket(50.0) == "Hyper Growth"