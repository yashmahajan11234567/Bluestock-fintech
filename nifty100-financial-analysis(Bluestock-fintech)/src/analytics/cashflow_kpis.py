"""
Cash Flow Intelligence — Day 31 KPI computations.

Computes 7 cash-flow intelligence KPIs for each company and generates
two output artefacts:
  - Data/output/cashflow_intelligence.xlsx  (92 rows × 11 columns)
  - Data/output/distress_alerts.csv        (only distressed companies)

All pure functions accept numeric inputs and return floats, strings,
booleans, or None.  No database access, logging, or file I/O inside
the KPI layer.  The orchestration layer (build_company_kpis,
generate_cashflow_intelligence, generate_distress_alerts) is the
only place that touches the database and the filesystem.
"""

from typing import Dict, List, Optional, Tuple, Union
import os
import sys
import math

# ---------------------------------------------------------------------------
# Ensure src/ is importable so that sibling analytics modules resolve
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pandas as pd

# Reuse existing analytics functions
from src.analytics.cashflow import cash_conversion_ratio, free_cash_flow
from src.analytics.cagr import calculate_cagr
from src.analytics.capital_allocation import capital_allocation_category

# Type alias for numeric values that may be None
Numeric = Union[float, int, None]


# ---------------------------------------------------------------------------
# 1. CFO Quality
# ---------------------------------------------------------------------------

def calculate_cfo_quality(
    ccr_values: List[Optional[float]],
) -> Tuple[Optional[float], str]:
    """
    Compute CFO quality from a list of annual cash conversion ratios (CFO / PAT).

    The mean of all non-None CFO/PAT ratios over the available years is
    computed.  A label is assigned based on the mean:

        > 1.0            -> "High Quality"
        0.5 < mean <= 1.0 -> "Moderate"
        <= 0.5           -> "Accrual Risk"
        (no valid data)  -> (None, "Insufficient Data")

    Args:
        ccr_values: List of CFO/PAT ratios, one per year.  May contain
            None entries for years with missing data.

    Returns:
        Tuple of (mean_ccr, label).  mean_ccr is a float or None;
        label is one of "High Quality", "Moderate", "Accrual Risk",
        "Insufficient Data".

    Examples:
        >>> calculate_cfo_quality([1.5, 1.2, 1.0])
        (1.2333, 'High Quality')
        >>> calculate_cfo_quality([0.8, 0.6])
        (0.7, 'Moderate')
        >>> calculate_cfo_quality([0.3, 0.2])
        (0.25, 'Accrual Risk')
        >>> calculate_cfo_quality([None, None])
        (None, 'Insufficient Data')
    """
    valid = [v for v in ccr_values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not valid:
        return None, "Insufficient Data"

    mean_ccr = sum(valid) / len(valid)

    if mean_ccr > 1.0:
        label = "High Quality"
    elif mean_ccr > 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return round(mean_ccr, 4), label


# ---------------------------------------------------------------------------
# 2. CapEx Intensity
# ---------------------------------------------------------------------------

def calculate_capex_intensity(
    investing_activity: Optional[float],
    sales: Optional[float],
) -> Tuple[Optional[float], str]:
    """
    Compute CapEx intensity as |investing_activity| / sales * 100.

    The investing_activity figure from the cash-flow statement includes
    capital expenditure and other investing items.  Its absolute value
    is used because investing cash flow is typically negative.

    Labels:
        < 20 %           -> "Asset Light"
        20 % - 50 %      -> "Moderate"
        > 50 %           -> "Capital Intensive"
        (invalid input)  -> (None, "Insufficient Data")

    Args:
        investing_activity: Total investing cash flow for the latest year
            (typically negative).
        sales: Total revenue / sales for the latest year.

    Returns:
        Tuple of (intensity_pct, label).

    Examples:
        >>> calculate_capex_intensity(-100, 1000)
        (10.0, 'Asset Light')
        >>> calculate_capex_intensity(-300, 1000)
        (30.0, 'Moderate')
        >>> calculate_capex_intensity(-600, 1000)
        (60.0, 'Capital Intensive')
        >>> calculate_capex_intensity(None, 1000)
        (None, 'Insufficient Data')
    """
    if investing_activity is None or sales is None:
        return None, "Insufficient Data"
    if sales == 0 or sales < 0:
        return None, "Insufficient Data"

    intensity_pct = abs(investing_activity) / sales * 100.0

    if intensity_pct < 20.0:
        label = "Asset Light"
    elif intensity_pct <= 50.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return round(intensity_pct, 2), label


# ---------------------------------------------------------------------------
# 3. FCF CAGR (5-year)
# ---------------------------------------------------------------------------

def calculate_fcf_cagr(
    fcf_values: List[Optional[float]],
    years: List[int],
) -> Optional[float]:
    """
    Compute the 5-year compound annual growth rate of free cash flow.

    Uses calculate_cagr() internally.  Only positive FCF values are
    considered (matching the pattern in pros_cons_generator's
    _compute_cagr_from_series), because calculate_cagr() rejects
    non-positive start values.  The oldest and newest positive
    non-None FCF values are taken as start and end, and the number of
    years elapsed is computed from the corresponding year values.

    Args:
        fcf_values: List of FCF values ordered most-recent-first
            (same ordering as the cash-flow DataFrame returned by the
            DB helpers -- DESC by year).
        years: Parallel list of integer years.

    Returns:
        CAGR as a percentage, or None if fewer than 2 positive values
        are available or calculate_cagr() returns None.

    Examples:
        >>> calculate_fcf_cagr([300, 200, 150, 100, 50], [2024, 2023, 2022, 2021, 2020])
        48.81...
        >>> calculate_fcf_cagr([-100, 200, 150, 100, 50], [2024, 2023, 2022, 2021, 2020])
        # start=50 (2020), end=300 (2023), years=3
        58.74...
    """
    pairs = [(y, v) for y, v in zip(years, fcf_values)
             if v is not None and not (isinstance(v, float) and math.isnan(v))
             and y is not None
             and v > 0]

    pairs.sort(key=lambda p: p[0])

    if len(pairs) < 2:
        return None

    start_year, start_val = pairs[0]
    end_year, end_val = pairs[-1]
    n_years = end_year - start_year

    if n_years <= 0:
        return None

    return calculate_cagr(start_val, end_val, n_years)


# ---------------------------------------------------------------------------
# 4. FCF Conversion
# ---------------------------------------------------------------------------

def calculate_fcf_conversion(
    fcf_latest: Optional[float],
    pat_latest: Optional[float],
) -> Optional[float]:
    """
    Compute FCF conversion: FCF_latest / PAT_latest * 100.

    A ratio above 100% means the company generates more free cash than
    it books as profit -- a sign of high-quality earnings.

    Args:
        fcf_latest: Free cash flow for the latest year (OCF - CapEx).
        pat_latest: Net profit (PAT) for the latest year.

    Returns:
        FCF conversion percentage, or None if either input is None or
        PAT is zero/negative.

    Examples:
        >>> calculate_fcf_conversion(300, 200)
        150.0
        >>> calculate_fcf_conversion(100, 100)
        100.0
        >>> calculate_fcf_conversion(50, 0)
        None
    """
    if fcf_latest is None or pat_latest is None:
        return None
    if pat_latest <= 0:
        return None
    return round(fcf_latest / pat_latest * 100.0, 2)


# ---------------------------------------------------------------------------
# 5. Distress Flag
# ---------------------------------------------------------------------------

def detect_distress(
    cfo_latest: Optional[float],
    cff_latest: Optional[float],
) -> bool:
    """
    Detect financial distress: CFO negative AND CFF positive.

    When a company is burning operating cash (negative CFO) but propping
    itself up with fresh financing (positive CFF), it may be in distress.

    Args:
        cfo_latest: Operating cash flow for the latest year.
        cff_latest: Financing cash flow for the latest year.

    Returns:
        True if CFO < 0 AND CFF > 0, False otherwise (including None
        inputs).

    Examples:
        >>> detect_distress(-100, 50)
        True
        >>> detect_distress(100, 50)
        False
        >>> detect_distress(None, 50)
        False
    """
    if cfo_latest is None or cff_latest is None:
        return False
    if isinstance(cfo_latest, float) and math.isnan(cfo_latest):
        return False
    if isinstance(cff_latest, float) and math.isnan(cff_latest):
        return False
    return cfo_latest < 0 and cff_latest > 0


# ---------------------------------------------------------------------------
# 6. Deleveraging Flag
# ---------------------------------------------------------------------------

def detect_deleveraging(
    cff_latest: Optional[float],
    borrowings_latest: Optional[float],
    borrowings_previous: Optional[float],
) -> bool:
    """
    Detect deleveraging: CFF negative AND borrowings declining YoY.

    A company that is actively repaying debt (negative financing cash
    flow) while reducing its borrowings year-over-year is deleveraging.

    Args:
        cff_latest: Financing cash flow for the latest year.
        borrowings_latest: Total borrowings for the latest year.
        borrowings_previous: Total borrowings for the preceding year.

    Returns:
        True if CFF < 0 AND borrowings_latest < borrowings_previous,
        False otherwise (including None inputs).

    Examples:
        >>> detect_deleveraging(-100, 400, 500)
        True
        >>> detect_deleveraging(100, 400, 500)
        False
        >>> detect_deleveraging(-100, 500, 400)
        False
    """
    if cff_latest is None or borrowings_latest is None or borrowings_previous is None:
        return False
    vals = [cff_latest, borrowings_latest, borrowings_previous]
    if any(isinstance(v, float) and math.isnan(v) for v in vals):
        return False
    return cff_latest < 0 and borrowings_latest < borrowings_previous


# ---------------------------------------------------------------------------
# 7. Capital Allocation
# ---------------------------------------------------------------------------

def calculate_capital_allocation(
    roe: Optional[float],
    roce: Optional[float],
    cash_conversion_ratio_val: Optional[float],
) -> Optional[str]:
    """
    Classify capital allocation quality.

    Delegates directly to capital_allocation_category() from
    src/analytics/capital_allocation.py.

    Args:
        roe: Return on Equity (%).
        roce: Return on Capital Employed (%).
        cash_conversion_ratio_val: Cash conversion ratio (OCF / PAT).

    Returns:
        Capital allocation category string: "Excellent", "Good",
        "Average", "Weak", "Poor", or None if any input is None.

    Examples:
        >>> calculate_capital_allocation(25, 25, 1.5)
        'Excellent'
        >>> calculate_capital_allocation(None, 20, 1.2)
        None
    """
    return capital_allocation_category(roe, roce, cash_conversion_ratio_val)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_float(value) -> Optional[float]:
    """Convert a value to float, returning None for NaN/inf/None/errors."""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _to_float(value) -> Optional[float]:
    """Alias for _safe_float."""
    return _safe_float(value)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_company_kpis(company_id: str) -> Dict:
    """
    Build all 11 KPI columns for a single company.

    Fetches data via DB helpers and computes the 7 KPIs.

    Args:
        company_id: Company ticker / ID (e.g. "BHARTIARTL").

    Returns:
        Dict with keys:
            company_id, cfo_quality_value, cfo_quality_label,
            capex_intensity_value, capex_intensity_label,
            fcf_cagr_5yr, fcf_conversion_pct, distress_flag,
            deleveraging_flag, capital_allocation, latest_year
    """
    from src.dashboard.utils.db import (
        get_cashflow_data, get_pl, get_bs, get_financial_ratios,
    )

    result = {
        "company_id": company_id,
        "cfo_quality_value": None,
        "cfo_quality_label": "Insufficient Data",
        "capex_intensity_value": None,
        "capex_intensity_label": "Insufficient Data",
        "fcf_cagr_5yr": None,
        "fcf_conversion_pct": None,
        "distress_flag": False,
        "deleveraging_flag": False,
        "capital_allocation": None,
        "latest_year": None,
    }

    # --- Fetch raw data ---
    cf_df = get_cashflow_data(company_id)
    pl_df = get_pl(company_id)
    bs_df = get_bs(company_id)
    fr_df = get_financial_ratios(company_id)

    if cf_df.empty:
        return result

    cf_df = cf_df.sort_values("year", ascending=False).reset_index(drop=True)

    # Latest year
    latest_year = int(cf_df.iloc[0]["year"]) if pd.notna(cf_df.iloc[0]["year"]) else None
    result["latest_year"] = latest_year

    # Extract up to 5 years of cash flow data (most recent first)
    n_years = min(5, len(cf_df))
    cf_subset = cf_df.head(n_years)

    ocf_values = [_to_float(v) for v in cf_subset["operating_activity"].tolist()]
    cff_values = [_to_float(v) for v in cf_subset["financing_activity"].tolist()]
    investing_values = [_to_float(v) for v in cf_subset["investing_activity"].tolist()]
    cf_years = [int(y) if pd.notna(y) else None for y in cf_subset["year"].tolist()]

    # --- CFO Quality (mean CCR over 5 years) ---
    ccr_values = []
    if not pl_df.empty:
        for i, year in enumerate(cf_years):
            if year is None:
                ccr_values.append(None)
                continue
            pat_row = pl_df[pl_df["year"] == year]
            pat = _to_float(pat_row.iloc[0]["net_profit"]) if not pat_row.empty else None
            ocf = ocf_values[i] if i < len(ocf_values) else None
            ccr = cash_conversion_ratio(ocf, pat) if ocf is not None else None
            ccr_values.append(ccr)

    cfo_quality_val, cfo_quality_lbl = calculate_cfo_quality(ccr_values)
    result["cfo_quality_value"] = cfo_quality_val
    result["cfo_quality_label"] = cfo_quality_lbl

    # --- CapEx Intensity (latest year) ---
    latest_ocf = ocf_values[0] if ocf_values else None
    latest_cff = cff_values[0] if cff_values else None
    latest_investing = investing_values[0] if investing_values else None
    latest_sales = None
    if not pl_df.empty and pd.notna(pl_df.iloc[0]["year"]):
        latest_sales = _to_float(pl_df.iloc[0]["sales"])

    capex_intensity_val, capex_intensity_lbl = calculate_capex_intensity(latest_investing, latest_sales)
    result["capex_intensity_value"] = capex_intensity_val
    result["capex_intensity_label"] = capex_intensity_lbl

    # --- FCF CAGR (5-year) ---
    # FCF = OCF - CapEx.  CapEx is available in financial_ratios.capex_cr
    # and OCF is in cashflow.operating_activity
    fcf_values = []
    for i, year in enumerate(cf_years):
        ocf = ocf_values[i] if i < len(ocf_values) else None
        capex = None
        if not fr_df.empty:
            fr_row = fr_df[fr_df["year"] == year]
            if not fr_row.empty:
                capex = _to_float(fr_row.iloc[0]["capex_cr"])
        if ocf is not None and capex is not None:
            fcf = free_cash_flow(ocf, capex)
            fcf_values.append(fcf)
        elif ocf is not None and latest_investing is not None:
            # Fallback: use investing_activity as a proxy for capex if no capex_cr
            fcf = free_cash_flow(ocf, abs(latest_investing) if latest_investing < 0 else latest_investing)
            fcf_values.append(fcf)
        else:
            fcf_values.append(None)

    fcf_cagr = calculate_fcf_cagr(fcf_values, cf_years)
    result["fcf_cagr_5yr"] = round(fcf_cagr, 2) if fcf_cagr is not None else None

    # --- FCF Conversion ---
    fcf_latest = fcf_values[0] if fcf_values else None
    pat_latest = None
    if not pl_df.empty and pd.notna(pl_df.iloc[0]["year"]):
        pat_latest = _to_float(pl_df.iloc[0]["net_profit"])

    fcf_conv = calculate_fcf_conversion(fcf_latest, pat_latest)
    result["fcf_conversion_pct"] = fcf_conv

    # --- Distress Flag ---
    distress = detect_distress(latest_ocf, latest_cff)
    result["distress_flag"] = distress

    # --- Deleveraging Flag ---
    borrowings_latest = None
    borrowings_previous = None
    if not bs_df.empty:
        bs_sorted = bs_df.sort_values("year", ascending=False).reset_index(drop=True)
        borrowings_latest = _to_float(bs_sorted.iloc[0]["borrowings"]) if len(bs_sorted) > 0 else None
        borrowings_previous = _to_float(bs_sorted.iloc[1]["borrowings"]) if len(bs_sorted) > 1 else None

    deleveraging = detect_deleveraging(latest_cff, borrowings_latest, borrowings_previous)
    result["deleveraging_flag"] = deleveraging

    # --- Capital Allocation ---
    roe = None
    roce = None
    ccr_latest = ccr_values[0] if ccr_values else None
    if not fr_df.empty:
        roe = _to_float(fr_df.iloc[0]["return_on_equity_pct"]) if len(fr_df) > 0 else None
        roce = _to_float(fr_df.iloc[0]["return_on_capital_employed_pct"]) if len(fr_df) > 0 else None

    ca = calculate_capital_allocation(roe, roce, ccr_latest)
    result["capital_allocation"] = ca

    return result


def generate_cashflow_intelligence() -> pd.DataFrame:
    """
    Generate the full cash flow intelligence DataFrame for all companies.

    Returns:
        pd.DataFrame with 11 columns:
            company_id, cfo_quality_value, cfo_quality_label,
            capex_intensity_value, capex_intensity_label,
            fcf_cagr_5yr, fcf_conversion_pct, distress_flag,
            deleveraging_flag, capital_allocation, latest_year
    """
    from src.dashboard.utils.db import get_company_list

    companies = get_company_list()
    rows = []

    for company in companies:
        company_id = company["company_id"]
        kpis = build_company_kpis(company_id)
        rows.append(kpis)

    df = pd.DataFrame(rows)

    # Ensure column order
    columns = [
        "company_id",
        "cfo_quality_value",
        "cfo_quality_label",
        "capex_intensity_value",
        "capex_intensity_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation",
        "latest_year",
    ]

    # Reorder columns, filling missing with empty
    for col in columns:
        if col not in df.columns:
            df[col] = None
    df = df[columns]

    return df


def generate_distress_alerts(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Filter the cash flow intelligence DataFrame to only distressed companies.

    Args:
        df: Optional pre-computed DataFrame from
            generate_cashflow_intelligence().  If None, the function
            will generate it on the fly.

    Returns:
        pd.DataFrame containing only rows where distress_flag is True,
        with all 11 columns.
    """
    if df is None:
        df = generate_cashflow_intelligence()

    if df.empty:
        return df

    return df[df["distress_flag"] == True].reset_index(drop=True)


def save_outputs(df: Optional[pd.DataFrame] = None) -> None:
    """
    Save the cash flow intelligence outputs to disk.

    Generates (or uses provided) DataFrame and writes:
      - Data/output/cashflow_intelligence.xlsx
      - Data/output/distress_alerts.csv

    Args:
        df: Optional pre-computed DataFrame.  If None, generated on the fly.
    """
    if df is None:
        df = generate_cashflow_intelligence()

    output_dir = os.path.join(_PROJECT_ROOT, "Data", "output")
    os.makedirs(output_dir, exist_ok=True)

    xlsx_path = os.path.join(output_dir, "cashflow_intelligence.xlsx")
    csv_path = os.path.join(output_dir, "distress_alerts.csv")

    df.to_excel(xlsx_path, index=False)
    alerts_df = generate_distress_alerts(df)
    alerts_df.to_csv(csv_path, index=False)


if __name__ == "__main__":
    df = generate_cashflow_intelligence()
    save_outputs(df)
    print(f"Generated cashflow_intelligence.xlsx: {len(df)} rows")
    print(f"Distress alerts: {df['distress_flag'].sum()} companies")
