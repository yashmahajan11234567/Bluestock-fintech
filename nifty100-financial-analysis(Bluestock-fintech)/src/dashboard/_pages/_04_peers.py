"""Peer comparison with percentile ranks and company-versus-peer radar analysis."""

import pandas as pd
import streamlit as st

from src.dashboard.ui import (
    COLORS, badge, metric_grid, page_header, section_header,
)
from src.dashboard.utils.db import (
    get_company_list, get_peer_group_members, get_peer_groups, get_peer_percentiles,
)
from src.screener.charts import create_peer_radar_chart


def render() -> None:
    page_header(
        "Peer comparison",
        "Benchmark a company against its sector peer set using percentile ranks and a side-by-side financial profile.",
    )

    companies = get_company_list()
    if not companies:
        st.error("No companies found.")
        return

    with st.container(border=True):
        select_col, action_col = st.columns([3, 1], gap="large")
        company_names = [c["company_name"] for c in companies]
        with select_col:
            selected = st.selectbox("Company", company_names)
        with action_col:
            st.markdown('<div style="height:27px"></div>', unsafe_allow_html=True)
            analyze = st.button("Compare with peers", type="primary", use_container_width=True)

    if not analyze:
        st.caption("Choose a company to calculate its relative position within the assigned peer group.")
        return

    company_id = next(c["company_id"] for c in companies if c["company_name"] == selected)
    with st.spinner("Computing peer percentiles..."):
        percentiles = get_peer_percentiles(company_id)
        peer_group = str(get_peer_groups(company_id) or "")

    if not percentiles:
        st.warning("No peer group data available for this company.")
        return

    peer_list = get_peer_group_members(peer_group) if peer_group else []
    overall_score = percentiles.get("overall_peer_score")

    metric_grid([
        {"label": "Overall peer score", "value": f"{overall_score:.1f} / 100" if overall_score is not None else "N/A", "note": "Average of available percentiles"},
        {"label": "Peer group", "value": peer_group or "N/A", "note": selected},
        {"label": "Companies in peer set", "value": str(len(peer_list)), "note": "Including selected company"},
    ], columns=3)

    left_col, right_col = st.columns([1, 1.15], gap="large")

    with left_col:
        with st.container(border=True):
            section_header("Percentile rankings")
            pct_cols = [k for k in percentiles if k.endswith("_percentile")]
            if pct_cols:
                pct_data = {
                    k.replace("_percentile", "").replace("_", " ").title(): v
                    for k, v in percentiles.items() if k in pct_cols
                }
                df_pct = pd.DataFrame([
                    {"Metric": key, "Percentile": f"{value:.1f}" if pd.notna(value) else "N/A"}
                    for key, value in pct_data.items()
                ])
                st.dataframe(
                    df_pct,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Metric": st.column_config.TextColumn("Metric", width="large"),
                        "Percentile": st.column_config.TextColumn("Percentile", width="small"),
                    },
                )
            st.caption("Higher is better. P/E, P/B and debt-to-equity are inverted so lower values score higher.")

    with right_col:
        with st.container(border=True):
            section_header("Company vs peer average")
            try:
                fig = create_peer_radar_chart(company_id)
                fig.patch.set_facecolor("#FFFFFF")
                for ax in fig.get_axes():
                    ax.set_facecolor("#FFFFFF")
                    ax.tick_params(colors=COLORS["text_secondary"], labelsize=9)
                    ax.xaxis.label.set_color(COLORS["text_primary"])
                    ax.yaxis.label.set_color(COLORS["text_primary"])
                    ax.title.set_color(COLORS["text_primary"])
                    ax.grid(color=COLORS["border_light"], linewidth=0.8)
                    for spine in ax.spines.values():
                        spine.set_color(COLORS["border_medium"])
                st.pyplot(fig, use_container_width=True)
            except Exception as exc:
                st.error(f"Could not generate radar chart: {exc}")

    section_header("Peer group members")
    if peer_list:
        df_peers = pd.DataFrame(peer_list)
        st.dataframe(
            df_peers,
            use_container_width=True,
            hide_index=True,
            column_config={
                "company_id": st.column_config.TextColumn("Symbol", width="small"),
                "company_name": st.column_config.TextColumn("Company name", width="large"),
            },
        )
    else:
        st.info("No peer members available.")


if __name__ == "__main__":
    render()
