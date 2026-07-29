"""
Sector Analysis page - Sector-level aggregates, heatmaps, and leaderboards.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_sectors_list, get_sector_aggregates


def render() -> None:
    """Render the Sector Analysis page."""
    st.title("🏭 Sector Analysis")
    st.markdown("Analyze sector-level aggregates, compare sectors, and find sector leaders.")

    sectors = get_sectors_list()
    if not sectors:
        st.error("No sectors found.")
        return

    with st.spinner("Loading sector data..."):
        sector_data = get_sector_aggregates()

    if sector_data is None or sector_data.empty:
        st.warning("No sector aggregate data available.")
        return

    st.success(f"Loaded {len(sector_data)} sectors")

    # Sector overview table
    st.subheader("📊 Sector Overview")
    st.dataframe(
        sector_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "avg_roe_pct": st.column_config.NumberColumn("Avg ROE %", format="%.1f"),
            "avg_roce_pct": st.column_config.NumberColumn("Avg ROCE %", format="%.1f"),
            "avg_debt_to_equity": st.column_config.NumberColumn("Avg D/E", format="%.2f"),
            "avg_net_profit_margin_pct": st.column_config.NumberColumn("Avg NPM %", format="%.1f"),
            "total_market_cap_cr": st.column_config.NumberColumn("Total M.Cap (₹Cr)", format="₹%,.0f"),
            "company_count": st.column_config.NumberColumn("Companies", format="%d"),
        }
    )

    st.markdown("---")

    # Sector comparison charts
    tab1, tab2, tab3 = st.tabs(["📈 Profitability", "💰 Leverage & Valuation", "🏆 Leaders"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            if "avg_roe_pct" in sector_data.columns:
                fig = px.bar(
                    sector_data.sort_values("avg_roe_pct", ascending=True).tail(10),
                    x="avg_roe_pct", y="sector", orientation="h",
                    title="Top 10 Sectors by Average ROE",
                    labels={"avg_roe_pct": "ROE %", "sector": "Sector"}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "avg_roce_pct" in sector_data.columns:
                fig = px.bar(
                    sector_data.sort_values("avg_roce_pct", ascending=True).tail(10),
                    x="avg_roce_pct", y="sector", orientation="h",
                    title="Top 10 Sectors by Average ROCE",
                    labels={"avg_roce_pct": "ROCE %", "sector": "Sector"}
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            if "avg_debt_to_equity" in sector_data.columns:
                fig = px.bar(
                    sector_data.sort_values("avg_debt_to_equity", ascending=False).head(10),
                    x="avg_debt_to_equity", y="sector", orientation="h",
                    title="Top 10 Sectors by Average D/E (Highest Leverage)",
                    labels={"avg_debt_to_equity": "D/E Ratio", "sector": "Sector"}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "avg_pe_ratio" in sector_data.columns:
                fig = px.bar(
                    sector_data.sort_values("avg_pe_ratio", ascending=True).tail(10),
                    x="avg_pe_ratio", y="sector", orientation="h",
                    title="Top 10 Sectors by Average P/E",
                    labels={"avg_pe_ratio": "P/E Ratio", "sector": "Sector"}
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("🏆 Sector Leaders")
        metric = st.selectbox("Select Metric", [
            "avg_roe_pct", "avg_roce_pct", "avg_net_profit_margin_pct",
            "avg_debt_to_equity", "avg_pe_ratio", "total_market_cap_cr"
        ])
        if metric in sector_data.columns:
            ascending = metric in ["avg_debt_to_equity", "avg_pe_ratio"]
            leaders = sector_data.sort_values(metric, ascending=ascending).head(5)
            st.dataframe(
                leaders[["sector", metric, "company_count", "total_market_cap_cr"]],
                use_container_width=True,
                hide_index=True
            )


if __name__ == "__main__":
    render()