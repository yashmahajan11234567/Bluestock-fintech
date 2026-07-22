"""
Financial Ratios Pipeline - computes all analytics from raw financial data.

Reuses existing functions from analytics modules to compute comprehensive
financial metrics. All functions are pure with no database, logging, or I/O.
"""

from typing import Any, Dict, Optional, Union

# Type alias for numeric values that may be None
Numeric = Union[float, int, None]

# Import all analytics functions using absolute imports via sys.path
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import using importlib to avoid relative import issues
import importlib.util

def _import_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

analytics_src = project_root / "src" / "analytics"

# Import ratios module
analytics_ratios = _import_module(
    "analytics.ratios",
    analytics_src / "ratios.py"
)

# Import cagr module
analytics_cagr = _import_module(
    "analytics.cagr",
    analytics_src / "cagr.py"
)

# Import cashflow module
analytics_cashflow = _import_module(
    "analytics.cashflow",
    analytics_src / "cashflow.py"
)

# Import capital_allocation module
analytics_capital_allocation = _import_module(
    "analytics.capital_allocation",
    analytics_src / "capital_allocation.py"
)

# Extract functions for direct use
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

calculate_cagr = analytics_cagr.calculate_cagr
cagr_grade = analytics_cagr.cagr_grade
growth_bucket = analytics_cagr.growth_bucket
growth_score = analytics_cagr.growth_score
is_high_growth = analytics_cagr.is_high_growth
is_negative_growth = analytics_cagr.is_negative_growth
is_multibagger_growth = analytics_cagr.is_multibagger_growth

operating_cashflow_ratio = analytics_cashflow.operating_cashflow_ratio
cash_conversion_ratio = analytics_cashflow.cash_conversion_ratio
free_cash_flow = analytics_cashflow.free_cash_flow
fcf_status = analytics_cashflow.fcf_status
cashflow_quality = analytics_cashflow.cashflow_quality

capital_allocation_category = analytics_capital_allocation.capital_allocation_category
capital_score = analytics_capital_allocation.capital_score
is_capital_efficient = analytics_capital_allocation.is_capital_efficient
needs_capital_review = analytics_capital_allocation.needs_capital_review


def calculate_financial_metrics(financial_data: Dict[str, Optional[Numeric]]) -> Dict[str, Any]:
    """
    Compute all supported financial analytics from raw financial data.

    This function orchestrates the analytics modules to produce a comprehensive
    set of financial metrics. It accepts a dictionary containing the raw
    financial statement values and returns a dictionary with all computed metrics.

    Args:
        financial_data: Dictionary containing raw financial values. Expected keys:
            Profitability inputs:
                - net_profit: Net profit for the period
                - sales: Total sales / revenue
                - operating_profit: Operating profit (EBIT)
                - equity_capital: Share capital / equity capital
                - reserves: Reserves and surplus
                - borrowings: Total borrowings (long-term debt)
                - total_assets: Total assets

            Leverage inputs:
                - interest_expense: Interest expense
                - other_income: Other income
                - investments: Total investments
                - broad_sector: Sector name (for high leverage flag)

            Growth inputs:
                - revenue_start: Starting revenue (for CAGR)
                - revenue_end: Ending revenue (for CAGR)
                - revenue_years: Number of years (for CAGR)

            Cash Flow inputs:
                - operating_cashflow: Operating cash flow
                - capital_expenditure: Capital expenditure
                - net_profit_cf: Net profit (for cash conversion ratio)

            Capital Allocation inputs (computed from above):
                - roe: Return on equity (computed)
                - roce: Return on capital employed (computed)
                - ccr: Cash conversion ratio (computed)

    Returns:
        Dictionary with all computed metrics organized by category:
        {
            "profitability": {...},
            "leverage": {...},
            "growth": {...},
            "cash_flow": {...},
            "capital_allocation": {...}
        }

    Example:
        >>> data = {
        ...     "net_profit": 200,
        ...     "sales": 1000,
        ...     "operating_profit": 250,
        ...     "equity_capital": 100,
        ...     "reserves": 200,
        ...     "borrowings": 50,
        ...     "total_assets": 1000,
        ...     "interest_expense": 30,
        ...     "other_income": 20,
        ...     "investments": 150,
        ...     "revenue_start": 500,
        ...     "revenue_end": 1000,
        ...     "revenue_years": 5,
        ...     "operating_cashflow": 300,
        ...     "capital_expenditure": 100,
        ...     "net_profit_cf": 200,
        ... }
        >>> result = calculate_financial_metrics(data)
        >>> result["profitability"]["net_profit_margin"]
        20.0
    """
    # Extract inputs with safe defaults
    def get(key: str, default=None):
        return financial_data.get(key, default)

    # ============================================================
    # PROFITABILITY
    # ============================================================
    net_profit = get("net_profit")
    sales = get("sales")
    operating_profit = get("operating_profit")
    other_income = get("other_income")
    equity_capital = get("equity_capital")
    reserves = get("reserves")
    borrowings = get("borrowings")
    total_assets = get("total_assets")

    np_margin = net_profit_margin(net_profit, sales)
    op_margin = operating_profit_margin(operating_profit, sales)
    roe = return_on_equity(net_profit, equity_capital, reserves)
    roce = return_on_capital_employed(
        operating_profit + (other_income or 0) if operating_profit is not None else None,
        equity_capital, reserves, borrowings
    )
    roa = return_on_assets(net_profit, total_assets)

    # ============================================================
    # LEVERAGE
    # ============================================================
    interest_expense = get("interest")
    investments = get("investments")
    broad_sector = get("broad_sector")

    dte = debt_to_equity(borrowings, equity_capital, reserves)
    icr = interest_coverage_ratio(operating_profit, other_income, interest_expense)
    icr_label = interest_coverage_label(interest_expense)
    icr_warning = interest_coverage_warning(icr)
    high_lev_flag = high_leverage_flag(dte, broad_sector)
    nd = net_debt(borrowings, investments)
    at = asset_turnover(sales, total_assets)

    # ============================================================
    # GROWTH
    # ============================================================
    revenue_start = get("revenue_start")
    revenue_end = get("revenue_end")
    revenue_years = get("revenue_years")

    revenue_cagr = calculate_cagr(revenue_start, revenue_end, revenue_years)
    cagr_grd = cagr_grade(revenue_cagr)
    grwth_bkt = growth_bucket(revenue_cagr)
    grwth_scr = growth_score(revenue_cagr)
    hi_gr = is_high_growth(revenue_cagr)
    neg_gr = is_negative_growth(revenue_cagr)
    mb_gr = is_multibagger_growth(revenue_cagr)

    # ============================================================
    # CASH FLOW
    # ============================================================
    operating_cashflow = get("operating_cashflow")
    capital_expenditure = get("capital_expenditure")
    net_profit_cf = get("net_profit")

    ocf_ratio = operating_cashflow_ratio(operating_cashflow, sales)
    ccr = cash_conversion_ratio(operating_cashflow, net_profit_cf)
    fcf = free_cash_flow(operating_cashflow, capital_expenditure)
    fcf_stat = fcf_status(fcf)
    cf_quality = cashflow_quality(ccr)

    # ============================================================
    # CAPITAL ALLOCATION
    # ============================================================
    # Uses computed roe, roce, ccr from above
    ca_category = capital_allocation_category(roe, roce, ccr)
    ca_score = capital_score(ca_category)
    ca_eff = is_capital_efficient(ca_category)
    ca_review = needs_capital_review(ca_category)

    # ============================================================
    # ASSEMBLE RESULT
    # ============================================================
    return {
        "profitability": {
            "net_profit_margin": np_margin,
            "operating_profit_margin": op_margin,
            "roe": roe,
            "roce": roce,
            "roa": roa,
        },
        "leverage": {
            "debt_to_equity": dte,
            "interest_coverage_ratio": icr,
            "interest_coverage_label": icr_label,
            "interest_coverage_warning": icr_warning,
            "high_leverage_flag": high_lev_flag,
            "net_debt": nd,
            "asset_turnover": at,
        },
        "growth": {
            "revenue_cagr": revenue_cagr,
            "cagr_grade": cagr_grd,
            "growth_bucket": grwth_bkt,
            "growth_score": grwth_scr,
            "is_high_growth": hi_gr,
            "is_negative_growth": neg_gr,
            "is_multibagger_growth": mb_gr,
        },
        "cash_flow": {
            "operating_cashflow_ratio": ocf_ratio,
            "cash_conversion_ratio": ccr,
            "free_cash_flow": fcf,
            "fcf_status": fcf_stat,
            "cashflow_quality": cf_quality,
        },
        "capital_allocation": {
            "capital_allocation_category": ca_category,
            "capital_score": ca_score,
            "is_capital_efficient": ca_eff,
            "needs_capital_review": ca_review,
        },
    }