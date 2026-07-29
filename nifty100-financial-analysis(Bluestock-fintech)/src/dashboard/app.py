"""
Main Streamlit application entry point for Nifty 100 Analytics Dashboard.

This module configures Streamlit, sets up sidebar navigation to all 8 pages,
and delegates rendering to the selected page's render() function.
"""

import streamlit as st

# Import page render functions
from src.dashboard.pages import (
    home,
    profile,
    screener,
    peers,
    trends,
    sectors,
    capital,
    reports,
)


def main() -> None:
    """Configure Streamlit and run the selected page."""
    st.set_page_config(
        page_title="Nifty 100 Analytics",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar navigation
    st.sidebar.title("📈 Nifty 100 Analytics")
    st.sidebar.markdown("---")

    pages = {
        "🏠 Home": home.render,
        "🏢 Company Profile": profile.render,
        "🔍 Screener": screener.render,
        "👥 Peer Comparison": peers.render,
        "📈 Trends": trends.render,
        "🏭 Sector Analysis": sectors.render,
        "💰 Capital Allocation": capital.render,
        "📋 Reports": reports.render,
    }

    selection = st.sidebar.radio("Navigate", list(pages.keys()))
    st.sidebar.markdown("---")
    st.sidebar.caption("Nifty 100 Financial Analytics Platform")

    # Call the selected page's render function
    pages[selection]()


if __name__ == "__main__":
    main()