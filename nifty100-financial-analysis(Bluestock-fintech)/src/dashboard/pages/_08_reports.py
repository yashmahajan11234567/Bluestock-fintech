"""
Reports page - Export peer comparison Excel with conditional formatting.
"""

import streamlit as st
import pandas as pd
import io
import os

from src.dashboard.utils.db import get_company_list, get_peer_groups
from src.screener.report import generate_peer_comparison_report


def render() -> None:
    """Render the Reports page."""
    st.title("📋 Reports")
    st.markdown("Generate and download comprehensive financial analysis reports.")

    tab1, tab2, tab3 = st.tabs(["📊 Peer Comparison Report", "📈 Custom Report", "📁 Generated Reports"])

    with tab1:
        render_peer_comparison_report()

    with tab2:
        render_custom_report()

    with tab3:
        render_generated_reports()


def render_peer_comparison_report() -> None:
    """Render peer comparison Excel report generation."""
    st.subheader("📊 Peer Comparison Excel Report")
    st.markdown("""
    Generates a comprehensive Excel report with one worksheet per peer group containing:
    - Company Name, Peer Group, Overall Peer Score
    - All percentile metrics (ROE, NPM, Revenue CAGR, PAT CAGR, FCF, D/E, PE, PB)
    - Sorted by Overall Peer Score (descending)
    - **Conditional formatting**: Top 20% Green, Middle 60% Yellow, Bottom 20% Red
    - Frozen header row, auto-sized columns, bold headers
    """)

    if st.button("🚀 Generate Peer Comparison Report", type="primary", use_container_width=True):
        with st.spinner("Generating report... this may take a moment."):
            try:
                output_path = "Data/output/peer_comparison.xlsx"
                result_path = generate_peer_comparison_report(output_path)

                st.success("✅ Report generated successfully!")
                st.info(f"Saved to: `{result_path}`")

                # Provide download button
                with open(result_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=f.read(),
                        file_name="peer_comparison_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Error generating report: {e}")


def render_custom_report() -> None:
    """Render custom report builder."""
    st.subheader("📈 Custom Report Builder")
    st.markdown("Build a custom report by selecting companies and metrics.")

    companies = get_company_list()
    if not companies:
        st.warning("No companies available.")
        return

    company_names = [c["company_name"] for c in companies]
    selected_companies = st.multiselect("Select Companies", company_names)

    metrics = st.multiselect(
        "Select Metrics",
        ["ROE", "ROCE", "Net Profit Margin", "Debt to Equity", "PE Ratio", "PB Ratio",
         "Revenue CAGR", "PAT CAGR", "Free Cash Flow", "Dividend Yield"],
        default=["ROE", "ROCE", "Net Profit Margin", "Debt to Equity"]
    )

    if st.button("Generate Custom Report", use_container_width=True):
        if not selected_companies:
            st.warning("Please select at least one company.")
        elif not metrics:
            st.warning("Please select at least one metric.")
        else:
            st.info("Custom report generation coming soon...")


def render_generated_reports() -> None:
    """Show list of previously generated reports."""
    st.subheader("📁 Generated Reports")

    output_dir = "Data/output"
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if f.endswith((".xlsx", ".csv", ".pdf"))]
        if files:
            df = pd.DataFrame({"File": files})
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No generated reports found.")
    else:
        st.info("Output directory not found.")


if __name__ == "__main__":
    render()