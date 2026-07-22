"""
Profitability ratio computations for financial analysis.

All functions are pure â€” they accept numeric inputs and return computed
ratios as floats or None.  No database access, logging, or file I/O.
"""

from typing import Optional, Union

# Type alias for numeric values that may be None
Numeric = Union[float, int, None]


def net_profit_margin(
    net_profit: Numeric,
    sales: Numeric,
) -> Optional[float]:
    """
    Compute net profit margin as a percentage.

    Formula:
        (net_profit / sales) * 100

    Args:
        net_profit: Net profit (or loss) for the period.
        sales: Total sales / revenue for the period.

    Returns:
        Net profit margin as a float percentage, or None if sales is
        zero, None, or otherwise invalid.

    Example:
        >>> net_profit_margin(200, 1000)
        20.0
        >>> net_profit_margin(50, 0)
        None
    """
    if sales is None or sales == 0:
        return None
    if net_profit is None:
        return None
    return (net_profit / sales) * 100.0


def operating_profit_margin(
    operating_profit: Numeric,
    sales: Numeric,
) -> Optional[float]:
    """
    Compute operating profit margin as a percentage.

    Formula:
        (operating_profit / sales) * 100

    Args:
        operating_profit: Operating profit (EBIT) for the period.
        sales: Total sales / revenue for the period.

    Returns:
        Operating profit margin as a float percentage, or None if sales
        is zero or None.

    Example:
        >>> operating_profit_margin(200, 1000)
        20.0
        >>> operating_profit_margin(0, 1000)
        0.0
        >>> operating_profit_margin(100, 0)
        None
    """
    if sales is None or sales == 0:
        return None
    if operating_profit is None:
        return None
    return (operating_profit / sales) * 100.0


def return_on_equity(
    net_profit: Numeric,
    equity_capital: Numeric,
    reserves: Numeric,
) -> Optional[float]:
    """
    Compute return on equity (ROE) as a percentage.

    Formula:
        net_profit / (equity_capital + reserves) * 100

    Args:
        net_profit: Net profit (or loss) for the period.
        equity_capital: Share capital / equity capital.
        reserves: Reserves and surplus.

    Returns:
        ROE as a float percentage, or None if total equity
        (equity_capital + reserves) is <= 0 or any input is None.

    Example:
        >>> return_on_equity(200, 100, 200)
        66.66666666666666
        >>> return_on_equity(200, 0, 0)
        None
        >>> return_on_equity(200, 100, -200)
        None
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None
    return (net_profit / total_equity) * 100.0


def return_on_capital_employed(
    ebit: Numeric,
    equity_capital: Numeric,
    reserves: Numeric,
    borrowings: Numeric,
) -> Optional[float]:
    """
    Compute return on capital employed (ROCE) as a percentage.

    Formula:
        ebit / (equity_capital + reserves + borrowings) * 100

    Args:
        ebit: Earnings before interest and taxes.
        equity_capital: Share capital / equity capital.
        reserves: Reserves and surplus.
        borrowings: Total borrowings (long-term debt).

    Returns:
        ROCE as a float percentage, or None if capital employed
        (equity_capital + reserves + borrowings) is <= 0 or any input
        is None.

    Example:
        >>> return_on_capital_employed(300, 100, 200, 50)
        85.71428571428571
        >>> return_on_capital_employed(300, 0, 0, 0)
        None
        >>> return_on_capital_employed(300, 100, 200, -350)
        None
    """
    if any(x is None for x in (ebit, equity_capital, reserves, borrowings)):
        return None
    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None
    return (ebit / capital_employed) * 100.0


def return_on_assets(
    net_profit: Numeric,
    total_assets: Numeric,
) -> Optional[float]:
    """
    Compute return on assets (ROA) as a percentage.

    Formula:
        (net_profit / total_assets) * 100

    Args:
        net_profit: Net profit (or loss) for the period.
        total_assets: Total assets for the period.

    Returns:
        ROA as a float percentage, or None if total_assets is zero,
        None, or otherwise invalid.

    Example:
        >>> return_on_assets(200, 1000)
        20.0
        >>> return_on_assets(200, 0)
        None
    """
    if total_assets is None or total_assets == 0:
        return None
    if net_profit is None:
        return None
    return (net_profit / total_assets) * 100.0


def debt_to_equity(
    borrowings: Numeric,
    equity_capital: Numeric,
    reserves: Numeric,
) -> Optional[float]:
    """
    Compute debt-to-equity ratio.

    Formula:
        borrowings / (equity_capital + reserves)

    Args:
        borrowings: Total borrowings (long-term debt).
        equity_capital: Share capital / equity capital.
        reserves: Reserves and surplus.

    Returns:
        Debt-to-equity ratio as a float, or None if denominator is <= 0
        or any input is None. Returns 0.0 if borrowings is 0.

    Example:
        >>> debt_to_equity(100, 200, 300)
        0.2
        >>> debt_to_equity(0, 100, 200)
        0.0
        >>> debt_to_equity(100, 0, 0)
        None
    """
    if borrowings is None or equity_capital is None or reserves is None:
        return None
    if borrowings == 0:
        return 0.0
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None
    return borrowings / total_equity


def interest_coverage_ratio(
    operating_profit: Numeric,
    other_income: Numeric,
    interest: Numeric,
) -> Optional[float]:
    """
    Compute interest coverage ratio.

    Formula:
        (operating_profit + other_income) / interest

    Args:
        operating_profit: Operating profit (EBIT) for the period.
        other_income: Other income for the period.
        interest: Interest expense for the period.

    Returns:
        Interest coverage ratio as a float, or None if interest is
        zero or None. Negative operating profit and other income are allowed.

    Example:
        >>> interest_coverage_ratio(200, 50, 50)
        5.0
        >>> interest_coverage_ratio(-100, 200, 50)
        2.0
        >>> interest_coverage_ratio(200, -50, 50)
        3.0
        >>> interest_coverage_ratio(200, 50, 0)
        None
    """
    if interest is None or interest == 0:
        return None
    if operating_profit is None:
        return None
    if other_income is None:
        return None
    return (operating_profit + other_income) / interest


def interest_coverage_label(
    interest: Numeric,
) -> Optional[str]:
    """
    Return a label indicating whether the company is debt-free.

    Args:
        interest: Interest expense for the period.

    Returns:
        "Debt Free" if interest is zero or None, otherwise None.

    Example:
        >>> interest_coverage_label(0)
        'Debt Free'
        >>> interest_coverage_label(None)
        'Debt Free'
        >>> interest_coverage_label(50)
        None
    """
    if interest is None or interest == 0:
        return "Debt Free"
    return None


def interest_coverage_warning(
    icr: Numeric,
) -> bool:
    """
    Check if interest coverage ratio indicates potential risk.

    Args:
        icr: Interest coverage ratio value.

    Returns:
        True if ICR is below 1.5 (warning threshold), False if 1.5 or above,
        or if icr is None.

    Example:
        >>> interest_coverage_warning(1.0)
        True
        >>> interest_coverage_warning(1.5)
        False
        >>> interest_coverage_warning(2.0)
        False
        >>> interest_coverage_warning(None)
        False
    """
    if icr is None:
        return False
    return icr < 1.5


def high_leverage_flag(
    debt_to_equity: Numeric,
    broad_sector: Numeric,
) -> bool:
    """
    Flag non-financial companies with excessive leverage.

    Financials sector is exempt from this flag.

    Args:
        debt_to_equity: Debt-to-equity ratio.
        broad_sector: Sector classification string.

    Returns:
        True if D/E > 5 and sector does not start with "financial" (case-insensitive),
        otherwise False.

    Example:
        >>> high_leverage_flag(6.0, "Technology")
        True
        >>> high_leverage_flag(6.0, "Financials")
        False
        >>> high_leverage_flag(3.0, "Technology")
        False
    """
    if broad_sector is None:
        return False
    if debt_to_equity is None:
        return False
    if debt_to_equity > 5 and not broad_sector.strip().lower().startswith("financial"):
        return True
    return False


def net_debt(
    borrowings: Numeric,
    investments: Numeric,
) -> Optional[float]:
    """
    Compute net debt.

    Formula:
        borrowings - investments

    Args:
        borrowings: Total borrowings.
        investments: Total investments (including cash equivalents).

    Returns:
        Net debt as a float, or None if either input is None.
        Negative values are allowed (negative net debt = net cash position).

    Example:
        >>> net_debt(1000, 200)
        800.0
        >>> net_debt(200, 1000)
        -800.0
        >>> net_debt(1000, None)
        None
    """
    if borrowings is None or investments is None:
        return None
    return borrowings - investments


def asset_turnover(
    sales: Numeric,
    total_assets: Numeric,
) -> Optional[float]:
    """
    Compute asset turnover ratio.

    Formula:
        sales / total_assets

    Args:
        sales: Total sales / revenue for the period.
        total_assets: Total assets for the period.

    Returns:
        Asset turnover ratio as a float, or None if total_assets is
        <= 0 or None. None inputs return None.

    Example:
        >>> asset_turnover(1000, 500)
        2.0
        >>> asset_turnover(1000, 0)
        None
        >>> asset_turnover(1000, None)
        None
    """
    if total_assets is None or total_assets <= 0:
        return None
    if sales is None:
        return None
    return sales / total_assets


