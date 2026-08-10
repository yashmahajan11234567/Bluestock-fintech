"""
Auto Pros/Cons Generator for financial analysis.

Evaluates companies against 24 rules (12 Pro, 12 Con) and generates
pros/cons signals with deterministic confidence scores.

Uses existing analytics functions from src/analytics/ for calculations.
Reads data from the SQLite database via src/dashboard/utils/db.py.

Specification: Sprint 5, Day 30 — exactly 24 rules (PRO_1..PRO_12, CON_1..CON_12).
PRO_13 and CON_13 were tested as extensions but are NOT part of the final Sprint 5 implementation.
"""

import math
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

# Import from dashboard utils for database access
from src.dashboard.utils.db import (
    get_company_list,
    get_financial_ratios,
    get_pl,
    get_bs,
    get_valuation,
    get_sectors,
)

# Import analytics functions
from src.analytics.cagr import calculate_cagr


@dataclass
class ProsConsSignal:
    """A single pros or cons signal for a company."""
    company_id: str
    type: str  # "pro" or "con"
    rule_id: str
    text: str
    confidence_pct: float


@dataclass
class CompanyData:
    """Aggregated financial data for a company."""
    company_id: str
    financial_ratios: pd.DataFrame  # yearly ratios
    pl_data: pd.DataFrame  # yearly P&L
    bs_data: pd.DataFrame  # yearly balance sheet
    market_cap: pd.DataFrame  # yearly valuation
    sector: Optional[str] = None


def get_company_universe() -> List[Dict[str, str]]:
    """Get the full company universe from the database."""
    return get_company_list()


def load_company_data(company_id: str) -> CompanyData:
    """Load all financial data for a company from the database."""
    fr = get_financial_ratios(company_id)
    pl = get_pl(company_id)
    bs = get_bs(company_id)
    mc = get_valuation(company_id)

    sector_df = pd.DataFrame(get_sectors())
    sector_row = sector_df[sector_df['company_id'] == company_id]
    sector = sector_row['broad_sector'].iloc[0] if not sector_row.empty else None

    return CompanyData(
        company_id=company_id,
        financial_ratios=fr,
        pl_data=pl,
        bs_data=bs,
        market_cap=mc,
        sector=sector,
    )


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float, returning None on failure."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return None
        return result
    except (ValueError, TypeError):
        return None


def _get_latest_year_value(df: pd.DataFrame, col: str) -> Optional[float]:
    """Get the latest year value for a column from a DataFrame sorted by year descending."""
    if df.empty or col not in df.columns:
        return None
    val = df[col].iloc[0]
    return _safe_float(val)


def _get_year_values(df: pd.DataFrame, col: str) -> List[Optional[float]]:
    """Get all yearly values for a column."""
    if df.empty or col not in df.columns:
        return []
    return [_safe_float(v) for v in df[col].tolist()]


def _compute_cagr_from_series(values: List[Optional[float]], years: int) -> Optional[float]:
    """
    Compute CAGR from a list of values sorted newest-to-oldest.

    Takes the most recent value as start and oldest as end.
    """
    # values are sorted newest-to-oldest (DESC year order)
    # start = oldest (last valid), end = newest (first valid)
    valid = [(i, v) for i, v in enumerate(values) if v is not None and v > 0]
    if len(valid) < 2:
        return None

    # newest is valid[0], oldest is valid[-1]
    # CAGR: start = oldest, end = newest
    start_val = valid[-1][1]  # oldest
    end_val = valid[0][1]     # newest
    actual_years = valid[-1][0] - valid[0][0]  # number of periods between them (oldest index - newest index)
    if actual_years <= 0:
        return 0.0
    return calculate_cagr(start_val, end_val, actual_years)


def _consecutive_years_count(values: List[Optional[float]], condition_fn) -> int:
    """Count consecutive years from most recent where condition is True."""
    count = 0
    for v in values:
        if v is None or not condition_fn(v):
            break
        count += 1
    return count


def _consecutive_years_negative(values: List[Optional[float]], min_years: int) -> bool:
    """Check if values are negative for at least min_years consecutive years (most recent first)."""
    count = 0
    for v in values:
        if v is not None and v < 0:
            count += 1
            if count >= min_years:
                return True
        else:
            count = 0
    return count >= min_years


def _consecutive_years_present(values: List[Optional[float]], min_years: int) -> int:
    """Count consecutive non-None values from most recent."""
    count = 0
    for v in values:
        if v is None:
            break
        count += 1
    return count


# ============================================================
# CONFIDENCE SCORING METHODOLOGY
# ============================================================
#
# Confidence scores are deterministic and based on:
# 1. Margin from threshold (how far above/below the threshold)
# 2. Data completeness (number of years available)
# 3. Persistence (number of consecutive years satisfying the condition)
#
# Formula:
#   base_score = 50 (mid-range, neutral starting point)
#   margin_bonus = min(margin / threshold, 1.0) * 25  (0-25)
#   completeness_bonus = min(years_present / required_years, 1.0) * 15  (0-15)
#   persistence_bonus = min(consecutive_years / required_consecutive, 1.0) * 10  (0-10)
#
#   confidence = base_score + margin_bonus + completeness_bonus + persistence_bonus
#   clamped to [0, 100]

def _confidence_margin(metric_value: float, threshold: float, is_higher_better: bool = True) -> float:
    """Calculate confidence based on margin from threshold."""
    if threshold == 0:
        return 0.0
    ratio = abs(metric_value / threshold)
    if is_higher_better:
        if metric_value >= threshold:
            return min((ratio - 1.0) / 1.0 * 25, 25.0)
        else:
            return -min((1.0 - ratio) / 1.0 * 25, 25.0)
    else:
        if metric_value <= threshold:
            return min((1.0 - ratio) / 1.0 * 25, 25.0)
        else:
            return -min((ratio - 1.0) / 1.0 * 25, 25.0)


def _confidence_completeness(years_present: int, required_years: int) -> float:
    """Calculate confidence based on data completeness."""
    if required_years <= 0:
        return 15.0
    return min(years_present / required_years * 15.0, 15.0)


def _confidence_persistence(consecutive_years: int, required_years: int) -> float:
    """Calculate confidence based on persistence of condition."""
    if required_years <= 0:
        return 10.0
    return min(consecutive_years / required_years * 10.0, 10.0)


def _compute_confidence(
    metric_value: Optional[float],
    threshold: float,
    is_higher_better: bool,
    years_present: int,
    required_years: int,
    consecutive_years: int,
    required_consecutive: int,
) -> float:
    """
    Compute a deterministic confidence score (0-100).

    Methodology:
    - Base score: 50
    - Margin bonus: how far metric exceeds/falls below threshold (0-25)
    - Completeness bonus: data coverage (0-15)
    - Persistence bonus: consecutive years satisfying condition (0-10)

    For CON rules, is_higher_better should be True when the metric
    THRESHOLD being exceeded is the bad condition (e.g., D/E > 2.0).
    This ensures margin bonus is positive when the bad condition is met.
    For CON rules where the metric being BELOW the threshold is the bad
    condition (e.g., ICR < 1.5), pass is_higher_better=False.
    """
    if metric_value is None:
        return 0.0

    base = 50.0
    margin = _confidence_margin(metric_value, threshold, is_higher_better)
    completeness = _confidence_completeness(years_present, required_years)
    persistence = _confidence_persistence(consecutive_years, required_consecutive)

    confidence = base + margin + completeness + persistence
    return max(0.0, min(100.0, confidence))


# ============================================================
# PRO RULES
# ============================================================

def rule_pro_1_roe_sustained(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_1: ROE > 20% sustained for 3+ years.

    Uses financial_ratios.return_on_equity_pct trend.
    """
    roe_values = _get_year_values(data.financial_ratios, 'return_on_equity_pct')
    if not roe_values:
        return None

    consecutive = _consecutive_years_count(roe_values, lambda v: v > 20)
    if consecutive < 3:
        return None

    years_present = _consecutive_years_present(roe_values, 3)
    latest_roe = roe_values[0] if roe_values[0] is not None else 0.0

    confidence = _compute_confidence(
        latest_roe, 20.0, True, years_present, 3, consecutive, 3
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_1",
        text="Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_2_fcf_positive_5y(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_2: FCF positive for 5+ consecutive years.

    Uses financial_ratios.free_cash_flow_cr.
    """
    fcf_values = _get_year_values(data.financial_ratios, 'free_cash_flow_cr')

    consecutive = _consecutive_years_count(fcf_values, lambda v: v > 0)
    if consecutive < 5:
        return None

    years_present = _consecutive_years_present(fcf_values, 5)
    latest_fcf = fcf_values[0] if fcf_values[0] is not None else 0.0

    # For positive conditions, confidence based on magnitude
    avg_fcf = np.mean([v for v in fcf_values if v is not None]) if fcf_values else 0.0

    confidence = _compute_confidence(
        abs(avg_fcf), 1.0, True, years_present, 5, consecutive, 5
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_2",
        text="Strong free cash flow generation over 5 years signals healthy business fundamentals",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_3_de_ratio_zero(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_3: D/E = 0 in latest year.

    Uses financial_ratios.debt_to_equity.
    """
    latest_dte = _get_latest_year_value(data.financial_ratios, 'debt_to_equity')

    if latest_dte is None:
        # Check if interest is zero or borrowings are zero from P&L/BS
        latest_interest = _get_latest_year_value(data.pl_data, 'interest')
        if latest_interest is not None and latest_interest == 0:
            confidence = _compute_confidence(0.0, 0.0, True, 1, 1, 1, 1)
            confidence = max(confidence, 70.0)  # Strong signal for debt-free
            return ProsConsSignal(
                company_id=data.company_id,
                type="pro",
                rule_id="PRO_3",
                text="Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                confidence_pct=round(confidence, 2),
            )
        return None

    if latest_dte > 0:
        return None

    years_present = _consecutive_years_present(
        _get_year_values(data.financial_ratios, 'debt_to_equity'), 1
    )

    confidence = _compute_confidence(0.0, 0.0, True, years_present, 1, 1, 1)
    # D/E = 0 is a strong, definitive signal
    confidence = max(confidence, 70.0)

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_3",
        text="Debt-free balance sheet provides financial flexibility and eliminates interest burden",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_4_revenue_cagr_15pct(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_4: Revenue CAGR > 15% over 5 years.

    Computes CAGR from P&L sales data.
    """
    sales_values = _get_year_values(data.pl_data, 'sales')

    cagr = _compute_cagr_from_series(sales_values, 5)
    if cagr is None or cagr <= 15:
        return None

    years_present = _consecutive_years_present(sales_values, 5)

    confidence = _compute_confidence(
        cagr, 15.0, True, years_present, 5, years_present, 5
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_4",
        text="Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_5_opm_25pct(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_5: OPM > 25% in latest year.

    Uses financial_ratios.operating_profit_margin_pct.
    """
    latest_opm = _get_latest_year_value(data.financial_ratios, 'operating_profit_margin_pct')
    if latest_opm is None or latest_opm <= 25:
        return None

    years_present = _consecutive_years_present(
        _get_year_values(data.financial_ratios, 'operating_profit_margin_pct'), 1
    )

    confidence = _compute_confidence(
        latest_opm, 25.0, True, years_present, 1, 1, 1
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_5",
        text="Operating profit margin above 25% indicates strong pricing power and cost discipline",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_6_pat_cagr_20pct(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_6: PAT CAGR > 20% over 5 years.

    Computes CAGR from P&L net_profit data.
    """
    profit_values = _get_year_values(data.pl_data, 'net_profit')

    cagr = _compute_cagr_from_series(profit_values, 5)
    if cagr is None or cagr <= 20:
        return None

    years_present = _consecutive_years_present(profit_values, 5)

    confidence = _compute_confidence(
        cagr, 20.0, True, years_present, 5, years_present, 5
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_6",
        text="Net profit compounding at above 20% over 5 years creates significant shareholder value",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_7_icr_high_or_debt_free(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_7: ICR > 10 OR Debt Free.

    Uses financial_ratios.interest_coverage.
    """
    latest_icr = _get_latest_year_value(data.financial_ratios, 'interest_coverage')
    latest_interest = _get_latest_year_value(data.pl_data, 'interest')

    # Check for Debt Free (interest = 0 or None)
    is_debt_free = latest_interest is not None and latest_interest == 0
    if not is_debt_free:
        latest_dte = _get_latest_year_value(data.financial_ratios, 'debt_to_equity')
        if latest_dte is not None and latest_dte == 0:
            is_debt_free = True

    if latest_icr is not None and latest_icr > 10:
        years_present = _consecutive_years_present(
            _get_year_values(data.financial_ratios, 'interest_coverage'), 1
        )
        confidence = _compute_confidence(
            latest_icr, 10.0, True, years_present, 1, 1, 1
        )
    elif is_debt_free:
        confidence = 75.0
    else:
        return None

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_7",
        text="Very high interest coverage ratio reflects negligible financial stress from debt servicing",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_8_dividend_yield_and_fcf(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_8: Dividend Yield > 2% AND FCF positive.

    Uses market_cap.dividend_yield_pct and financial_ratios.free_cash_flow_cr.
    """
    latest_dy = _get_latest_year_value(data.market_cap, 'dividend_yield_pct')
    latest_fcf = _get_latest_year_value(data.financial_ratios, 'free_cash_flow_cr')

    if latest_dy is None or latest_dy <= 2:
        return None
    if latest_fcf is None or latest_fcf <= 0:
        return None

    dy_years = _consecutive_years_present(
        _get_year_values(data.market_cap, 'dividend_yield_pct'), 1
    )
    fcf_years = _consecutive_years_present(
        _get_year_values(data.financial_ratios, 'free_cash_flow_cr'), 1
    )

    # Confidence based on both metrics
    dy_conf = _compute_confidence(latest_dy, 2.0, True, dy_years, 1, 1, 1)
    fcf_conf = _compute_confidence(abs(latest_fcf), 1.0, True, fcf_years, 1, 1, 1)
    confidence = (dy_conf + fcf_conf) / 2.0

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_8",
        text="Consistent dividend yield above 2% backed by positive free cash flow",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_9_eps_cagr_15pct(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_9: EPS CAGR > 15% over 5 years.

    Computes CAGR from P&L EPS data.
    """
    eps_values = _get_year_values(data.pl_data, 'eps')

    cagr = _compute_cagr_from_series(eps_values, 5)
    if cagr is None or cagr <= 15:
        return None

    years_present = _consecutive_years_present(eps_values, 5)

    confidence = _compute_confidence(
        cagr, 15.0, True, years_present, 5, years_present, 5
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_9",
        text="Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_10_roe_improving_3y(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_10: ROE improving for 3 consecutive years.

    Uses financial_ratios.return_on_equity_pct trend.
    """
    roe_values = _get_year_values(data.financial_ratios, 'return_on_equity_pct')

    # Check for 3 consecutive years of improvement (newest first)
    # We need to reverse to get oldest-first for trend check
    valid_roe = [(i, v) for i, v in enumerate(roe_values) if v is not None]
    if len(valid_roe) < 3:
        return None

    # Check if ROE is improving for 3 consecutive years (from newest to oldest, so decreasing index)
    # ROE values are sorted DESC by year, so indices 0,1,2 are most recent 3 years
    # "Improving" means newest > older
    for i in range(len(valid_roe) - 2):
        idx1, val1 = valid_roe[i]
        idx2, val2 = valid_roe[i + 1]
        idx3, val3 = valid_roe[i + 2]
        if val1 > val2 > val3:
            # Found 3 consecutive years of improvement
            consecutive = 3
            while i + consecutive < len(valid_roe):
                idx_next, val_next = valid_roe[i + consecutive]
                idx_prev, val_prev = valid_roe[i + consecutive - 1]
                if val_prev > val_next:
                    consecutive += 1
                else:
                    break

            years_present = len(valid_roe)
            latest_roe = valid_roe[0][1]

            confidence = _compute_confidence(
                latest_roe, 20.0, True, years_present, 3, consecutive, 3
            )
            # Bonus for improvement trend
            confidence = min(100.0, confidence + 5.0)

            if confidence <= 60:
                return None

            return ProsConsSignal(
                company_id=data.company_id,
                type="pro",
                rule_id="PRO_10",
                text="Return on equity improving for 3 consecutive years shows strengthening business quality",
                confidence_pct=round(confidence, 2),
            )

    return None


def rule_pro_11_revenue_cagr_gt_pat_cagr(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_11: Revenue CAGR > PAT CAGR.
    """
    sales_cagr = _compute_cagr_from_series(_get_year_values(data.pl_data, 'sales'), 5)
    pat_cagr = _compute_cagr_from_series(_get_year_values(data.pl_data, 'net_profit'), 5)

    if sales_cagr is None or pat_cagr is None:
        return None
    if sales_cagr <= pat_cagr:
        return None

    years_present = min(
        _consecutive_years_present(_get_year_values(data.pl_data, 'sales'), 5),
        _consecutive_years_present(_get_year_values(data.pl_data, 'net_profit'), 5),
    )

    # Confidence based on the spread between the two CAGRs
    spread = sales_cagr - pat_cagr
    confidence = 50.0 + min(spread / 5.0 * 15, 20.0)  # up to 20 bonus for spread
    confidence += _confidence_completeness(years_present, 5)
    confidence = max(0.0, min(100.0, confidence))

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_11",
        text="Revenue growing slower than profits shows improving operating leverage and scale benefits",
        confidence_pct=round(confidence, 2),
    )


def rule_pro_12_assets_growing_declining_debt(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    PRO_12: Balance sheet assets growing with declining debt.
    """
    assets_values = _get_year_values(data.bs_data, 'total_assets')
    borrowings_values = _get_year_values(data.bs_data, 'borrowings')

    if not assets_values or not borrowings_values:
        return None

    # Check if assets growing (newest > older, since sorted DESC by year)
    # and debt declining (newest < older)
    valid_assets = [(i, v) for i, v in enumerate(assets_values) if v is not None and v > 0]
    valid_borrowings = [(i, v) for i, v in enumerate(borrowings_values) if v is not None]

    if len(valid_assets) < 2 or len(valid_borrowings) < 2:
        return None

    # Check most recent 3 years: assets growing and debt declining
    recent_assets = [v for _, v in valid_assets[:3]]
    recent_borrowings = [v for _, v in valid_borrowings[:3]]

    if len(recent_assets) < 2 or len(recent_borrowings) < 2:
        return None

    assets_growing = recent_assets[0] > recent_assets[-1]
    debt_declining = recent_borrowings[0] < recent_borrowings[-1]

    if not assets_growing or not debt_declining:
        return None

    years_present = _consecutive_years_present(assets_values, 3)
    assets_growth = recent_assets[0] / recent_assets[-1] - 1 if recent_assets[-1] > 0 else 0

    confidence = _compute_confidence(
        abs(assets_growth) * 100, 0.0, True, years_present, 3, years_present, 3
    )
    # Add bonus for declining debt
    confidence = min(100.0, confidence + 10.0)

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="pro",
        rule_id="PRO_12",
        text="Growing asset base funded by internal accruals reflects self-sustaining growth",
        confidence_pct=round(confidence, 2),
    )


# ============================================================
# CON RULES
# ============================================================

def rule_con_1_debt_to_equity_high(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_1: D/E > 2.0 for non-financial companies.

    Uses financial_ratios.debt_to_equity.
    """
    if data.sector and data.sector.lower().startswith('financial'):
        return None

    latest_dte = _get_latest_year_value(data.financial_ratios, 'debt_to_equity')
    if latest_dte is None or latest_dte <= 2.0:
        return None

    years_present = _consecutive_years_present(
        _get_year_values(data.financial_ratios, 'debt_to_equity'), 1
    )

    confidence = _compute_confidence(
        latest_dte, 2.0, True, years_present, 1, 1, 1
    )

    if confidence <= 60:
        return None

    text = f"Debt-to-equity ratio of {latest_dte:.2f} is elevated for a non-financial company and warrants monitoring"

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_1",
        text=text,
        confidence_pct=round(confidence, 2),
    )


def rule_con_2_fcf_negative_3y(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_2: FCF negative for 3 consecutive years.

    Uses financial_ratios.free_cash_flow_cr.
    """
    fcf_values = _get_year_values(data.financial_ratios, 'free_cash_flow_cr')

    consecutive = _consecutive_years_count(fcf_values, lambda v: v < 0)
    if consecutive < 3:
        return None

    years_present = _consecutive_years_present(fcf_values, 3)

    confidence = _compute_confidence(
        0.0, 0.0, False, years_present, 3, consecutive, 3
    )
    # Higher confidence for sustained negative FCF
    confidence = min(100.0, confidence + 10.0)

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_2",
        text="Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
        confidence_pct=round(confidence, 2),
    )


def rule_con_3_opm_declining_3y(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_3: OPM declining for 3 consecutive years.

    Uses financial_ratios.operating_profit_margin_pct.
    """
    opm_values = _get_year_values(data.financial_ratios, 'operating_profit_margin_pct')

    valid_opm = [(i, v) for i, v in enumerate(opm_values) if v is not None]
    if len(valid_opm) < 3:
        return None

    # Check for 3 consecutive years of decline (newest first, so newest < older)
    for i in range(len(valid_opm) - 2):
        idx1, val1 = valid_opm[i]
        idx2, val2 = valid_opm[i + 1]
        idx3, val3 = valid_opm[i + 2]
        if val1 < val2 < val3:
            consecutive = 3
            while i + consecutive < len(valid_opm):
                idx_next, val_next = valid_opm[i + consecutive]
                idx_prev, val_prev = valid_opm[i + consecutive - 1]
                if val_prev > val_next:
                    consecutive += 1
                else:
                    break

            years_present = len(valid_opm)

            # For trend-based rules, confidence is based on data quality and
            # persistence of the trend, not the absolute metric value.
            # Using latest_opm as metric value would penalize high-margin companies
            # whose margins happen to be declining from a high base.
            confidence = 50.0
            confidence += _confidence_completeness(years_present, 3)
            confidence += _confidence_persistence(consecutive, 3)
            confidence = max(0.0, min(100.0, confidence))

            if confidence <= 60:
                return None

            return ProsConsSignal(
                company_id=data.company_id,
                type="con",
                rule_id="CON_3",
                text="Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                confidence_pct=round(confidence, 2),
            )

    return None


def rule_con_4_net_profit_negative(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_4: Net profit negative in latest year.

    Uses profitandloss.net_profit.
    """
    latest_np = _get_latest_year_value(data.pl_data, 'net_profit')
    if latest_np is None or latest_np >= 0:
        return None

    years_present = _consecutive_years_present(
        _get_year_values(data.pl_data, 'net_profit'), 1
    )

    confidence = _compute_confidence(
        abs(latest_np), 0.0, False, years_present, 1, 1, 1
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_4",
        text="Company reported a net loss in the most recent financial year",
        confidence_pct=round(confidence, 2),
    )


def rule_con_5_revenue_declining_2y(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_5: Revenue declining for 2+ years.

    Uses profitandloss.sales.
    """
    sales_values = _get_year_values(data.pl_data, 'sales')
    valid_sales = [(i, v) for i, v in enumerate(sales_values) if v is not None and v > 0]

    if len(valid_sales) < 2:
        return None

    # Check for 2 consecutive years of decline
    for i in range(len(valid_sales) - 1):
        idx1, val1 = valid_sales[i]
        idx2, val2 = valid_sales[i + 1]
        if val1 < val2:
            consecutive = 2
            while i + consecutive < len(valid_sales):
                idx_next, val_next = valid_sales[i + consecutive]
                idx_prev, val_prev = valid_sales[i + consecutive - 1]
                if val_prev > val_next:
                    consecutive += 1
                else:
                    break

            years_present = _consecutive_years_present(sales_values, consecutive)

            # For trend-based rules, confidence is based on data quality and
            # persistence of the trend, not the absolute metric value.
            confidence = 50.0
            confidence += _confidence_completeness(years_present, 2)
            confidence += _confidence_persistence(consecutive, 2)
            confidence = max(0.0, min(100.0, confidence))

            if confidence <= 60:
                return None

            return ProsConsSignal(
                company_id=data.company_id,
                type="con",
                rule_id="CON_5",
                text="Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                confidence_pct=round(confidence, 2),
            )

    return None


def rule_con_6_icr_low(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_6: ICR < 1.5.

    Uses financial_ratios.interest_coverage.
    """
    latest_icr = _get_latest_year_value(data.financial_ratios, 'interest_coverage')
    if latest_icr is None or latest_icr >= 1.5:
        return None

    # Check if company has debt (if ICR is None but debt is 0, it's not a con)
    latest_dte = _get_latest_year_value(data.financial_ratios, 'debt_to_equity')
    if latest_dte is not None and latest_dte == 0:
        return None

    years_present = _consecutive_years_present(
        _get_year_values(data.financial_ratios, 'interest_coverage'), 1
    )

    confidence = _compute_confidence(
        latest_icr, 1.5, False, years_present, 1, 1, 1
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_6",
        text="Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
        confidence_pct=round(confidence, 2),
    )


def rule_con_7_dividend_payout_over_100(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_7: Dividend payout > 100%.

    Uses financial_ratios.dividend_payout_ratio_pct.
    """
    latest_dp = _get_latest_year_value(data.financial_ratios, 'dividend_payout_ratio_pct')
    if latest_dp is None or latest_dp <= 100:
        return None

    years_present = _consecutive_years_present(
        _get_year_values(data.financial_ratios, 'dividend_payout_ratio_pct'), 1
    )

    confidence = _compute_confidence(
        latest_dp, 100.0, True, years_present, 1, 1, 1
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_7",
        text="Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
        confidence_pct=round(confidence, 2),
    )


def rule_con_8_debt_to_equity_rising_3y(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_8: D/E rising for 3 consecutive years.

    Uses financial_ratios.debt_to_equity trend.
    """
    dte_values = _get_year_values(data.financial_ratios, 'debt_to_equity')
    valid_dte = [(i, v) for i, v in enumerate(dte_values) if v is not None]

    if len(valid_dte) < 3:
        return None

    for i in range(len(valid_dte) - 2):
        idx1, val1 = valid_dte[i]
        idx2, val2 = valid_dte[i + 1]
        idx3, val3 = valid_dte[i + 2]
        if val1 > val2 > val3:
            consecutive = 3
            while i + consecutive < len(valid_dte):
                idx_next, val_next = valid_dte[i + consecutive]
                idx_prev, val_prev = valid_dte[i + consecutive - 1]
                if val_prev < val_next:
                    consecutive += 1
                else:
                    break

            years_present = len(valid_dte)

            # For trend-based rules, confidence is based on data quality and
            # persistence of the trend, not the absolute metric value.
            confidence = 50.0
            confidence += _confidence_completeness(years_present, 3)
            confidence += _confidence_persistence(consecutive, 3)
            confidence = max(0.0, min(100.0, confidence))

            if confidence <= 60:
                return None

            return ProsConsSignal(
                company_id=data.company_id,
                type="con",
                rule_id="CON_8",
                text="Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                confidence_pct=round(confidence, 2),
            )

    return None


def rule_con_9_eps_declining_3y(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_9: EPS declining for 3 consecutive years.

    Uses profitandloss.eps.
    """
    eps_values = _get_year_values(data.pl_data, 'eps')
    valid_eps = [(i, v) for i, v in enumerate(eps_values) if v is not None]

    if len(valid_eps) < 3:
        return None

    for i in range(len(valid_eps) - 2):
        idx1, val1 = valid_eps[i]
        idx2, val2 = valid_eps[i + 1]
        idx3, val3 = valid_eps[i + 2]
        if val1 < val2 < val3:
            consecutive = 3
            while i + consecutive < len(valid_eps):
                idx_next, val_next = valid_eps[i + consecutive]
                idx_prev, val_prev = valid_eps[i + consecutive - 1]
                if val_prev > val_next:
                    consecutive += 1
                else:
                    break

            years_present = len(valid_eps)
            latest_eps = valid_eps[0][1]

            # Confidence is based on data completeness and persistence of decline
            # Since this is a trend-based rule, use a neutral margin (no penalty)
            confidence = 50.0
            confidence += _confidence_completeness(years_present, 3)
            confidence += _confidence_persistence(consecutive, 3)
            confidence = max(0.0, min(100.0, confidence))

            if confidence <= 60:
                return None

            return ProsConsSignal(
                company_id=data.company_id,
                type="con",
                rule_id="CON_9",
                text="Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                confidence_pct=round(confidence, 2),
            )

    return None


def rule_con_10_roce_low(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_10: ROCE < 10%.

    Uses companies.roce_percentage for latest, or compute from financial data.
    """
    latest_roce = _get_latest_year_value(data.financial_ratios, 'return_on_capital_employed_pct')
    if latest_roce is None or latest_roce >= 10:
        return None

    years_present = _consecutive_years_present(
        _get_year_values(data.financial_ratios, 'return_on_capital_employed_pct'), 1
    )

    confidence = _compute_confidence(
        latest_roce, 10.0, False, years_present, 1, 1, 1
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_10",
        text="Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
        confidence_pct=round(confidence, 2),
    )


def rule_con_11_net_debt_3x_ebitda(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_11: Net Debt > 3x EBITDA.

    Net Debt = borrowings - investments (from cashflow/balancesheet)
    EBITDA = operating_profit + depreciation (from P&L)
    """
    # Get latest balance sheet data for net debt
    latest_borrowings = _get_latest_year_value(data.bs_data, 'borrowings')
    latest_investments = _get_latest_year_value(data.bs_data, 'investments')
    latest_other_assets = _get_latest_year_value(data.bs_data, 'other_asset')

    # Approximate investments if not directly available
    if latest_investments is None and latest_other_assets is not None:
        latest_investments = latest_other_assets

    if latest_borrowings is None or latest_investments is None:
        return None

    net_debt_val = latest_borrowings - latest_investments
    if net_debt_val is None or net_debt_val <= 0:
        return None

    # Get EBITDA: operating_profit + depreciation
    latest_op = _get_latest_year_value(data.pl_data, 'operating_profit')
    latest_depr = _get_latest_year_value(data.pl_data, 'depreciation')

    if latest_op is None or latest_depr is None:
        return None

    ebitda = latest_op + latest_depr
    if ebitda is None or ebitda <= 0:
        return None

    debt_to_ebitda = net_debt_val / ebitda
    if debt_to_ebitda <= 3:
        return None

    years_present = min(
        _consecutive_years_present(_get_year_values(data.bs_data, 'borrowings'), 1),
        _consecutive_years_present(_get_year_values(data.pl_data, 'operating_profit'), 1),
    )

    confidence = _compute_confidence(
        debt_to_ebitda, 3.0, True, years_present, 1, 1, 1
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_11",
        text="Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
        confidence_pct=round(confidence, 2),
    )


def rule_con_12_revenue_cagr_under_5pct(data: CompanyData) -> Optional[ProsConsSignal]:
    """
    CON_12: Revenue CAGR < 5% over 5 years.
    """
    sales_values = _get_year_values(data.pl_data, 'sales')
    cagr = _compute_cagr_from_series(sales_values, 5)

    if cagr is None:
        return None
    if cagr >= 5:
        return None

    years_present = _consecutive_years_present(sales_values, 5)

    confidence = _compute_confidence(
        cagr, 5.0, False, years_present, 5, years_present, 5
    )

    if confidence <= 60:
        return None

    return ProsConsSignal(
        company_id=data.company_id,
        type="con",
        rule_id="CON_12",
        text="Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
        confidence_pct=round(confidence, 2),
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

PRO_RULES = [
    rule_pro_1_roe_sustained,
    rule_pro_2_fcf_positive_5y,
    rule_pro_3_de_ratio_zero,
    rule_pro_4_revenue_cagr_15pct,
    rule_pro_5_opm_25pct,
    rule_pro_6_pat_cagr_20pct,
    rule_pro_7_icr_high_or_debt_free,
    rule_pro_8_dividend_yield_and_fcf,
    rule_pro_9_eps_cagr_15pct,
    rule_pro_10_roe_improving_3y,
    rule_pro_11_revenue_cagr_gt_pat_cagr,
    rule_pro_12_assets_growing_declining_debt,
]

CON_RULES = [
    rule_con_1_debt_to_equity_high,
    rule_con_2_fcf_negative_3y,
    rule_con_3_opm_declining_3y,
    rule_con_4_net_profit_negative,
    rule_con_5_revenue_declining_2y,
    rule_con_6_icr_low,
    rule_con_7_dividend_payout_over_100,
    rule_con_8_debt_to_equity_rising_3y,
    rule_con_9_eps_declining_3y,
    rule_con_10_roce_low,
    rule_con_11_net_debt_3x_ebitda,
    rule_con_12_revenue_cagr_under_5pct,
]


def generate_signals_for_company(company_id: str) -> List[ProsConsSignal]:
    """Generate all qualifying pro and con signals for a single company."""
    data = load_company_data(company_id)
    signals = []

    for rule_fn in PRO_RULES:
        signal = rule_fn(data)
        if signal is not None:
            signals.append(signal)

    for rule_fn in CON_RULES:
        signal = rule_fn(data)
        if signal is not None:
            signals.append(signal)

    return signals


def generate_all_pros_cons() -> pd.DataFrame:
    """
    Generate pros/cons for all companies in the universe.

    Returns DataFrame with columns:
    company_id, type, rule_id, text, confidence_pct
    """
    companies = get_company_universe()
    all_signals = []

    for company in companies:
        company_id = company['company_id']
        signals = generate_signals_for_company(company_id)
        all_signals.extend(signals)

    # Create DataFrame
    df = pd.DataFrame([asdict(s) for s in all_signals])
    if df.empty:
        df = pd.DataFrame(columns=['company_id', 'type', 'rule_id', 'text', 'confidence_pct'])

    return df


def validate_company_coverage(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Validate that every company has at least 1 pro and 1 con.

    Returns dict of issues.
    """
    companies = get_company_list()
    all_company_ids = [c['company_id'] for c in companies]

    issues = {
        'companies_with_zero_pros': [],
        'companies_with_zero_cons': [],
        'companies_with_no_signals': [],
    }

    for cid in all_company_ids:
        company_signals = df[df['company_id'] == cid] if not df.empty else pd.DataFrame()
        pros = company_signals[company_signals['type'] == 'pro'] if not company_signals.empty else pd.DataFrame()
        cons = company_signals[company_signals['type'] == 'con'] if not company_signals.empty else pd.DataFrame()

        if len(company_signals) == 0:
            issues['companies_with_no_signals'].append(cid)
        if len(pros) == 0:
            issues['companies_with_zero_pros'].append(cid)
        if len(cons) == 0:
            issues['companies_with_zero_cons'].append(cid)

    return issues


def generate_output(output_path: str = 'Data/output/pros_cons_generated.csv') -> None:
    """Generate the output CSV file."""
    df = generate_all_pros_cons()

    # Ensure exact column order
    columns = ['company_id', 'type', 'rule_id', 'text', 'confidence_pct']
    if not df.empty:
        df = df[columns]

    # Write without index
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} signals for {df['company_id'].nunique() if not df.empty else 0} companies")

    # Validate coverage
    issues = validate_company_coverage(df)
    if issues['companies_with_zero_pros']:
        print(f"WARNING: Companies with zero pros: {len(issues['companies_with_zero_pros'])}")
    if issues['companies_with_zero_cons']:
        print(f"WARNING: Companies with zero cons: {len(issues['companies_with_zero_cons'])}")

    return df


if __name__ == '__main__':
    generate_output()
