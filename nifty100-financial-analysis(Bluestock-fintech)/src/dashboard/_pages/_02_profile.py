"""Company profile with statement history, ratios, and capital metrics."""

import pandas as pd
import streamlit as st

from src.dashboard.ui import (
    badge, format_currency, format_number, format_percentage,
    metric_grid, page_header, section_header,
)
from src.dashboard.utils.db import (
    get_capital_alloc_data, get_cashflow_data, get_company_list,
    get_company_profile, get_financial_ratios,
)


def _has_data(df: pd.DataFrame | None) -> bool:
    return df is not None and not df.empty


def render() -> None:
    page_header(
        "Company profile",
        "Inspect a company’s financial position, historical ratios, cash generation and capital efficiency in one workspace.",
    )

    companies = get_company_list()
    if not companies:
        st.error("No companies found in database.")
        return

    with st.container(border=True):
        select_col, action_col = st.columns([3, 1], gap="large")
        company_names = [c["company_name"] for c in companies]
        with select_col:
            selected_name = st.selectbox("Company", company_names)
        with action_col:
            st.markdown('<div style="height:27px"></div>', unsafe_allow_html=True)
            load = st.button("View company", type="primary", use_container_width=True)

    if not load:
        st.caption("Choose a company and select View company to load its financial profile.")
        return

    company_id = next(c["company_id"] for c in companies if c["company_name"] == selected_name)
    with st.spinner("Loading company data..."):
        profile = get_company_profile(company_id)
        ratios = get_financial_ratios(company_id)
        cashflow = get_cashflow_data(company_id)
        capital = get_capital_alloc_data(company_id)

    if not profile:
        st.warning("No profile data found for this company.")
        return

    with st.container(border=True):
        st.markdown(
            f'<div class="nf-summary"><div><div class="nf-summary-title">{selected_name}</div>'
            f'<div class="nf-summary-sub">{profile.get("sector", "N/A")} · {profile.get("industry", "N/A")}</div></div>'
            f'{badge(company_id)}</div>',
            unsafe_allow_html=True,
        )

    metric_grid([
        {"label": "Sector", "value": profile.get("sector", "N/A"), "note": "Broad sector"},
        {"label": "Industry", "value": profile.get("industry", "N/A"), "note": "Sub-sector classification"},
        {"label": "Market capitalization", "value": format_currency(profile.get("market_cap_cr")), "note": "Latest reported value"},
    ], columns=3)

    tab1, tab2, tab3, tab4 = st.tabs(["Financial ratios", "Cash flow", "Capital allocation", "Raw financials"])

    with tab1:
        if _has_data(ratios):
            latest = ratios.iloc[0]
            metric_grid([
                {"label": "Return on equity", "value": format_percentage(latest.get("return_on_equity_pct")), "note": f"FY {latest.get('year', 'latest')}"},
                {"label": "Return on capital employed", "value": format_percentage(latest.get("return_on_capital_employed_pct")), "note": "Latest reported year"},
                {"label": "Debt / equity", "value": format_number(latest.get("debt_to_equity")), "note": "Leverage ratio"},
                {"label": "Interest coverage", "value": format_number(latest.get("interest_coverage")), "note": "Times interest earned"},
            ], columns=4)
            section_header("Ratio history")
            st.dataframe(
                ratios,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "year": st.column_config.NumberColumn("Year", format="%d"),
                    "return_on_equity_pct": st.column_config.NumberColumn("ROE %", format="%.2f"),
                    "return_on_capital_employed_pct": st.column_config.NumberColumn("ROCE %", format="%.2f"),
                    "net_profit_margin_pct": st.column_config.NumberColumn("Net margin %", format="%.2f"),
                    "operating_profit_margin_pct": st.column_config.NumberColumn("Operating margin %", format="%.2f"),
                    "debt_to_equity": st.column_config.NumberColumn("Debt / equity", format="%.2f"),
                    "free_cash_flow_cr": st.column_config.NumberColumn("Free cash flow (₹Cr)", format="%.1f"),
                    "cash_from_operations_cr": st.column_config.NumberColumn("Operating cash flow (₹Cr)", format="%.1f"),
                },
            )
        else:
            st.info("No ratio data available.")

    with tab2:
        section_header("Cash-flow history")
        if _has_data(cashflow):
            st.dataframe(
                cashflow,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "year": st.column_config.NumberColumn("Year", format="%d"),
                    "operating_activity": st.column_config.NumberColumn("Operating activity (₹Cr)", format="%.1f"),
                    "investing_activity": st.column_config.NumberColumn("Investing activity (₹Cr)", format="%.1f"),
                    "financing_activity": st.column_config.NumberColumn("Financing activity (₹Cr)", format="%.1f"),
                    "net_cash_flow": st.column_config.NumberColumn("Net cash flow (₹Cr)", format="%.1f"),
                },
            )
        else:
            st.info("No cash flow data available.")

    with tab3:
        section_header("Capital allocation history")
        if _has_data(capital):
            latest_capital = capital.iloc[0]
            metric_grid([
                {"label": "ROE", "value": format_percentage(latest_capital.get("return_on_equity_pct")), "note": "Latest year"},
                {"label": "ROCE", "value": format_percentage(latest_capital.get("return_on_capital_employed_pct")), "note": "Latest year"},
                {"label": "Cash conversion", "value": format_number(latest_capital.get("cash_conversion_ratio")) + "x", "note": "Operating cash / net profit"},
            ], columns=3)
            st.dataframe(capital, use_container_width=True, hide_index=True)
        else:
            st.info("No capital allocation data available.")

    with tab4:
        st.info("Raw financial statements are available through the project’s database integration module.")


if __name__ == "__main__":
    render()
