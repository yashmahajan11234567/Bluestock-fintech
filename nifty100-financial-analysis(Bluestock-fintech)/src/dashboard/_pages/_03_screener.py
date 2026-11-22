"""Stock screener with preset strategies and custom financial filters."""

import streamlit as st

from src.dashboard.ui import badge, page_header, section_header
from src.dashboard.utils.db import get_screener_results
from src.screener.engine import (
    get_debt_free_blue_chip_filters, get_dividend_champion_filters,
    get_growth_accelerator_filters, get_quality_compounder_filters,
    get_turnaround_watch_filters, get_value_pick_filters,
)


def render() -> None:
    page_header(
        "Stock screener",
        "Build an investable watchlist using curated strategies or precise fundamental thresholds across the Nifty 100 universe.",
    )

    presets = {
        "Quality Compounder": get_quality_compounder_filters(),
        "Value Pick": get_value_pick_filters(),
        "Growth Accelerator": get_growth_accelerator_filters(),
        "Dividend Champion": get_dividend_champion_filters(),
        "Debt-Free Blue Chip": get_debt_free_blue_chip_filters(),
        "Turnaround Watch": get_turnaround_watch_filters(),
    }

    with st.container(border=True):
        section_header("Strategy workspace")
        preset_col, action_col = st.columns([3, 1], gap="large")
        with preset_col:
            selected_preset = st.selectbox("Preset strategy", list(presets.keys()))
        with action_col:
            st.markdown('<div style="height:27px"></div>', unsafe_allow_html=True)
            use_preset = st.button("Apply strategy", use_container_width=True)

        if use_preset:
            st.session_state["screener_filters"] = presets[selected_preset]
            st.success(f"Applied: {selected_preset}")

        current_filters = st.session_state.get("screener_filters", {})
        if current_filters:
            st.markdown("**Active filters**")
            st.code(" · ".join(f"{key}: {value}" for key, value in current_filters.items()), language=None)

    with st.expander("Custom financial filters"):
        filter_col1, filter_col2 = st.columns(2, gap="large")
        with filter_col1:
            roe_min = st.number_input("Minimum ROE (%)", min_value=0.0, max_value=100.0, step=1.0)
            fcf_min = st.number_input("Minimum free cash flow (₹Cr)", min_value=0.0, step=10.0)
            sales_cagr_min = st.number_input("Minimum revenue CAGR (%)", min_value=0.0, step=1.0)
            pat_cagr_min = st.number_input("Minimum PAT CAGR (%)", min_value=0.0, step=1.0)
            div_yield_min = st.number_input("Minimum dividend yield (%)", min_value=0.0, step=0.1)
        with filter_col2:
            de_max = st.number_input("Maximum debt to equity", min_value=0.0, max_value=20.0, step=0.1)
            pe_max = st.number_input("Maximum P/E ratio", min_value=0.0, max_value=200.0, step=1.0)
            pb_max = st.number_input("Maximum P/B ratio", min_value=0.0, max_value=50.0, step=0.1)
            ic_min = st.number_input("Minimum interest coverage", min_value=0.0, step=0.5)
            mcap_min = st.number_input("Minimum market cap (₹Cr)", min_value=0.0, step=1000.0)

        if st.button("Apply custom filters", use_container_width=True):
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
            st.success("Custom filters applied.")

    run = st.button("Run screener", type="primary", use_container_width=True)
    if not run:
        return

    filters = st.session_state.get("screener_filters", {})
    if not filters:
        st.warning("Select a preset strategy or define custom filters before running the screener.")
        return

    with st.spinner("Screening companies..."):
        results = get_screener_results(filters)

    if results is None or results.empty:
        st.warning("No companies match the selected criteria.")
        return

    display_cols = [
        "company_id", "company_name", "composite_quality_score", "sector_relative_score",
        "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
        "compounded_sales_growth", "dividend_yield_pct", "net_profit_margin_pct",
        "pe_ratio", "pb_ratio", "sector",
    ]
    display_cols = [c for c in display_cols if c in results.columns]

    section_header("Screening results")
    result_head, download_col = st.columns([3, 1], gap="large")
    with result_head:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">{badge(f"{len(results)} matches", "success")}'
            f'<span style="color:#64748B;font-size:12px">Sorted by composite quality score · showing up to 50 rows</span></div>',
            unsafe_allow_html=True,
        )
    with download_col:
        st.download_button(
            "Download CSV", results[display_cols].to_csv(index=False),
            "screener_results.csv", "text/csv", use_container_width=True,
        )

    st.dataframe(
        results[display_cols].head(50),
        use_container_width=True,
        hide_index=True,
        column_config={
            "company_id": st.column_config.TextColumn("Symbol", width="small"),
            "company_name": st.column_config.TextColumn("Company", width="large"),
            "sector": st.column_config.TextColumn("Sector", width="medium"),
            "composite_quality_score": st.column_config.NumberColumn("Quality score", format="%.1f"),
            "sector_relative_score": st.column_config.NumberColumn("Sector score", format="%.1f"),
            "return_on_equity_pct": st.column_config.NumberColumn("ROE %", format="%.1f"),
            "debt_to_equity": st.column_config.NumberColumn("Debt / equity", format="%.2f"),
            "free_cash_flow_cr": st.column_config.NumberColumn("Free cash flow (₹Cr)", format="%.1f"),
            "compounded_sales_growth": st.column_config.NumberColumn("Revenue CAGR %", format="%.1f"),
            "dividend_yield_pct": st.column_config.NumberColumn("Dividend yield %", format="%.1f"),
            "net_profit_margin_pct": st.column_config.NumberColumn("Net margin %", format="%.1f"),
            "pe_ratio": st.column_config.NumberColumn("P/E", format="%.1f"),
            "pb_ratio": st.column_config.NumberColumn("P/B", format="%.1f"),
        },
    )


if __name__ == "__main__":
    render()
