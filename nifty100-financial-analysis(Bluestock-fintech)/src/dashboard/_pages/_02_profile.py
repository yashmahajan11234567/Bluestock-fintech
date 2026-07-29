"""
Company Profile page - Detailed financials, ratios, and charts for a single company.
"""

import streamlit as st
import pandas as pd

from src.dashboard.utils.db import (
    get_company_list,
    get_company_profile,
    get_financial_ratios,
    get_cashflow_data,
    get_capital_alloc_data,
)


def _has_data(df: pd.DataFrame | None) -> bool:
    """Check if DataFrame is not None and not empty."""
    return df is not None and not df.empty


def render() -> None:
    """Render the Company Profile page."""
    st.title("🏢 Company Profile")
    st.markdown("Select a company to view detailed financial analysis.")

    # Company selector
    companies = get_company_list()
    if not companies:
        st.error("No companies found in database.")
        return

    company_names = [c["company_name"] for c in companies]
    selected_name = st.selectbox("Select Company", company_names)

    # Get company ID
    company_id = next(c["company_id"] for c in companies if c["company_name"] == selected_name)

    if st.button("Load Profile", type="primary"):
        with st.spinner("Loading company data..."):
            profile = get_company_profile(company_id)
            ratios = get_financial_ratios(company_id)
            cashflow = get_cashflow_data(company_id)
            capital = get_capital_alloc_data(company_id)

        if not profile:
            st.warning("No profile data found for this company.")
            return

        # Company header
        st.subheader(f"{profile.get('company_name', selected_name)} ({profile.get('symbol', 'N/A')})")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sector", profile.get("sector", "N/A"))
        with col2:
            st.metric("Industry", profile.get("industry", "N/A"))
        with col3:
            st.metric("Market Cap (₹Cr)", profile.get("market_cap_cr", "N/A"))

        st.markdown("---")

        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Financial Ratios", "💰 Cash Flow", "🏦 Capital Allocation", "📈 Raw Financials"])

        with tab1:
            if _has_data(ratios):
                st.dataframe(ratios, use_container_width=True, hide_index=True)

                # Key ratio cards
                if len(ratios) > 0:
                    latest = ratios.iloc[0]
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    with kpi1:
                        st.metric("ROE (%)", f"{latest.get('return_on_equity_pct', 0):.1f}" if latest.get('return_on_equity_pct') else "N/A")
                    with kpi2:
                        st.metric("ROCE (%)", f"{latest.get('return_on_capital_employed_pct', 0):.1f}" if latest.get('return_on_capital_employed_pct') else "N/A")
                    with kpi3:
                        st.metric("Debt/Equity", f"{latest.get('debt_to_equity', 0):.2f}" if latest.get('debt_to_equity') else "N/A")
                    with kpi4:
                        st.metric("Interest Coverage", f"{latest.get('interest_coverage', 0):.1f}" if latest.get('interest_coverage') else "N/A")
            else:
                st.info("No ratio data available.")

        with tab2:
            if _has_data(cashflow):
                st.dataframe(cashflow, use_container_width=True, hide_index=True)
            else:
                st.info("No cash flow data available.")

        with tab3:
            if _has_data(capital):
                st.dataframe(capital, use_container_width=True, hide_index=True)
            else:
                st.info("No capital allocation data available.")

        with tab4:
            st.info("Raw financial statements view - connect to db_integration module for full data.")


if __name__ == "__main__":
    render()