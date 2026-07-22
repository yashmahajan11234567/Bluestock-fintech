"""
Cash Flow KPI computations for financial analysis.

All functions are pure — they accept numeric inputs and return computed
results as floats, strings, or None. No database access, logging,
or file I/O.
"""

from typing import Optional, Union

# Type alias for numeric values that may be None
Numeric = Union[float, int, None]


def operating_cashflow_ratio(
    operating_cashflow: Numeric,
    sales: Numeric,
) -> Optional[float]:
    """
    Compute operating cash flow ratio.

    Formula:
        operating_cashflow / sales

    Args:
        operating_cashflow: Operating cash flow for the period.
        sales: Total sales / revenue for the period.

    Returns:
        Operating cash flow ratio as a float, or None if sales is None,
        zero, negative, or if operating_cashflow is None.

    Example:
        >>> operating_cashflow_ratio(200, 1000)
        0.2
        >>> operating_cashflow_ratio(200, 0)
        None
        >>> operating_cashflow_ratio(200, -100)
        None
        >>> operating_cashflow_ratio(None, 1000)
        None
    """
    if operating_cashflow is None:
        return None
    if sales is None or sales <= 0:
        return None
    return operating_cashflow / sales


def cash_conversion_ratio(
    operating_cashflow: Numeric,
    net_profit: Numeric,
) -> Optional[float]:
    """
    Compute cash conversion ratio.

    Formula:
        operating_cashflow / net_profit

    Args:
        operating_cashflow: Operating cash flow for the period.
        net_profit: Net profit for the period.

    Returns:
        Cash conversion ratio as a float, or None if net_profit is None
        or zero, or if operating_cashflow is None. Negative values allowed.

    Example:
        >>> cash_conversion_ratio(200, 100)
        2.0
        >>> cash_conversion_ratio(-50, 100)
        -0.5
        >>> cash_conversion_ratio(200, -100)
        -2.0
        >>> cash_conversion_ratio(200, 0)
        None
        >>> cash_conversion_ratio(None, 100)
        None
    """
    if operating_cashflow is None:
        return None
    if net_profit is None or net_profit == 0:
        return None
    return operating_cashflow / net_profit


def free_cash_flow(
    operating_cashflow: Numeric,
    capital_expenditure: Numeric,
) -> Optional[float]:
    """
    Compute free cash flow.

    Formula:
        operating_cashflow - capital_expenditure

    Args:
        operating_cashflow: Operating cash flow for the period.
        capital_expenditure: Capital expenditure for the period.

    Returns:
        Free cash flow as a float, or None if either input is None.
        Negative values allowed.

    Example:
        >>> free_cash_flow(500, 200)
        300.0
        >>> free_cash_flow(200, 200)
        0.0
        >>> free_cash_flow(100, 300)
        -200.0
        >>> free_cash_flow(None, 200)
        None
        >>> free_cash_flow(500, None)
        None
    """
    if operating_cashflow is None or capital_expenditure is None:
        return None
    return operating_cashflow - capital_expenditure


def fcf_status(fcf: Numeric) -> Optional[str]:
    """
    Return a label indicating the free cash flow status.

    Args:
        fcf: Free cash flow value (can be None).

    Returns:
        "Positive" if fcf > 0
        "Neutral" if fcf == 0
        "Negative" if fcf < 0
        None if fcf is None

    Example:
        >>> fcf_status(100.0)
        'Positive'
        >>> fcf_status(0.0)
        'Neutral'
        >>> fcf_status(-50.0)
        'Negative'
        >>> fcf_status(None)
        None
    """
    if fcf is None:
        return None
    if fcf > 0:
        return "Positive"
    if fcf == 0:
        return "Neutral"
    return "Negative"


def cashflow_quality(ccr: Numeric) -> Optional[str]:
    """
    Return a quality label based on cash conversion ratio.

    Args:
        ccr: Cash conversion ratio (can be None).

    Returns:
        "Excellent" if ccr >= 1.2
        "Good" if 1.0 <= ccr < 1.2
        "Average" if 0.8 <= ccr < 1.0
        "Weak" if ccr < 0.8
        None if ccr is None

    Example:
        >>> cashflow_quality(1.5)
        'Excellent'
        >>> cashflow_quality(1.1)
        'Good'
        >>> cashflow_quality(0.9)
        'Average'
        >>> cashflow_quality(0.5)
        'Weak'
        >>> cashflow_quality(None)
        None
        >>> cashflow_quality(-0.5)
        'Weak'
    """
    if ccr is None:
        return None
    if ccr >= 1.2:
        return "Excellent"
    if ccr >= 1.0:
        return "Good"
    if ccr >= 0.8:
        return "Average"
    return "Weak"