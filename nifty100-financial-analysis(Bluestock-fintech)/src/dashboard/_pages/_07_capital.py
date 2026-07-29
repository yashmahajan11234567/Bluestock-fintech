"""
Capital Allocation page - ROE/ROCE analysis, cash conversion, efficiency scores.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_company_list, get_capital_alloc_data
from src.analytics.capital_allocation import (
    capital_allocation_category,
    capital_score,
    is_capital_efficient,
    needs_capital_review,
)


def render() -> None:
    """Render the Capital Allocation page."""
    st.title("💰 Capital Allocation")
    st.markdown("Assess how efficiently companies deploy capital using ROE, ROCE, and Cash Conversion Ratio.")

    companies = get_company_list()
    if not companies:
        st.error("No companies found.")
        return

    company_names = [c["company_name"] for c in companies]
    selected = st.selectbox("Select Company", company_names)

    if st.button("Analyze Capital Allocation", type="primary"):
        company_id = next(c["company_id"] for c in companies if c["company_name"] == selected)

        with st.spinner("Loading capital allocation data..."):
            data = get_capital_alloc_data(company_id)

        if data is None or data.empty:
            st.warning("No capital allocation data available.")
            return

        st.success(f"Capital allocation analysis for **{selected}**")

        # Latest period analysis
        latest = data.sort_values("year", ascending=False).iloc[0]
        roe = latest.get("return_on_equity_pct")
        roce = latest.get("return_on_capital_employed_pct")
        ccr = latest.get("cash_conversion_ratio")

        # Classification
        category = capital_allocation_category(roe, roce, ccr)
        score = capital_score(category)
        efficient = is_capital_efficient(category)
        review = needs_capital_review(category)

        # Display category badge
        color_map = {
            "Excellent": "🟢", "Good": "🟢",
            "Average": "🟡", "Weak": "🟠", "Poor": "🔴"
        }
        emoji = color_map.get(category, "⚪")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Capital Allocation", f"{emoji} {category or 'N/A'}")
        with col2:
            st.metric("Score", f"{score}/5")
        with col3:
            st.metric("Efficient", "✅ Yes" if efficient else "❌ No")
        with col4:
            st.metric("Needs Review", "⚠️ Yes" if review else "✅ No")

        st.markdown("---")

        # Key inputs
        st.subheader("📥 Key Inputs")
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("ROE", f"{roe:.1f}%" if pd.notna(roe) else "N/A")
        with k2:
            st.metric("ROCE", f"{roce:.1f}%" if pd.notna(roce) else "N/A")
        with k3:
            st.metric("Cash Conversion Ratio", f"{ccr:.2f}x" if pd.notna(ccr) else "N/A")

        st.markdown("---")

        # Historical trend
        st.subheader("📈 Capital Allocation Trend")
        if "year" in data.columns and category:
            data["category"] = data.apply(
                lambda r: capital_allocation_category(
                    r.get("return_on_equity_pct"),
                    r.get("return_on_capital_employed_pct"),
                    r.get("cash_conversion_ratio")
                ), axis=1
            )
            category_order = ["Excellent", "Good", "Average", "Weak", "Poor"]
            data["category_rank"] = data["category"].map(
                {c: i for i, c in enumerate(category_order)}
            )

            fig = px.line(
                data.sort_values("year"),
                x="year", y="category_rank",
                title="Capital Allocation Category Over Time",
                markers=True
            )
            fig.update_yaxes(
                tickvals=list(range(len(category_order))),
                ticktext=category_order,
                title="Category"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Comparison with peers
        st.markdown("---")
        st.subheader("🏭 Sector Comparison")
        sector_comparison = get_sector_capital_alloc_comparison(data)
        if sector_comparison is not None:
            st.dataframe(sector_comparison, use_container_width=True, hide_index=True)


def get_sector_capital_alloc_comparison(company_data: pd.DataFrame) -> pd.DataFrame | None:
    """Get sector-level capital allocation comparison (placeholder)."""
    # In a real implementation, this would query sector aggregates
    return pd.DataFrame({
        "Sector": ["Technology", "Financials", "Consumer", "Industrial", "Healthcare"],
        "Avg ROE %": [18.5, 15.2, 14.8, 16.3, 22.1],
        "Avg ROCE %": [19.2, 14.8, 15.5, 17.1, 23.4],
        "Avg CCR": [1.15, 0.95, 1.05, 1.08, 1.25],
    })


if __name__ == "__main__":
    render()