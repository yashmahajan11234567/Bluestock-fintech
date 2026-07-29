"""
Financial Trends page - Revenue, profit, margin trends over years.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_company_list, get_financial_trends
from src.screener.engine import load_screener_data


def render() -> None:
    """Render the Financial Trends page."""
    st.title("📈 Financial Trends")
    st.markdown("Track revenue, profit, and margin trends over time for Nifty 100 companies.")

    # Company selector
    companies = get_company_list()
    if not companies:
        st.error("No companies found.")
        return

    company_names = [c["company_name"] for c in companies]
    selected = st.selectbox("Select Company", company_names)

    if st.button("Load Trends", type="primary"):
        company_id = next(c["company_id"] for c in companies if c["company_name"] == selected)

        with st.spinner("Loading financial trends..."):
            trends = get_financial_trends(company_id)

        if trends is None or trends.empty:
            st.warning("No trend data available for this company.")
            return

        st.success(f"Displaying trends for **{selected}**")

        # Key metrics cards
        latest = trends.sort_values("year", ascending=False).iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Latest Revenue", f"₹{latest.get('sales', 0):,.0f} Cr")
        with col2:
            st.metric("Latest Net Profit", f"₹{latest.get('net_profit', 0):,.0f} Cr")
        with col3:
            npm = latest.get('net_profit_margin_pct')
            st.metric("Net Profit Margin", f"{npm:.1f}%" if pd.notna(npm) else "N/A")
        with col4:
            roe = latest.get('return_on_equity_pct')
            st.metric("ROE", f"{roe:.1f}%" if pd.notna(roe) else "N/A")

        st.markdown("---")

        # Revenue & Profit trend
        st.subheader("💰 Revenue & Profit Trend")
        fig1 = px.line(
            trends, x="year", y=["sales", "net_profit"],
            title="Revenue vs Net Profit Over Time",
            labels={"value": "₹ Crores", "year": "Year", "variable": "Metric"},
            color_discrete_map={"sales": "#1f77b4", "net_profit": "#2ca02c"}
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Margins trend
        st.subheader("📊 Margin Trends")
        margins = ["net_profit_margin_pct", "operating_profit_margin_pct"]
        available_margins = [m for m in margins if m in trends.columns]
        if available_margins:
            fig2 = px.line(
                trends, x="year", y=available_margins,
                title="Profit Margins Over Time",
                labels={"value": "Percentage (%)", "year": "Year"},
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Margin data not available")

        # CAGR calculations
        st.subheader("📐 Compound Annual Growth Rates")
        if len(trends) >= 3:
            from src.analytics.cagr import calculate_cagr, cagr_grade

            first = trends.sort_values("year").iloc[0]
            last = trends.sort_values("year").iloc[-1]
            years = int(last["year"] - first["year"])

            rev_cagr = calculate_cagr(first["sales"], last["sales"], years)
            prof_cagr = calculate_cagr(first["net_profit"], last["net_profit"], years)

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Revenue CAGR", f"{rev_cagr:.1f}%" if rev_cagr else "N/A")
                if rev_cagr:
                    st.caption(f"Grade: {cagr_grade(rev_cagr)}")
            with c2:
                st.metric("Profit CAGR", f"{prof_cagr:.1f}%" if prof_cagr else "N/A")
                if prof_cagr:
                    st.caption(f"Grade: {cagr_grade(prof_cagr)}")

        # Raw data table
        st.markdown("---")
        st.subheader("📋 Raw Data")
        display_cols = ["year", "sales", "net_profit", "operating_profit",
                       "net_profit_margin_pct", "operating_profit_margin_pct",
                       "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr"]
        available = [c for c in display_cols if c in trends.columns]
        st.dataframe(
            trends[available].sort_values("year", ascending=False),
            use_container_width=True,
            hide_index=True
        )


if __name__ == "__main__":
    render()