"""Capital allocation efficiency using ROE, ROCE, and cash conversion."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.capital_allocation import (
    capital_allocation_category, capital_score, is_capital_efficient, needs_capital_review,
)
from src.dashboard.ui import (
    COLORS, apply_plotly_theme, format_number, format_percentage,
    metric_grid, page_header, section_header,
)
from src.dashboard.utils.db import get_capital_alloc_data, get_company_list


def render() -> None:
    page_header(
        "Capital allocation",
        "Evaluate how effectively a company turns invested capital into returns and converts accounting profit into operating cash.",
    )

    companies = get_company_list()
    if not companies:
        st.error("No companies found.")
        return

    with st.container(border=True):
        select_col, action_col = st.columns([3, 1], gap="large")
        company_names = [c["company_name"] for c in companies]
        with select_col:
            selected = st.selectbox("Company", company_names)
        with action_col:
            st.markdown('<div style="height:27px"></div>', unsafe_allow_html=True)
            analyze = st.button("Assess allocation", type="primary", use_container_width=True)

    if not analyze:
        st.caption("Choose a company to assess its capital efficiency and historical allocation category.")
        return

    company_id = next(c["company_id"] for c in companies if c["company_name"] == selected)
    with st.spinner("Loading capital allocation data..."):
        data = get_capital_alloc_data(company_id)

    if data is None or data.empty:
        st.warning("No capital allocation data available.")
        return

    latest = data.sort_values("year", ascending=False).iloc[0]
    roe = latest.get("return_on_equity_pct")
    roce = latest.get("return_on_capital_employed_pct")
    ccr = latest.get("cash_conversion_ratio")

    category = capital_allocation_category(roe, roce, ccr)
    score = capital_score(category)
    efficient = is_capital_efficient(category)
    review = needs_capital_review(category)

    metric_grid([
        {"label": "Allocation category", "value": category or "N/A", "note": "Latest financial year"},
        {"label": "Capital score", "value": f"{score} / 5", "note": "Composite allocation rating"},
        {"label": "Capital efficient", "value": "Yes" if efficient else "No", "note": "Based on current category", "tone": "positive" if efficient else "negative"},
        {"label": "Review required", "value": "Yes" if review else "No", "note": "Allocation risk flag", "tone": "negative" if review else "positive"},
    ], columns=4)

    section_header("Latest financial inputs")
    metric_grid([
        {"label": "Return on equity", "value": format_percentage(roe), "note": "Net profit relative to equity"},
        {"label": "Return on capital employed", "value": format_percentage(roce), "note": "Returns across total capital"},
        {"label": "Cash conversion ratio", "value": format_number(ccr) + "x", "note": "Operating cash flow / net profit"},
    ], columns=3)

    if "year" in data.columns and category:
        data = data.copy()
        data["category"] = data.apply(
            lambda row: capital_allocation_category(
                row.get("return_on_equity_pct"),
                row.get("return_on_capital_employed_pct"),
                row.get("cash_conversion_ratio"),
            ),
            axis=1,
        )
        category_order = ["Excellent", "Good", "Average", "Weak", "Poor"]
        data["category_rank"] = data["category"].map({c: i for i, c in enumerate(category_order)})

        with st.container(border=True):
            section_header("Allocation category over time")
            fig = px.line(
                data.sort_values("year"), x="year", y="category_rank", markers=True,
                labels={"year": "Financial year", "category_rank": "Category"},
                color_discrete_sequence=[COLORS["accent_primary"]],
            )
            fig.update_yaxes(tickvals=list(range(len(category_order))), ticktext=category_order)
            fig.update_traces(line={"width": 2.5}, marker={"size": 8})
            apply_plotly_theme(fig, height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    section_header("Reference sector comparison")
    sector_comparison = get_sector_capital_alloc_comparison(data)
    if sector_comparison is not None:
        st.dataframe(
            sector_comparison,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sector": st.column_config.TextColumn("Sector", width="large"),
                "Avg ROE %": st.column_config.NumberColumn("Avg ROE %", format="%.1f"),
                "Avg ROCE %": st.column_config.NumberColumn("Avg ROCE %", format="%.1f"),
                "Avg CCR": st.column_config.NumberColumn("Avg cash conversion", format="%.2f"),
            },
        )


def get_sector_capital_alloc_comparison(company_data: pd.DataFrame) -> pd.DataFrame | None:
    """Return the existing sector reference table."""
    return pd.DataFrame({
        "Sector": ["Technology", "Financials", "Consumer", "Industrial", "Healthcare"],
        "Avg ROE %": [18.5, 15.2, 14.8, 16.3, 22.1],
        "Avg ROCE %": [19.2, 14.8, 15.5, 17.1, 23.4],
        "Avg CCR": [1.15, 0.95, 1.05, 1.08, 1.25],
    })


if __name__ == "__main__":
    render()
