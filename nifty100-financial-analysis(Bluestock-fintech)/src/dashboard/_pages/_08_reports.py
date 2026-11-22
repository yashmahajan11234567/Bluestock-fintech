"""Report generation and download center."""

import os

import pandas as pd
import streamlit as st

from src.dashboard.ui import page_header, section_header
from src.dashboard.utils.db import get_company_list
from src.screener.report import generate_peer_comparison_report


def render() -> None:
    page_header(
        "Reports",
        "Generate peer-analysis workbooks, configure custom company reports, and access previously generated files.",
    )

    tab1, tab2, tab3 = st.tabs(["Peer comparison", "Custom report", "Generated files"])

    with tab1:
        render_peer_comparison_report()
    with tab2:
        render_custom_report()
    with tab3:
        render_generated_reports()


def render_peer_comparison_report() -> None:
    with st.container(border=True):
        section_header("Peer comparison workbook")
        st.markdown(
            "Create one workbook with a worksheet per peer group, including company scores and percentile metrics. "
            "Reports are sorted by overall peer score and include conditional formatting for quick comparison."
        )
        st.markdown(
            "- ROE, net margin, revenue CAGR and PAT CAGR\n"
            "- Free cash flow, debt-to-equity, P/E and P/B\n"
            "- Frozen headers, readable columns and top/middle/bottom performance bands"
        )
        generate = st.button("Generate peer comparison report", type="primary", use_container_width=True)

    if generate:
        with st.spinner("Generating report... this may take a moment."):
            try:
                output_path = "Data/output/peer_comparison.xlsx"
                result_path = generate_peer_comparison_report(output_path)
                st.success("Report generated successfully.")
                st.caption(f"Saved to: {result_path}")
                with open(result_path, "rb") as file:
                    st.download_button(
                        "Download Excel report",
                        data=file.read(),
                        file_name="peer_comparison_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            except Exception as exc:
                st.error(f"Error generating report: {exc}")


def render_custom_report() -> None:
    with st.container(border=True):
        section_header("Custom report builder")
        st.markdown("Select the companies and financial metrics to include in a tailored report.")

        companies = get_company_list()
        if not companies:
            st.warning("No companies available.")
            return

        company_names = [c["company_name"] for c in companies]
        selected_companies = st.multiselect("Companies", company_names)
        metrics = st.multiselect(
            "Metrics",
            ["ROE", "ROCE", "Net Profit Margin", "Debt to Equity", "PE Ratio", "PB Ratio",
             "Revenue CAGR", "PAT CAGR", "Free Cash Flow", "Dividend Yield"],
            default=["ROE", "ROCE", "Net Profit Margin", "Debt to Equity"],
        )
        generate = st.button("Generate custom report", use_container_width=True)

    if generate:
        if not selected_companies:
            st.warning("Please select at least one company.")
        elif not metrics:
            st.warning("Please select at least one metric.")
        else:
            st.info("Custom report generation is not yet available.")


def render_generated_reports() -> None:
    section_header("Generated files")
    output_dir = "Data/output"
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if f.endswith((".xlsx", ".csv", ".pdf"))]
        if files:
            st.dataframe(
                pd.DataFrame({"Report file": sorted(files)}),
                use_container_width=True,
                hide_index=True,
                column_config={"Report file": st.column_config.TextColumn("Report file", width="large")},
            )
        else:
            st.info("No generated reports found.")
    else:
        st.info("The output directory has not been created yet.")


if __name__ == "__main__":
    render()
