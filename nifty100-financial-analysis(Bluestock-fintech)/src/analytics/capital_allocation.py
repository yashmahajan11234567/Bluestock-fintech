"""
Capital Allocation Classification for financial analysis.

All functions are pure — they accept numeric inputs and return computed
results as strings, integers, booleans, or None. No database access,
logging, or file I/O.
"""

from typing import Optional, Union

# Type alias for numeric values that may be None
Numeric = Union[float, int, None]


def capital_allocation_category(
    roe: Numeric,
    roce: Numeric,
    cash_conversion_ratio: Numeric,
) -> Optional[str]:
    """
    Classify capital allocation quality based on ROE, ROCE, and Cash Conversion Ratio.

    Classification Rules:
        Excellent: ROE >= 20, ROCE >= 20, CCR >= 1.2
        Good:    ROE >= 15, ROCE >= 15, CCR >= 1.0
        Average: ROE >= 10, ROCE >= 10, CCR >= 0.8
        Weak:    ROE >= 5,  ROCE >= 5
        Poor:    Otherwise
        None:    If any input is None

    Args:
        roe: Return on Equity as a percentage.
        roce: Return on Capital Employed as a percentage.
        cash_conversion_ratio: Cash Conversion Ratio (unitless).

    Returns:
        Category string: "Excellent", "Good", "Average", "Weak", "Poor", or None.

    Example:
        >>> capital_allocation_category(25, 25, 1.5)
        'Excellent'
        >>> capital_allocation_category(18, 18, 1.1)
        'Good'
        >>> capital_allocation_category(12, 12, 0.9)
        'Average'
        >>> capital_allocation_category(8, 8, 0.5)
        'Weak'
        >>> capital_allocation_category(3, 3, 0.5)
        'Poor'
        >>> capital_allocation_category(None, 20, 1.2)
        None
    """
    if roe is None or roce is None or cash_conversion_ratio is None:
        return None

    if roe >= 20 and roce >= 20 and cash_conversion_ratio >= 1.2:
        return "Excellent"

    if roe >= 15 and roce >= 15 and cash_conversion_ratio >= 1.0:
        return "Good"

    if roe >= 10 and roce >= 10 and cash_conversion_ratio >= 0.8:
        return "Average"

    if roe >= 5 and roce >= 5:
        return "Weak"

    return "Poor"


def capital_score(category: Optional[str]) -> int:
    """
    Return a numeric score for the capital allocation category.

    Rules:
        Excellent -> 5
        Good -> 4
        Average -> 3
        Weak -> 2
        Poor -> 1
        None -> 0

    Args:
        category: Capital allocation category string or None.

    Returns:
        Integer score from 0 to 5.

    Example:
        >>> capital_score("Excellent")
        5
        >>> capital_score("Good")
        4
        >>> capital_score("Average")
        3
        >>> capital_score("Weak")
        2
        >>> capital_score("Poor")
        1
        >>> capital_score(None)
        0
    """
    if category is None:
        return 0

    scores = {
        "Excellent": 5,
        "Good": 4,
        "Average": 3,
        "Weak": 2,
        "Poor": 1,
    }
    return scores.get(category, 0)


def is_capital_efficient(category: Optional[str]) -> bool:
    """
    Check if capital allocation is efficient (Excellent or Good).

    Rules:
        Excellent -> True
        Good -> True
        Average -> False
        Weak -> False
        Poor -> False
        None -> False

    Args:
        category: Capital allocation category string or None.

    Returns:
        True if category is "Excellent" or "Good", False otherwise.

    Example:
        >>> is_capital_efficient("Excellent")
        True
        >>> is_capital_efficient("Good")
        True
        >>> is_capital_efficient("Average")
        False
        >>> is_capital_efficient("Weak")
        False
        >>> is_capital_efficient("Poor")
        False
        >>> is_capital_efficient(None)
        False
    """
    return category in ("Excellent", "Good")


def needs_capital_review(category: Optional[str]) -> bool:
    """
    Check if capital allocation needs review (Weak or Poor).

    Rules:
        Weak -> True
        Poor -> True
        Excellent -> False
        Good -> False
        Average -> False
        None -> False

    Args:
        category: Capital allocation category string or None.

    Returns:
        True if category is "Weak" or "Poor", False otherwise.

    Example:
        >>> needs_capital_review("Weak")
        True
        >>> needs_capital_review("Poor")
        True
        >>> needs_capital_review("Excellent")
        False
        >>> needs_capital_review("Good")
        False
        >>> needs_capital_review("Average")
        False
        >>> needs_capital_review(None)
        False
    """
    return category in ("Weak", "Poor")