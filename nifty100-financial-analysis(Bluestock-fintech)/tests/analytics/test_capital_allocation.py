"""
Tests for src/analytics/capital_allocation.py — Capital Allocation Classification.

Covers normal calculations, edge cases, None inputs, and boundary conditions
for capital allocation classification functions.
"""

import sys
from pathlib import Path

import pytest

# Ensure src/ is on the path so imports work
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import the analytics module directly using importlib to avoid package conflicts
import importlib.util
capital_allocation_path = Path(__file__).parents[2] / "src" / "analytics" / "capital_allocation.py"
spec = importlib.util.spec_from_file_location("analytics.capital_allocation", capital_allocation_path)
analytics_capital_allocation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_capital_allocation)

capital_allocation_category = analytics_capital_allocation.capital_allocation_category
capital_score = analytics_capital_allocation.capital_score
is_capital_efficient = analytics_capital_allocation.is_capital_efficient
needs_capital_review = analytics_capital_allocation.needs_capital_review


# =========================================================================
# capital_allocation_category
# =========================================================================


class TestCapitalAllocationCategory:
    """Tests for capital_allocation_category()."""

    def test_excellent(self):
        """ROE >=20, ROCE >=20, CCR >=1.2 -> Excellent."""
        assert capital_allocation_category(25, 25, 1.5) == "Excellent"
        assert capital_allocation_category(20, 20, 1.2) == "Excellent"  # boundary
        assert capital_allocation_category(30, 30, 2.0) == "Excellent"

    def test_good(self):
        """ROE >=15, ROCE >=15, CCR >=1.0 -> Good."""
        assert capital_allocation_category(18, 18, 1.1) == "Good"
        assert capital_allocation_category(15, 15, 1.0) == "Good"  # boundary
        assert capital_allocation_category(22, 22, 1.1) == "Good"  # ROE/ROCE >=20 but CCR <1.2

    def test_average(self):
        """ROE >=10, ROCE >=10, CCR >=0.8 -> Average."""
        assert capital_allocation_category(12, 12, 0.9) == "Average"
        assert capital_allocation_category(10, 10, 0.8) == "Average"  # boundary
        assert capital_allocation_category(18, 18, 0.9) == "Average"  # ROE/ROCE >=15 but CCR <1.0

    def test_weak(self):
        """ROE >=5, ROCE >=5 -> Weak."""
        assert capital_allocation_category(8, 8, 0.5) == "Weak"
        assert capital_allocation_category(5, 5, 0.5) == "Weak"  # boundary
        assert capital_allocation_category(12, 12, 0.6) == "Weak"  # ROE/ROCE >=10 but CCR <0.8

    def test_poor(self):
        """ROE <5 or ROCE <5 -> Poor."""
        assert capital_allocation_category(3, 8, 0.5) == "Poor"  # ROE <5
        assert capital_allocation_category(8, 3, 0.5) == "Poor"  # ROCE <5
        assert capital_allocation_category(3, 3, 0.5) == "Poor"  # both <5
        assert capital_allocation_category(0, 0, 0.5) == "Poor"  # zero

    def test_none_returns_none(self):
        """None inputs return None."""
        assert capital_allocation_category(None, 20, 1.2) is None
        assert capital_allocation_category(20, None, 1.2) is None
        assert capital_allocation_category(20, 20, None) is None
        assert capital_allocation_category(None, None, None) is None


# =========================================================================
# capital_score
# =========================================================================


class TestCapitalScore:
    """Tests for capital_score()."""

    def test_excellent(self):
        """Excellent -> 5."""
        assert capital_score("Excellent") == 5

    def test_good(self):
        """Good -> 4."""
        assert capital_score("Good") == 4

    def test_average(self):
        """Average -> 3."""
        assert capital_score("Average") == 3

    def test_weak(self):
        """Weak -> 2."""
        assert capital_score("Weak") == 2

    def test_poor(self):
        """Poor -> 1."""
        assert capital_score("Poor") == 1

    def test_none_returns_zero(self):
        """None category returns 0."""
        assert capital_score(None) == 0


# =========================================================================
# is_capital_efficient
# =========================================================================


class TestIsCapitalEfficient:
    """Tests for is_capital_efficient()."""

    def test_excellent_true(self):
        """Excellent returns True."""
        assert is_capital_efficient("Excellent") is True

    def test_good_true(self):
        """Good returns True."""
        assert is_capital_efficient("Good") is True

    def test_average_false(self):
        """Average returns False."""
        assert is_capital_efficient("Average") is False

    def test_weak_false(self):
        """Weak returns False."""
        assert is_capital_efficient("Weak") is False

    def test_poor_false(self):
        """Poor returns False."""
        assert is_capital_efficient("Poor") is False

    def test_none_false(self):
        """None returns False."""
        assert is_capital_efficient(None) is False


# =========================================================================
# needs_capital_review
# =========================================================================


class TestNeedsCapitalReview:
    """Tests for needs_capital_review()."""

    def test_weak_true(self):
        """Weak returns True."""
        assert needs_capital_review("Weak") is True

    def test_poor_true(self):
        """Poor returns True."""
        assert needs_capital_review("Poor") is True

    def test_excellent_false(self):
        """Excellent returns False."""
        assert needs_capital_review("Excellent") is False

    def test_good_false(self):
        """Good returns False."""
        assert needs_capital_review("Good") is False

    def test_average_false(self):
        """Average returns False."""
        assert needs_capital_review("Average") is False

    def test_none_false(self):
        """None returns False."""
        assert needs_capital_review(None) is False