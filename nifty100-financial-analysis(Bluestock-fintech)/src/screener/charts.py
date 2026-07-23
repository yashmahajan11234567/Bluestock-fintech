"""Radar Chart Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module provides functions to create radar (spider) charts comparing a
selected company against its peer-group average using the percentile metrics
computed by ``src.screener.peer``.

Functions
==========
* ``create_radar_chart(values_dict, categories)`` – low-level helper that
  creates a matplotlib Figure with a single radar axis.
* ``create_peer_radar_chart(company_id)`` – high-level wrapper that loads the
  screener data, computes peer percentiles, and produces a radar chart
  comparing the company to its peer-group average.
* ``save_radar_chart(fig, company_id, output_dir)`` – saves the figure to
  ``<company_id>_radar.png`` under the specified directory (defaults to
  ``Data/output/charts/``).

All functions are pure – they do not mutate global state and rely only on the
public APIs of ``engine`` and ``peer``.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Low-level radar chart primitive
# ---------------------------------------------------------------------------

def create_radar_chart(
    values_dict: Dict[str, float],
    categories: List[str],
    title: str = "Radar Chart",
    label_company: str = "Company",
    label_peer_avg: str = "Peer Average",
) -> plt.Figure:
    """Create a radar (spider) chart comparing two series.

    Parameters
    ----------
    values_dict : dict
        Mapping of category name to a tuple ``(company_value, peer_avg_value)``.
        Values are expected to be in the range 0–100 (percentiles).
    categories : list[str]
        Ordered list of category names defining axes order.
    title : str
        Chart title.
    label_company : str
        Legend label for the company polygon.
    label_peer_avg : str
        Legend label for the peer-average polygon.

    Returns
    -------
    matplotlib.figure.Figure
        The created figure (caller is responsible for closing/saving).
    """
    # Filter to categories that have at least one non-NaN value
    available_cats = [
        c for c in categories
        if c in values_dict and (
            not np.isnan(values_dict[c][0]) or not np.isnan(values_dict[c][1])
        )
    ]
    if not available_cats:
        raise ValueError("No valid categories with data to plot")

    N = len(available_cats)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the loop

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Company series
    company_vals = [values_dict[c][0] for c in available_cats]
    company_vals = [0 if np.isnan(v) else v for v in company_vals]
    company_vals += company_vals[:1]

    # Peer average series
    peer_vals = [values_dict[c][1] for c in available_cats]
    peer_vals = [0 if np.isnan(v) else v for v in peer_vals]
    peer_vals += peer_vals[:1]

    # Plot
    ax.plot(angles, company_vals, "o-", linewidth=2, label=label_company, color="#1f77b4")
    ax.fill(angles, company_vals, alpha=0.15, color="#1f77b4")

    ax.plot(angles, peer_vals, "s-", linewidth=2, label=label_peer_avg, color="#ff7f0e")
    ax.fill(angles, peer_vals, alpha=0.15, color="#ff7f0e")

    # Axes & labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(available_cats, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.5)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)

    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# High-level wrapper using peer module
# ---------------------------------------------------------------------------

# Metric display names aligned with percentile column names from peer.py
RADAR_METRICS = [
    ("roe_percentile", "ROE"),
    ("net_profit_margin_percentile", "Net Profit Margin"),
    ("revenue_cagr_percentile", "Revenue CAGR"),
    ("pat_cagr_percentile", "PAT CAGR"),
    ("free_cash_flow_percentile", "Free Cash Flow"),
    ("debt_to_equity_percentile", "Debt-to-Equity"),
    ("pe_percentile", "PE"),
    ("pb_percentile", "PB"),
]


def create_peer_radar_chart(company_id: str) -> plt.Figure:
    """Create a radar chart comparing ``company_id`` to its peer-group average.

    Steps
    -----
    1. Load screener data via ``engine.load_screener_data()``.
    2. Compute percentiles via ``peer.compute_peer_percentiles()``.
    3. Extract the company's row and the peer-group average for each metric.
    4. Call ``create_radar_chart()`` with the paired values.

    Parameters
    ----------
    company_id : str
        Company identifier as used in the screener data.

    Returns
    -------
    matplotlib.figure.Figure
        The radar chart figure.

    Raises
    ------
    ValueError
        If the company is not found or has no peer group assigned.
    """
    # Local imports to avoid circular dependency at module load time
    from .engine import load_screener_data
    from .peer import compute_peer_percentiles

    # Load & compute percentiles
    df = load_screener_data()
    df_pct = compute_peer_percentiles(df)

    # Find the company row
    company_row = df_pct[df_pct["company_id"] == company_id]
    if company_row.empty:
        raise ValueError(f"Company '{company_id}' not found in screener data")
    company_row = company_row.iloc[0]

    # Peer group name
    peer_group = company_row.get("peer_group_name")
    if pd.isna(peer_group):
        raise ValueError(f"Company '{company_id}' has no peer group assigned")

    # Peer group average percentiles (excluding the company itself)
    peer_mask = (df_pct["peer_group_name"] == peer_group) & (df_pct["company_id"] != company_id)
    peer_group_df = df_pct[peer_mask]

    # Build values dict
    values = {}
    for pct_col, display_name in RADAR_METRICS:
        if pct_col not in df_pct.columns:
            continue
        company_val = company_row.get(pct_col, np.nan)
        peer_avg = peer_group_df[pct_col].mean() if not peer_group_df.empty else np.nan
        values[display_name] = (company_val, peer_avg)

    # Default categories order (only those with at least one side present)
    categories = [d for _, d in RADAR_METRICS if d in values]

    title = f"{company_id} vs {peer_group} Average – Percentile Comparison"
    return create_radar_chart(
        values_dict=values,
        categories=categories,
        title=title,
        label_company=company_id,
        label_peer_avg=f"{peer_group} Avg",
    )


def save_radar_chart(
    fig: plt.Figure,
    company_id: str,
    output_dir: Optional[str] = None,
) -> str:
    """Save a radar chart figure to disk.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure returned by ``create_radar_chart`` or ``create_peer_radar_chart``.
    company_id : str
        Used to construct the filename ``<company_id>_radar.png``.
    output_dir : str, optional
        Target directory. Defaults to ``Data/output/charts/`` relative to this
        module.

    Returns
    -------
    str
        Absolute path of the saved file.
    """
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "Data", "output", "charts"
        )
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{company_id}_radar.png"
    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return os.path.abspath(filepath)


__all__ = [
    "create_radar_chart",
    "create_peer_radar_chart",
    "save_radar_chart",
]
