"""Financial trends with revenue, profitability, margin, and CAGR analysis."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.cagr import calculate_cagr, cagr_grade
from src.dashboard.ui import (
    COLORS, apply_plotly_theme, format_currency, format_percentage,
    metric_grid, page_header, section_header,
)
from src.dashboard.utils.db import get_company_list, get_financial_trends


def render() -> None:
    page_header(
        "Financial trends",
        "Track revenue, earnings and margin development over time, with compound growth calculated from reported financial statements.",
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
            load = st.button("Load trends", type="primary", use_container_width=True)

    if not load:
        st.caption("Choose a company to analyze its historical financial trajectory.")
        return

    company_id = next(c["company_id"] for c in companies if c["company_name"] == selected)
    with st.spinner("Loading financial trends..."):
        trends = get_financial_trends(company_id)

    if trends is None or trends.empty:
        st.warning("No trend data available for this company.")
        return

    trends = trends.sort_values("year")
    latest = trends.iloc[-1]
    metric_grid([
        {"label": "Revenue", "value": format_currency(latest.get("sales")), "note": f"FY {latest.get('year', 'latest')}"},
        {"label": "Net profit", "value": format_currency(latest.get("net_profit")), "note": "Latest reported year"},
        {"label": "Net profit margin", "value": format_percentage(latest.get("net_profit_margin_pct")), "note": "Latest reported year"},
        {"label": "Return on equity", "value": format_percentage(latest.get("return_on_equity_pct")), "note": "Latest reported year"},
    ], columns=4)

    chart_col1, chart_col2 = st.columns(2, gap="large")

    with chart_col1:
        with st.container(border=True):
            section_header("Revenue and net profit")
            plot_df = trends[["year", "sales", "net_profit"]].rename(columns={
                "sales": "Revenue", "net_profit": "Net profit",
            })
            fig1 = px.line(
                plot_df, x="year", y=["Revenue", "Net profit"], markers=True,
                labels={"value": "₹ crore", "year": "Financial year", "variable": ""},
                color_discrete_map={"Revenue": COLORS["accent_primary"], "Net profit": COLORS["accent_success"]},
            )
            fig1.update_traces(line={"width": 2.5}, marker={"size": 6})
            apply_plotly_theme(fig1, height=360, legend={"orientation": "h", "y": 1.12, "x": 0})
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with chart_col2:
        with st.container(border=True):
            section_header("Margin development")
            margins = ["net_profit_margin_pct", "operating_profit_margin_pct"]
            available_margins = [m for m in margins if m in trends.columns]
            if available_margins:
                margin_df = trends[["year", *available_margins]].rename(columns={
                    "net_profit_margin_pct": "Net margin",
                    "operating_profit_margin_pct": "Operating margin",
                })
                margin_names = ["Net margin" if m == "net_profit_margin_pct" else "Operating margin" for m in available_margins]
                fig2 = px.line(
                    margin_df, x="year", y=margin_names, markers=True,
                    labels={"value": "Margin (%)", "year": "Financial year", "variable": ""},
                    color_discrete_sequence=[COLORS["accent_primary"], "#14B8A6"],
                )
                fig2.update_traces(line={"width": 2.5}, marker={"size": 6})
                apply_plotly_theme(fig2, height=360, legend={"orientation": "h", "y": 1.12, "x": 0})
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Margin data not available.")

    if len(trends) >= 3:
        first = trends.iloc[0]
        last = trends.iloc[-1]
        years = int(last["year"] - first["year"])
        rev_cagr = calculate_cagr(first["sales"], last["sales"], years)
        prof_cagr = calculate_cagr(first["net_profit"], last["net_profit"], years)

        section_header("Compound annual growth")
        metric_grid([
            {"label": "Revenue CAGR", "value": format_percentage(rev_cagr), "note": f"Grade: {cagr_grade(rev_cagr) if rev_cagr else 'N/A'}"},
            {"label": "Profit CAGR", "value": format_percentage(prof_cagr), "note": f"Grade: {cagr_grade(prof_cagr) if prof_cagr else 'N/A'}"},
            {"label": "Measurement period", "value": f"{years} years", "note": f"FY {first['year']} to FY {last['year']}"},
        ], columns=3)

    section_header("Historical financial data")
    display_cols = [
        "year", "sales", "net_profit", "operating_profit", "net_profit_margin_pct",
        "operating_profit_margin_pct", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
    ]
    available = [c for c in display_cols if c in trends.columns]
    st.dataframe(
        trends[available].sort_values("year", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "year": st.column_config.NumberColumn("Year", format="%d"),
            "sales": st.column_config.NumberColumn("Revenue (₹Cr)", format="%.1f"),
            "net_profit": st.column_config.NumberColumn("Net profit (₹Cr)", format="%.1f"),
            "operating_profit": st.column_config.NumberColumn("Operating profit (₹Cr)", format="%.1f"),
            "net_profit_margin_pct": st.column_config.NumberColumn("Net margin %", format="%.2f"),
            "operating_profit_margin_pct": st.column_config.NumberColumn("Operating margin %", format="%.2f"),
            "return_on_equity_pct": st.column_config.NumberColumn("ROE %", format="%.2f"),
            "debt_to_equity": st.column_config.NumberColumn("Debt / equity", format="%.2f"),
            "free_cash_flow_cr": st.column_config.NumberColumn("Free cash flow (₹Cr)", format="%.1f"),
        },
    )


if __name__ == "__main__":
    render()
