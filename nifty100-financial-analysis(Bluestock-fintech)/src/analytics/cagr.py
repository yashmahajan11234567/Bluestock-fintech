"""
Compound Annual Growth Rate (CAGR) computations for financial analysis.

All functions are pure — they accept numeric inputs and return computed
results as floats, booleans, strings, or None. No database access,
logging, or file I/O.
"""

from typing import Optional, Union

# Type alias for numeric values that may be None
Numeric = Union[float, int, None]


def calculate_cagr(
    start_value: Numeric,
    end_value: Numeric,
    years: Numeric,
) -> Optional[float]:
    """
    Compute Compound Annual Growth Rate (CAGR) as a percentage.

    Formula:
        ((end_value / start_value) ** (1 / years) - 1) * 100

    Args:
        start_value: Starting value (must be > 0).
        end_value: Ending value (must be >= 0; negative returns None).
        years: Number of years (must be > 0).

    Returns:
        CAGR as a float percentage, or None if any input is invalid:
        - start_value is None, <= 0
        - end_value is None, < 0
        - years is None, <= 0

    Example:
        >>> calculate_cagr(100, 200, 5)
        14.869835499703506
        >>> calculate_cagr(100, 100, 10)
        0.0
        >>> calculate_cagr(200, 100, 4)
        -15.910358474627903
        >>> calculate_cagr(0, 100, 5)
        None
        >>> calculate_cagr(100, -50, 5)
        None
        >>> calculate_cagr(100, 200, 0)
        None
    """
    if start_value is None or start_value <= 0:
        return None
    if end_value is None or end_value < 0:
        return None
    if years is None or years <= 0:
        return None

    return ((end_value / start_value) ** (1 / years) - 1) * 100.0


def cagr_direction(cagr: Numeric) -> Optional[str]:
    """
    Return a label indicating the growth direction based on CAGR.

    Args:
        cagr: Compound Annual Growth Rate as a percentage (can be None).

    Returns:
        "Growing" if cagr > 0
        "Flat" if cagr == 0
        "Declining" if cagr < 0
        None if cagr is None

    Example:
        >>> cagr_direction(15.5)
        'Growing'
        >>> cagr_direction(0.0)
        'Flat'
        >>> cagr_direction(-5.2)
        'Declining'
        >>> cagr_direction(None)
        None
    """
    if cagr is None:
        return None
    if cagr > 0:
        return "Growing"
    if cagr == 0:
        return "Flat"
    return "Declining"


def is_high_growth(cagr: Numeric) -> bool:
    """
    Check if CAGR indicates high growth (>= 20%).

    Args:
        cagr: Compound Annual Growth Rate as a percentage (can be None).

    Returns:
        True if cagr >= 20, False otherwise (including None).

    Example:
        >>> is_high_growth(25.0)
        True
        >>> is_high_growth(20.0)
        True
        >>> is_high_growth(15.0)
        False
        >>> is_high_growth(0.0)
        False
        >>> is_high_growth(-5.0)
        False
        >>> is_high_growth(None)
        False
    """
    if cagr is None:
        return False
    return cagr >= 20.0


def is_negative_growth(cagr: Numeric) -> bool:
    """
    Check if CAGR indicates negative growth (< 0%).

    Args:
        cagr: Compound Annual Growth Rate as a percentage (can be None).

    Returns:
        True if cagr < 0, False otherwise (including None).

    Example:
        >>> is_negative_growth(-5.0)
        True
        >>> is_negative_growth(-0.1)
        True
        >>> is_negative_growth(0.0)
        False
        >>> is_negative_growth(5.0)
        False
        >>> is_negative_growth(None)
        False
    """
    if cagr is None:
        return False
    return cagr < 0.0


def cagr_grade(cagr: Numeric) -> Optional[str]:
    """
    Return a grade label for the CAGR based on performance tiers.

    Args:
        cagr: Compound Annual Growth Rate as a percentage (can be None).

    Returns:
        "Exceptional" if cagr >= 30
        "High" if cagr >= 20
        "Healthy" if cagr >= 10
        "Stable" if cagr >= 0
        "Negative" if cagr < 0
        None if cagr is None

    Example:
        >>> cagr_grade(35.0)
        'Exceptional'
        >>> cagr_grade(25.0)
        'High'
        >>> cagr_grade(15.0)
        'Healthy'
        >>> cagr_grade(5.0)
        'Stable'
        >>> cagr_grade(-2.0)
        'Negative'
        >>> cagr_grade(None)
        None
    """
    if cagr is None:
        return None
    if cagr >= 30:
        return "Exceptional"
    if cagr >= 20:
        return "High"
    if cagr >= 10:
        return "Healthy"
    if cagr >= 0:
        return "Stable"
    return "Negative"


def growth_score(cagr: Numeric) -> int:
    """
    Return a discrete growth score (0-4) based on CAGR bands.

    Args:
        cagr: Compound Annual Growth Rate as a percentage (can be None).

    Returns:
        0 if cagr is None or cagr < 0
        1 if 0 <= cagr < 10
        2 if 10 <= cagr < 20
        3 if 20 <= cagr < 30
        4 if cagr >= 30

    Example:
        >>> growth_score(None)
        0
        >>> growth_score(-5.0)
        0
        >>> growth_score(5.0)
        1
        >>> growth_score(10.0)
        2
        >>> growth_score(15.0)
        2
        >>> growth_score(20.0)
        3
        >>> growth_score(25.0)
        3
        >>> growth_score(30.0)
        4
        >>> growth_score(40.0)
        4
    """
    if cagr is None or cagr < 0:
        return 0
    if cagr < 10:
        return 1
    if cagr < 20:
        return 2
    if cagr < 30:
        return 3
    return 4


def is_multibagger_growth(cagr: Numeric) -> bool:
    """
    Check if CAGR indicates multibagger potential (>= 25%).

    Args:
        cagr: Compound Annual Growth Rate as a percentage (can be None).

    Returns:
        True if cagr >= 25, False otherwise (including None).

    Example:
        >>> is_multibagger_growth(24.9)
        False
        >>> is_multibagger_growth(25.0)
        True
        >>> is_multibagger_growth(40.0)
        True
        >>> is_multibagger_growth(None)
        False
    """
    if cagr is None:
        return False
    return cagr >= 25.0


def growth_bucket(cagr: Numeric) -> str:
    """
    Return a bucket label for the CAGR based on growth speed categories.

    Args:
        cagr: Compound Annual Growth Rate as a percentage (can be None).

    Returns:
        "Unknown" if cagr is None
        "Negative" if cagr < 0
        "Slow" if 0 <= cagr < 10
        "Moderate" if 10 <= cagr < 20
        "Fast" if 20 <= cagr < 30
        "Hyper Growth" if cagr >= 30

    Example:
        >>> growth_bucket(None)
        'Unknown'
        >>> growth_bucket(-5.0)
        'Negative'
        >>> growth_bucket(5.0)
        'Slow'
        >>> growth_bucket(10.0)
        'Moderate'
        >>> growth_bucket(15.0)
        'Moderate'
        >>> growth_bucket(20.0)
        'Fast'
        >>> growth_bucket(25.0)
        'Fast'
        >>> growth_bucket(30.0)
        'Hyper Growth'
        >>> growth_bucket(40.0)
        'Hyper Growth'
    """
    if cagr is None:
        return "Unknown"
    if cagr < 0:
        return "Negative"
    if cagr < 10:
        return "Slow"
    if cagr < 20:
        return "Moderate"
    if cagr < 30:
        return "Fast"
    return "Hyper Growth"