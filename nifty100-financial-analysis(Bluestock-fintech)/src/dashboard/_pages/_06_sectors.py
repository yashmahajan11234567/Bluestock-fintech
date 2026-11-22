"""Sector-level aggregates, comparisons, and leaderboards."""

import plotly.express as px
import streamlit as st

from src.dashboard.ui import (
    COLORS, apply_plotly_theme, format_currency, format_percentage,
    metric_grid, page_header, section_header,
)
from src.dashboard.utils.db import get_sector_aggregates, get_sectors_list


def _bar_chart(data, metric: str, title: str, color: str, ascending: bool = False):
    ordered = data.sort_values(metric, ascending=ascending)
    fig = px.bar(
        ordered,
        x=metric,
        y="sector",
        orientation="h",
        labels={metric: title, "sector": ""},
        color_discrete_sequence=[color],
        text_auto=".1f",
    )
    fig.update_traces(
        textposition="outside",
        textfont={"family": "Inter", "size": 10, "color": "#64748B"},
        marker={"line": {"width": 0}},
        hovertemplate="%{y}<br>%{x:.2f}<extra></extra>",
    )
    apply_plotly_theme(fig, height=390, showlegend=False, margin={"l": 10, "r": 50, "t": 20, "b": 40})
    return fig


def render() -> None:
    page_header(
        "Sector analysis",
        "Compare sector economics across profitability, leverage and valuation, and identify the strongest industry groups.",
    )

    sectors = get_sectors_list()
    if not sectors:
        st.error("No sectors found.")
        return

    with st.spinner("Loading sector data..."):
        sector_data = get_sector_aggregates()

    if sector_data is None or sector_data.empty:
        st.warning("No sector aggregate data available.")
        return

    total_companies = int(sector_data["company_count"].sum()) if "company_count" in sector_data else 0
    total_market_cap = sector_data["total_market_cap_cr"].sum() if "total_market_cap_cr" in sector_data else None
    top_roe = sector_data.loc[sector_data["avg_roe_pct"].idxmax(), "sector"] if "avg_roe_pct" in sector_data else "N/A"

    metric_grid([
        {"label": "Sector groups", "value": str(len(sector_data)), "note": "With reported financials"},
        {"label": "Companies represented", "value": str(total_companies), "note": "Across sector aggregates"},
        {"label": "Combined market cap", "value": format_currency(total_market_cap), "note": "Latest reported year"},
        {"label": "Highest average ROE", "value": top_roe, "note": "Leading sector by profitability"},
    ], columns=4)

    section_header("Sector overview")
    st.dataframe(
        sector_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "sector": st.column_config.TextColumn("Sector", width="large"),
            "company_count": st.column_config.NumberColumn("Companies", format="%d"),
            "avg_roe_pct": st.column_config.NumberColumn("Avg ROE %", format="%.1f"),
            "avg_roce_pct": st.column_config.NumberColumn("Avg ROCE %", format="%.1f"),
            "avg_debt_to_equity": st.column_config.NumberColumn("Avg debt / equity", format="%.2f"),
            "avg_net_profit_margin_pct": st.column_config.NumberColumn("Avg net margin %", format="%.1f"),
            "avg_pe_ratio": st.column_config.NumberColumn("Avg P/E", format="%.1f"),
            "total_market_cap_cr": st.column_config.NumberColumn("Market cap (₹Cr)", format="%.0f"),
        },
    )

    tab1, tab2, tab3 = st.tabs(["Profitability", "Leverage and valuation", "Sector leaders"])

    with tab1:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            with st.container(border=True):
                section_header("Average ROE by sector")
                if "avg_roe_pct" in sector_data:
                    data = sector_data.nlargest(10, "avg_roe_pct").sort_values("avg_roe_pct")
                    st.plotly_chart(_bar_chart(data, "avg_roe_pct", "ROE (%)", COLORS["accent_primary"]), use_container_width=True, config={"displayModeBar": False})
        with col2:
            with st.container(border=True):
                section_header("Average ROCE by sector")
                if "avg_roce_pct" in sector_data:
                    data = sector_data.nlargest(10, "avg_roce_pct").sort_values("avg_roce_pct")
                    st.plotly_chart(_bar_chart(data, "avg_roce_pct", "ROCE (%)", "#14B8A6"), use_container_width=True, config={"displayModeBar": False})

    with tab2:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            with st.container(border=True):
                section_header("Highest debt-to-equity")
                if "avg_debt_to_equity" in sector_data:
                    data = sector_data.nlargest(10, "avg_debt_to_equity").sort_values("avg_debt_to_equity")
                    st.plotly_chart(_bar_chart(data, "avg_debt_to_equity", "Debt / equity", "#D97706"), use_container_width=True, config={"displayModeBar": False})
        with col2:
            with st.container(border=True):
                section_header("Average P/E by sector")
                if "avg_pe_ratio" in sector_data:
                    data = sector_data.nlargest(10, "avg_pe_ratio").sort_values("avg_pe_ratio")
                    st.plotly_chart(_bar_chart(data, "avg_pe_ratio", "P/E ratio", "#8B5CF6"), use_container_width=True, config={"displayModeBar": False})

    with tab3:
        with st.container(border=True):
            section_header("Sector leaderboard")
            metric = st.selectbox(
                "Ranking metric",
                ["avg_roe_pct", "avg_roce_pct", "avg_net_profit_margin_pct", "avg_debt_to_equity", "avg_pe_ratio", "total_market_cap_cr"],
                format_func=lambda x: x.replace("avg_", "").replace("_pct", " %").replace("_", " ").title(),
            )
            if metric in sector_data:
                ascending = metric in ["avg_debt_to_equity", "avg_pe_ratio"]
                leaders = sector_data.sort_values(metric, ascending=ascending).head(5)
                st.dataframe(
                    leaders[["sector", metric, "company_count", "total_market_cap_cr"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "sector": st.column_config.TextColumn("Sector", width="large"),
                        metric: st.column_config.NumberColumn("Ranking value", format="%.2f"),
                        "company_count": st.column_config.NumberColumn("Companies", format="%d"),
                        "total_market_cap_cr": st.column_config.NumberColumn("Market cap (₹Cr)", format="%.0f"),
                    },
                )


if __name__ == "__main__":
    render()
