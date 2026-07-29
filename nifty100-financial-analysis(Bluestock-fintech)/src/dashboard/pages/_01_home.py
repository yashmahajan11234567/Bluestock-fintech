"""
Home Dashboard - Overview with KPI cards, sector donut, and top companies table.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_available_years,
    get_home_kpis,
    get_sector_distribution,
    get_top_companies,
)


def render() -> None:
    """Render the Home Dashboard page."""
    st.title("Nifty 100 Analytics Dashboard")
    st.markdown("Comprehensive financial analytics for Nifty 100 companies.")

    # ------------------------------------------------------------------
    # Sidebar year selector
    # ------------------------------------------------------------------
    years = get_available_years()
    if not years:
        st.error("No data available. Please check the database connection.")
        return

    default_idx = len(years) - 1  # most recent year
    selected_year = st.sidebar.selectbox(
        "Select Year",
        options=years,
        index=default_idx,
        format_func=lambda y: str(y),
    )

    # ------------------------------------------------------------------
    # 1. KPI cards
    # ------------------------------------------------------------------
    kpis = get_home_kpis(selected_year)

    kpi_config = [
        ("Average ROE", f"{kpis['avg_roe']:.2f}%" if isinstance(kpis['avg_roe'], float) else "N/A"),
        ("Median P/E", f"{kpis['median_pe']:.2f}" if isinstance(kpis['median_pe'], float) else "N/A"),
        ("Median Debt/Equity", f"{kpis['median_debt_equity']:.2f}" if isinstance(kpis['median_debt_equity'], float) else "N/A"),
        ("Total Companies", str(kpis['total_companies'])),
        ("Median Revenue CAGR (5yr)", f"{kpis['median_revenue_cagr_5yr']:.2f}%" if isinstance(kpis['median_revenue_cagr_5yr'], float) else "N/A"),
        ("Debt-Free Companies", str(kpis['debt_free_companies'])),
    ]

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    cols = [col1, col2, col3, col4, col5, col6]
    for col, (label, value) in zip(cols, kpi_config):
        with col:
            with st.container(border=True):
                st.metric(label=label, value=value)

    # ------------------------------------------------------------------
    # 2. Donut chart - Sector Distribution
    # ------------------------------------------------------------------
    sector_data = get_sector_distribution(selected_year)
    if sector_data:
        st.markdown("---")
        st.subheader("Sector Distribution")
        df_sector = pd.DataFrame(sector_data)
        fig = px.pie(
            df_sector,
            names="sector",
            values="count",
            hole=0.4,
            title=f"Sector Distribution ({selected_year})",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textposition="outside", textinfo="label+percent")
        fig.update_layout(
            height=450,
            margin=dict(t=40, b=20, l=20, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sector data available for the selected year.")

    # ------------------------------------------------------------------
    # 3. Top-5 Companies table
    # ------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Top 5 Companies by Composite Score")
    top_companies = get_top_companies(selected_year, limit=5)
    if top_companies:
        df_top = pd.DataFrame(top_companies)
        df_top.rename(
            columns={
                "company": "Company",
                "sector": "Sector",
                "composite_score": "Composite Score",
            },
            inplace=True,
        )
        st.dataframe(df_top, use_container_width=True, hide_index=True)
    else:
        st.info("No top company data available for the selected year.")


if __name__ == "__main__":
    render()