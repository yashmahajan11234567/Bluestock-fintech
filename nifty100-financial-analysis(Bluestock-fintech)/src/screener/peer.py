"""Peer Percentile Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~
This module provides utilities to compute percentile rankings of companies
within their peer groups and an aggregated *overall peer score*.

The implementation works on the screener data produced by ``src.screener.engine``
and a ``peer_groups.xlsx`` file located in ``Data/raw``.  No existing screener
APIs are modified – the functions are self‑contained and can be imported
independently.

Key functions
==============
* ``load_peer_groups()`` – reads ``peer_groups.xlsx`` and returns a DataFrame
  with ``company_id`` and ``peer_group_name`` columns.
* ``compute_peer_percentiles(df)`` – merges the peer groups into the supplied
  screener DataFrame and adds percentile columns for the metrics required by
  the specification.  Percentiles are in the range 0‑100; higher is better for
  all metrics except PE, PB and Debt‑to‑Equity where lower values receive a
  higher percentile.
* ``compare_company_to_peers(company_id)`` – convenience wrapper that loads the
  screener data, computes the percentiles and returns a single‑row DataFrame for
  the requested company, including an ``overall_peer_score`` column.

The module is deliberately pure – it does not mutate the original DataFrames
and uses only pandas operations that are well‑tested.
"""

from __future__ import annotations

# Reuse the CAGR parsing helper so it stays in sync with the screener engine.
from .engine import _parse_cagr_strings

import os
from typing import List

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper constants
# ---------------------------------------------------------------------------

# Mapping of metric column names in the screener output to a readable percentile
# column name.  The keys must exist in the screener DataFrame; missing columns are
# ignored gracefully.
METRIC_PERCENTILE_MAP = {
    "return_on_equity_pct": "roe_percentile",
    "net_profit_margin_pct": "net_profit_margin_percentile",
    "compounded_sales_growth": "revenue_cagr_percentile",
    "compounded_profit_growth": "pat_cagr_percentile",
    "debt_to_equity": "debt_to_equity_percentile",
    "pe_ratio": "pe_percentile",
    "pb_ratio": "pb_percentile",
    "dividend_yield_pct": "dividend_yield_percentile",
    "free_cash_flow_cr": "free_cash_flow_percentile",
}

# Metrics where a *lower* absolute value is better.  For these we invert the
# percentile (e.g. 0 -> 100, 50 -> 50, 100 -> 0).
LOWER_BETTER = {"pe_percentile", "pb_percentile", "debt_to_equity_percentile"}

# Category definitions used to compute the weighted overall score.
CATEGORY_WEIGHTS = {
    "profitability": 0.35,  # ROE + Net Profit Margin
    "growth": 0.25,        # Revenue CAGR + PAT CAGR
    "cash_quality": 0.20,  # Free Cash Flow + Dividend Yield
    "valuation": 0.10,    # PE + PB
    "leverage": 0.10,      # Debt to Equity
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_peer_groups() -> pd.DataFrame:
    """Load the ``peer_groups.xlsx`` file.

    The file is expected to be located at ``../Data/raw/peer_groups.xlsx``
    relative to this module's directory (mirroring the layout used by the
    screener engine).

    Returns
    -------
    pandas.DataFrame
        Columns ``company_id`` and ``peer_group_name``.
    """
    base_path = os.path.join(os.path.dirname(__file__), "..", "..", "Data", "raw")
    peer_path = os.path.join(base_path, "peer_groups.xlsx")
    # ``engine`` uses the default ``header=0`` for this sheet; the source sheet
    # contains the two required columns.
    peer_df = pd.read_excel(peer_path, dtype={"company_id": object})
    # Ensure the expected column names exist – if the source uses a different
    # casing we normalise them.
    expected = {"company_id", "peer_group_name"}
    missing = expected - set(peer_df.columns.str.lower())
    if missing:
        raise KeyError(f"peer_groups.xlsx is missing columns: {missing}")
    # Standardise column names.
    peer_df = peer_df.rename(columns=lambda c: c.strip().lower())
    return peer_df[["company_id", "peer_group_name"]]


def _percentile_series(series: pd.Series, higher_is_better: bool) -> pd.Series:
    """Return a 0‑100 percentile series for *series* within its group.

    Parameters
    ----------
    series : pd.Series
        Numeric series (may contain NaN).  NaN values are propagated.
    higher_is_better : bool
        If ``True`` higher values map to higher percentiles.  If ``False`` the
        mapping is inverted.
    """
    # ``rank(pct=True)`` returns values in the (0, 1] interval where the minimum
    # non‑NaN gets 1/n, the maximum gets 1.  Multiplying by 100 yields 0‑100.
    pct = series.rank(method="average", pct=True, na_option="keep") * 100
    if not higher_is_better:
        pct = 100 - pct
    return pct


def compute_peer_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """Compute percentile rankings for each company within its peer group.

    The function merges the peer‑group information, calculates the required
    percentiles and adds an ``overall_peer_score`` column (weighted average).

    Parameters
    ----------
    df : pandas.DataFrame
        Screener data (as returned by ``engine.load_screener_data``).

    Returns
    -------
    pandas.DataFrame
        The original columns plus ``peer_group_name``, the percentile columns
        defined in :data:`METRIC_PERCENTILE_MAP` and ``overall_peer_score``.
    """
    # Ensure CAGR columns are numeric (they may come as strings like "10 Years: 21%").
    merged = _parse_cagr_strings(df)

    # Merge peer group names.
    peer_df = load_peer_groups()
    merged = merged.merge(peer_df, on="company_id", how="left")

    # Compute percentiles per peer group.
    for metric_col, perc_col in METRIC_PERCENTILE_MAP.items():
        if metric_col not in merged.columns:
            # Skip missing metrics – they will simply not be present in the final
            # dataframe.  This mirrors the behaviour of the existing screener.
            continue
        higher_is_better = perc_col not in LOWER_BETTER
        merged[perc_col] = (
            merged.groupby("peer_group_name", dropna=False)[metric_col]
            .transform(lambda s: _percentile_series(s, higher_is_better))
        )

    # ---------------------------------------------------------------------
    # Overall peer score – weighted average of category scores.
    # ---------------------------------------------------------------------
    # Helper to safely compute the mean of a list of columns that may be missing.
    def _category_score(cols: List[str]) -> pd.Series:
        available = [c for c in cols if c in merged.columns]
        if not available:
            return pd.Series(np.nan, index=merged.index)
        return merged[available].mean(axis=1)

    # Build category scores and track which are available per row.
    profitability_score = _category_score([
        METRIC_PERCENTILE_MAP.get("return_on_equity_pct"),
        METRIC_PERCENTILE_MAP.get("net_profit_margin_pct"),
    ])
    growth_score = _category_score([
        METRIC_PERCENTILE_MAP.get("compounded_sales_growth"),
        METRIC_PERCENTILE_MAP.get("compounded_profit_growth"),
    ])
    cash_quality_score = _category_score([
        METRIC_PERCENTILE_MAP.get("free_cash_flow_cr"),
        METRIC_PERCENTILE_MAP.get("dividend_yield_pct"),
    ])
    valuation_score = _category_score([
        METRIC_PERCENTILE_MAP.get("pe_ratio"),
        METRIC_PERCENTILE_MAP.get("pb_ratio"),
    ])
    leverage_score = _category_score([
        METRIC_PERCENTILE_MAP.get("debt_to_equity"),
    ])

    # Compute weighted overall score, renormalising weights for missing categories.
    # We do this row-by-row because NaN availability can differ across companies.
    cat_scores = pd.DataFrame({
        "profitability": profitability_score,
        "growth": growth_score,
        "cash_quality": cash_quality_score,
        "valuation": valuation_score,
        "leverage": leverage_score,
    })

    def _weighted_score(row: pd.Series) -> float:
        available = row.dropna()
        if available.empty:
            return np.nan
        total_w = sum(CATEGORY_WEIGHTS[c] for c in available.index)
        if total_w == 0:
            return np.nan
        # Normalised weights
        norm_weights = {c: CATEGORY_WEIGHTS[c] / total_w for c in available.index}
        return sum(available[c] * norm_weights[c] for c in available.index)

    merged["overall_peer_score"] = cat_scores.apply(_weighted_score, axis=1)

    return merged


def compare_company_to_peers(company_id: str) -> pd.DataFrame:
    """Convenience wrapper to obtain percentile data for a single company.

    Parameters
    ----------
    company_id : str
        The identifier used in the screener data.

    Returns
    -------
    pandas.DataFrame
        A single‑row DataFrame containing ``company_id``, ``peer_group_name``,
        all percentile columns and ``overall_peer_score``.
    """
    # Import locally to avoid circular imports when the module is used on its own.
    from .engine import load_screener_data

    screener_df = load_screener_data()
    df_with_percentiles = compute_peer_percentiles(screener_df)
    result = df_with_percentiles[df_with_percentiles["company_id"] == company_id]
    # Return a copy to keep the caller safe from accidental modifications.
    return result.copy()


__all__ = [
    "load_peer_groups",
    "compute_peer_percentiles",
    "compare_company_to_peers",
]
