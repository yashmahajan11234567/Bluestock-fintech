"""
Screener page - Filter companies by financial criteria with preset strategies.
"""

import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_screener_results, get_preset_filters
from src.screener.engine import (
    get_quality_compounder_filters,
    get_value_pick_filters,
    get_growth_accelerator_filters,
    get_dividend_champion_filters,
    get_debt_free_blue_chip_filters,
    get_turnaround_watch_filters,
)


def render() -> None:
    """Render the Screener page."""
    st.title("🔍 Stock Screener")
    st.markdown("Filter Nifty 100 companies by financial criteria using preset strategies or custom filters.")

    # Preset strategy selector
    st.subheader("🎯 Preset Strategies")
    presets = {
        "Quality Compounder": get_quality_compounder_filters(),
        "Value Pick": get_value_pick_filters(),
        "Growth Accelerator": get_growth_accelerator_filters(),
        "Dividend Champion": get_dividend_champion_filters(),
        "Debt-Free Blue Chip": get_debt_free_blue_chip_filters(),
        "Turnaround Watch": get_turnaround_watch_filters(),
    }

    preset_col1, preset_col2 = st.columns([2, 1])
    with preset_col1:
        selected_preset = st.selectbox("Select Preset Strategy", list(presets.keys()))
    with preset_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        use_preset = st.button("Apply Preset", type="primary", use_container_width=True)

    # Get filters from preset
    if use_preset:
        st.session_state["screener_filters"] = presets[selected_preset]
        st.success(f"Applied: {selected_preset}")

    # Display current filters
    current_filters = st.session_state.get("screener_filters", {})
    if current_filters:
        st.markdown("**Active Filters:**")
        for k, v in current_filters.items():
            st.markdown(f"- **{k}**: {v}")

    st.markdown("---")

    # Custom filters
    st.subheader("⚙️ Custom Filters")
    with st.expander("Add/Modify Filters"):
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            roe_min = st.number_input("Min ROE (%)", min_value=0.0, max_value=100.0, step=1.0)
            fcf_min = st.number_input("Min Free Cash Flow (₹Cr)", min_value=0.0, step=10.0)
            sales_cagr_min = st.number_input("Min Revenue CAGR (%)", min_value=0.0, step=1.0)
            pat_cagr_min = st.number_input("Min PAT CAGR (%)", min_value=0.0, step=1.0)
            div_yield_min = st.number_input("Min Dividend Yield (%)", min_value=0.0, step=0.1)

        with filter_col2:
            de_max = st.number_input("Max Debt to Equity", min_value=0.0, max_value=20.0, step=0.1)
            pe_max = st.number_input("Max PE Ratio", min_value=0.0, max_value=200.0, step=1.0)
            pb_max = st.number_input("Max PB Ratio", min_value=0.0, max_value=50.0, step=0.1)
            ic_min = st.number_input("Min Interest Coverage", min_value=0.0, step=0.5)
            mcap_min = st.number_input("Min Market Cap (₹Cr)", min_value=0.0, step=1000.0)

        if st.button("Apply Custom Filters"):
            custom_filters = {}
            if roe_min > 0:
                custom_filters["ROE"] = {"min": roe_min}
            if fcf_min > 0:
                custom_filters["Free Cash Flow"] = {"min": fcf_min}
            if sales_cagr_min > 0:
                custom_filters["Revenue CAGR"] = {"min": sales_cagr_min}
            if pat_cagr_min > 0:
                custom_filters["PAT CAGR"] = {"min": pat_cagr_min}
            if div_yield_min > 0:
                custom_filters["Dividend Yield"] = {"min": div_yield_min}
            if de_max < 20:
                custom_filters["Debt to Equity"] = {"max": de_max}
            if pe_max < 200:
                custom_filters["PE"] = {"max": pe_max}
            if pb_max < 50:
                custom_filters["PB"] = {"max": pb_max}
            if ic_min > 0:
                custom_filters["Interest Coverage"] = {"min": ic_min}
            if mcap_min > 0:
                custom_filters["Market Cap"] = {"min": mcap_min}

            st.session_state["screener_filters"] = custom_filters
            st.success("Custom filters applied!")

    st.markdown("---")

    # Run screener
    if st.button("🔍 Run Screener", type="primary", use_container_width=True):
        filters = st.session_state.get("screener_filters", {})
        if not filters:
            st.warning("Please select a preset or define custom filters.")
            return

        with st.spinner("Screening companies..."):
            results = get_screener_results(filters)

        if results is None or results.empty:
            st.warning("No companies match the selected criteria.")
            return

        st.success(f"Found {len(results)} matching companies!")

        # Display results
        display_cols = [
            "company_id", "company_name", "composite_quality_score", "sector_relative_score",
            "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
            "compounded_sales_growth", "dividend_yield_pct",
            "net_profit_margin_pct", "pe_ratio", "pb_ratio", "sector"
        ]
        display_cols = [c for c in display_cols if c in results.columns]

        st.dataframe(
            results[display_cols].head(50),
            use_container_width=True,
            hide_index=True,
            column_config={
                "composite_quality_score": st.column_config.NumberColumn("Quality Score", format="%.1f"),
                "sector_relative_score": st.column_config.NumberColumn("Sector Score", format="%.1f"),
                "return_on_equity_pct": st.column_config.NumberColumn("ROE %", format="%.1f"),
                "debt_to_equity": st.column_config.NumberColumn("D/E", format="%.2f"),
                "free_cash_flow_cr": st.column_config.NumberColumn("FCF (₹Cr)", format="₹%,.1f"),
                "compounded_sales_growth": st.column_config.NumberColumn("Rev CAGR %", format="%.1f"),
                "dividend_yield_pct": st.column_config.NumberColumn("Div Yield %", format="%.1f"),
                "net_profit_margin_pct": st.column_config.NumberColumn("NPM %", format="%.1f"),
                "pe_ratio": st.column_config.NumberColumn("P/E", format="%.1f"),
                "pb_ratio": st.column_config.NumberColumn("P/B", format="%.1f"),
            }
        )

        # Download results
        csv = results[display_cols].to_csv(index=False)
        st.download_button(
            "📥 Download Results (CSV)",
            csv,
            "screener_results.csv",
            "text/csv",
            use_container_width=True
        )


if __name__ == "__main__":
    render()