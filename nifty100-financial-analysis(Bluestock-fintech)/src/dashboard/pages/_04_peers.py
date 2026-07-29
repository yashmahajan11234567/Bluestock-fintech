"""
Peer Comparison page - Percentile rankings and radar charts within peer groups.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.dashboard.utils.db import get_company_list, get_peer_groups, get_peer_percentiles
from src.screener.charts import create_peer_radar_chart, save_radar_chart


def render() -> None:
    """Render the Peer Comparison page."""
    st.title("👥 Peer Comparison")
    st.markdown("Compare a company against its peer group using percentile rankings.")

    # Company selector
    companies = get_company_list()
    if not companies:
        st.error("No companies found.")
        return

    company_names = [c["company_name"] for c in companies]
    selected = st.selectbox("Select Company", company_names)

    if st.button("Analyze Peers", type="primary"):
        company_id = next(c["company_id"] for c in companies if c["company_name"] == selected)

        with st.spinner("Computing peer percentiles..."):
            percentiles = get_peer_percentiles(company_id)
            peer_group = get_peer_groups(company_id)

        if not percentiles:
            st.warning("No peer group data available for this company.")
            return

        # Peer group info
        st.subheader(f"Peer Group: {peer_group}")
        st.caption(f"Analysis for: **{selected}**")

        # Overall peer score
        overall_score = percentiles.get("overall_peer_score")
        if overall_score is not None:
            score_color = "green" if overall_score >= 80 else "orange" if overall_score >= 50 else "red"
            st.markdown(f"### Overall Peer Score: "
                       f"<span style='color:{score_color};font-size:1.5em'>{overall_score:.1f}/100</span>",
                       unsafe_allow_html=True)

        st.markdown("---")

        # Percentile table
        st.subheader("📊 Percentile Rankings (0-100, Higher is Better*)")
        pct_cols = [k for k in percentiles.keys() if k.endswith("_percentile") or k == "overall_peer_score"]

        if pct_cols:
            pct_data = {k.replace("_percentile", "").replace("_", " ").title(): v
                       for k, v in percentiles.items() if k in pct_cols}
            df_pct = pd.DataFrame([pct_data]).T.rename(columns={0: "Percentile"})
            df_pct["Percentile"] = df_pct["Percentile"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
            st.dataframe(df_pct, use_container_width=True)

        st.caption("* For PE, PB, and Debt-to-Equity: lower values receive higher percentiles (inverted)")

        # Radar chart
        st.subheader("🕸️ Radar Chart: Company vs Peer Average")
        try:
            fig = create_peer_radar_chart(company_id)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Could not generate radar chart: {e}")

        # Peer group details
        st.markdown("---")
        st.subheader("🏷️ Peer Group Members")
        peer_list = get_peer_group_members(peer_group)
        if peer_list:
            df_peers = pd.DataFrame(peer_list)
            st.dataframe(df_peers, use_container_width=True, hide_index=True)


def get_peer_group_members(peer_group: str) -> list:
    """Get list of companies in the peer group."""
    from src.dashboard.utils.db import get_peer_group_members as db_get_members
    return db_get_members(peer_group)


if __name__ == "__main__":
    render()