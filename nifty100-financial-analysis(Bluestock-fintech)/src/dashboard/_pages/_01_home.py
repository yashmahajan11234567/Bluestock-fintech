"""Home dashboard with market KPIs, sector mix, and quality leaders."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.ui import (
    COLORS, apply_plotly_theme, format_number, format_percentage,
    metric_grid, page_header, section_header,
)
from src.dashboard.utils.db import (
    get_available_years, get_home_kpis, get_sector_distribution, get_top_companies,
)


def render() -> None:
    page_header(
        "Nifty 100 market overview",
        "A consolidated view of profitability, valuation, leverage and sector leadership across the Nifty 100 universe.",
    )

    years = get_available_years()
    if not years:
        st.error("No data available. Please check the database connection.")
        return

    selected_year = st.sidebar.selectbox(
        "Reporting year", options=years, index=len(years) - 1, format_func=lambda y: str(y)
    )
    kpis = get_home_kpis(selected_year)

    metric_grid([
        {"label": "Average ROE", "value": format_percentage(kpis.get("avg_roe")), "note": "Winsorized company average"},
        {"label": "Median P/E", "value": format_number(kpis.get("median_pe")), "note": "Across listed valuations"},
        {"label": "Median debt / equity", "value": format_number(kpis.get("median_debt_equity")), "note": "Balance-sheet leverage"},
        {"label": "Companies reporting", "value": str(kpis.get("total_companies", 0)), "note": f"Financial year {selected_year}"},
        {"label": "Median revenue CAGR", "value": format_percentage(kpis.get("median_revenue_cagr_5yr")), "note": "Five-year growth"},
        {"label": "Debt-free companies", "value": str(kpis.get("debt_free_companies", 0)), "note": "Zero or no reported debt"},
    ], columns=6)

    chart_col, table_col = st.columns([1.45, 1], gap="large")

    with chart_col:
        with st.container(border=True):
            section_header("Sector distribution")
            sector_data = get_sector_distribution(selected_year)
            if sector_data:
                df_sector = pd.DataFrame(sector_data)
                fig = px.pie(
                    df_sector,
                    names="sector",
                    values="count",
                    hole=0.56,
                    color_discrete_sequence=COLORS["chart_palette"],
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    textfont={"family": "Inter", "size": 11, "color": "#FFFFFF"},
                    marker={"line": {"color": "#FFFFFF", "width": 2}},
                    hovertemplate="%{label}<br>%{value} companies · %{percent}<extra></extra>",
                )
                apply_plotly_theme(
                    fig,
                    height=390,
                    showlegend=True,
                    legend={
                        "orientation": "v", "yanchor": "middle", "y": 0.5,
                        "xanchor": "left", "x": 1.01,
                        "font": {"family": "Inter", "size": 11, "color": "#475569"},
                    },
                    margin={"l": 10, "r": 120, "t": 20, "b": 10},
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.caption(f"Company count by broad sector · FY {selected_year}")
            else:
                st.info("No sector data available for the selected year.")

    with table_col:
        with st.container(border=True):
            section_header("Quality leaders")
            st.caption("Top five companies by composite quality score")
            top_companies = get_top_companies(selected_year, limit=5)
            if top_companies:
                df_top = pd.DataFrame(top_companies).rename(columns={
                    "company": "Company", "sector": "Sector", "composite_score": "Score",
                })
                st.dataframe(
                    df_top,
                    use_container_width=True,
                    hide_index=True,
                    height=300,
                    column_config={
                        "Company": st.column_config.TextColumn("Company"),
                        "Sector": st.column_config.TextColumn("Sector"),
                        "Score": st.column_config.NumberColumn("Score", format="%.1f"),
                    },
                )
                st.caption("Scores blend profitability, cash quality, growth and leverage.")
            else:
                st.info("No top company data available for the selected year.")


if __name__ == "__main__":
    render()
