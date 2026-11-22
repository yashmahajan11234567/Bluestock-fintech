"""Main entry point for the Nifty 100 Streamlit analytics dashboard."""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

from src.dashboard._pages import home, profile, screener, peers, trends, sectors, capital, reports
from src.dashboard.ui import init_ui


def _sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="nf-brand">
          <div class="nf-brand-mark" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M5 16.5L10 11.5L13 14.5L19 7.5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M15 7.5H19V11.5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M4 20H20" stroke="white" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div>
            <div class="nf-brand-name">Nifty 100</div>
            <div class="nf-brand-sub">Equity analytics workspace</div>
          </div>
        </div>
        <div class="nf-nav-label">WORKSPACE</div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Nifty 100 Analytics",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_ui()
    _sidebar_brand()

    pages = {
        "Home": home.render,
        "Company Profile": profile.render,
        "Screener": screener.render,
        "Peer Comparison": peers.render,
        "Financial Trends": trends.render,
        "Sector Analysis": sectors.render,
        "Capital Allocation": capital.render,
        "Reports": reports.render,
    }

    selection = st.sidebar.radio("Navigate", list(pages.keys()), label_visibility="collapsed")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="nf-sidebar-foot"><strong>92 listed companies</strong><br>'
        'Financial statements, ratios and peer intelligence across 10+ years.</div>',
        unsafe_allow_html=True,
    )
    pages[selection]()


if __name__ == "__main__":
    main()
