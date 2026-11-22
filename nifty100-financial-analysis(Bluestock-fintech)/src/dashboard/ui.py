"""Shared light-theme design system for the Nifty 100 Streamlit dashboard."""

from __future__ import annotations

from html import escape
from typing import Any, Iterable

import pandas as pd
import streamlit as st


COLORS = {
    "bg_primary": "#F5F7FB",
    "bg_secondary": "#FFFFFF",
    "bg_subtle": "#F8FAFC",
    "bg_hover": "#F1F5F9",
    "text_primary": "#172033",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "accent_primary": "#2563EB",
    "accent_secondary": "#3B82F6",
    "accent_cta": "#2563EB",
    "accent_success": "#16A34A",
    "accent_warning": "#D97706",
    "accent_danger": "#DC2626",
    "border_light": "#E2E8F0",
    "border_medium": "#CBD5E1",
    "positive": "#16A34A",
    "negative": "#DC2626",
    "chart_palette": [
        "#2563EB", "#60A5FA", "#14B8A6", "#F59E0B",
        "#8B5CF6", "#0F766E", "#93C5FD", "#94A3B8",
        "#CBD5E1", "#475569", "#38BDF8", "#A7F3D0",
    ],
}

SPACING = {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"}


GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&family=Manrope:wght@600;700&display=swap');

:root {
  --nf-bg: #F5F7FB;
  --nf-surface: #FFFFFF;
  --nf-subtle: #F8FAFC;
  --nf-text: #172033;
  --nf-secondary: #64748B;
  --nf-muted: #94A3B8;
  --nf-blue: #2563EB;
  --nf-blue-dark: #1D4ED8;
  --nf-blue-soft: #EFF6FF;
  --nf-border: #E2E8F0;
  --nf-border-strong: #CBD5E1;
  --nf-green: #16A34A;
  --nf-red: #DC2626;
  --nf-amber: #D97706;
  --nf-shadow: 0 1px 2px rgba(15, 23, 42, .04), 0 4px 12px rgba(15, 23, 42, .025);
}

/* App shell */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--nf-bg) !important;
  color: var(--nf-text) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] {
  background: transparent !important;
}
[data-testid="stAppDeployButton"], #MainMenu, footer { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container {
  max-width: 1360px !important;
  padding: 30px 36px 56px !important;
}
[data-testid="stMain"] { background: var(--nf-bg) !important; }
::selection { background: #BFDBFE; color: #172033; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 8px; border: 2px solid #F1F5F9; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* Typography */
h1, h2, h3, h4, .nf-page-title, .nf-section-title {
  font-family: 'Manrope', 'Inter', sans-serif !important;
  color: var(--nf-text) !important;
}
p, label, input, button, textarea, select, [data-testid="stMarkdownContainer"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
[data-testid="stMarkdownContainer"] p { color: var(--nf-text); line-height: 1.6; }
[data-testid="stCaptionContainer"], .stCaption, small { color: var(--nf-secondary) !important; }
a { color: var(--nf-blue); text-underline-offset: 3px; }
hr { border-color: var(--nf-border) !important; margin: 26px 0 !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--nf-surface) !important;
  border-right: 1px solid var(--nf-border) !important;
  box-shadow: 1px 0 8px rgba(15, 23, 42, .025) !important;
}
section[data-testid="stSidebar"] > div:first-child { padding-top: 4px !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 18px 16px !important; }
section[data-testid="stSidebar"] hr { margin: 20px 0 !important; }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: var(--nf-secondary) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
}
.nf-brand { display: flex; align-items: center; gap: 12px; padding: 4px 8px 20px; }
.nf-brand-mark {
  width: 38px; height: 38px; border-radius: 10px; background: var(--nf-blue);
  display: grid; place-items: center; flex: 0 0 auto;
  box-shadow: 0 4px 10px rgba(37, 99, 235, .18);
}
.nf-brand-name { font-family: 'Manrope', sans-serif; font-size: 17px; font-weight: 700; color: var(--nf-text); line-height: 1.25; }
.nf-brand-sub { font-size: 11px; color: var(--nf-secondary); margin-top: 2px; }
.nf-nav-label { padding: 6px 10px 8px; font-size: 11px; font-weight: 600; color: var(--nf-muted); letter-spacing: .04em; }
section[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: 4px !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
  min-height: 42px !important;
  padding: 10px 12px !important;
  margin: 0 !important;
  border: 1px solid transparent !important;
  border-radius: 9px !important;
  background: transparent !important;
  color: #475569 !important;
  transition: background-color 160ms ease, color 160ms ease, border-color 160ms ease !important;
  cursor: pointer !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: var(--nf-subtle) !important;
  color: var(--nf-text) !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background: var(--nf-blue-soft) !important;
  border-color: #DBEAFE !important;
  color: var(--nf-blue-dark) !important;
  box-shadow: inset 3px 0 0 var(--nf-blue) !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child { display: none !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
  font-size: 13px !important;
  font-weight: 500 !important;
  color: inherit !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p { font-weight: 650 !important; }
.nf-sidebar-foot { padding: 14px 10px 2px; font-size: 11px; line-height: 1.55; color: var(--nf-secondary); }

/* Shared content primitives */
.nf-page-head { margin: 0 0 26px; }
.nf-page-title { font-size: 30px; line-height: 1.25; letter-spacing: -.025em; font-weight: 700; margin: 0 0 7px; }
.nf-page-description { color: var(--nf-secondary); font-size: 14px; line-height: 1.6; margin: 0; max-width: 76ch; }
.nf-section-title { font-size: 18px; line-height: 1.35; letter-spacing: -.012em; font-weight: 700; margin: 28px 0 13px; }
.nf-section-title:first-child { margin-top: 0; }
.nf-metric-grid { display: grid; gap: 14px; margin: 0 0 22px; }
.nf-metric-grid.nf-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.nf-metric-grid.nf-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.nf-metric-grid.nf-cols-6 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.nf-metric-card {
  min-width: 0; min-height: 110px; box-sizing: border-box;
  background: var(--nf-surface); border: 1px solid var(--nf-border); border-radius: 13px;
  padding: 18px 19px 16px; box-shadow: var(--nf-shadow);
  display: flex; flex-direction: column; justify-content: space-between;
}
.nf-metric-label { color: var(--nf-secondary); font-size: 12px; font-weight: 550; line-height: 1.45; }
.nf-metric-value { color: var(--nf-text); font-size: 27px; line-height: 1.2; letter-spacing: -.025em; font-weight: 700; margin: 9px 0 6px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.nf-metric-note { color: var(--nf-muted); font-size: 11px; line-height: 1.4; }
.nf-metric-note.positive { color: var(--nf-green); }
.nf-metric-note.negative { color: var(--nf-red); }
.nf-badge { display: inline-flex; align-items: center; width: fit-content; padding: 4px 9px; border: 1px solid #BFDBFE; border-radius: 999px; background: #EFF6FF; color: #1D4ED8; font-size: 11px; font-weight: 600; line-height: 1.35; }
.nf-badge.success { color: #15803D; background: #F0FDF4; border-color: #BBF7D0; }
.nf-badge.warning { color: #B45309; background: #FFFBEB; border-color: #FDE68A; }
.nf-badge.danger { color: #B91C1C; background: #FEF2F2; border-color: #FECACA; }
.nf-badge.neutral { color: #475569; background: #F8FAFC; border-color: #E2E8F0; }
.nf-summary { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.nf-summary-title { font-family: 'Manrope', sans-serif; font-size: 20px; font-weight: 700; color: var(--nf-text); }
.nf-summary-sub { color: var(--nf-secondary); font-size: 13px; margin-top: 4px; }
.nf-info { background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 11px; padding: 14px 16px; color: #1E40AF; font-size: 13px; line-height: 1.6; }

/* Streamlit bordered containers become content cards */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--nf-surface) !important;
  border: 1px solid var(--nf-border) !important;
  border-radius: 14px !important;
  box-shadow: var(--nf-shadow) !important;
  padding: 18px 20px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVerticalBlockBorderWrapper"]) { box-shadow: none !important; }
[data-testid="stHorizontalBlock"] { gap: 16px !important; }
[data-testid="stColumn"] { min-width: 0; }

/* Metrics retained for backwards compatibility */
[data-testid="stMetric"] { background: transparent !important; border: 0 !important; box-shadow: none !important; padding: 0 !important; }
[data-testid="stMetricLabel"] p { color: var(--nf-secondary) !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: var(--nf-text) !important; font-size: 27px !important; font-weight: 700 !important; letter-spacing: -.025em !important; }

/* Inputs and selectors */
[data-testid="stWidgetLabel"] p { color: #475569 !important; font-size: 12px !important; font-weight: 550 !important; }
.stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input,
[data-baseweb="select"] > div, [data-baseweb="base-input"] {
  background: var(--nf-surface) !important;
  border-color: var(--nf-border-strong) !important;
  border-radius: 9px !important;
  color: var(--nf-text) !important;
  min-height: 40px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus,
[data-baseweb="select"] > div:focus-within, [data-baseweb="base-input"]:focus-within {
  border-color: var(--nf-blue) !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, .10) !important;
}
[data-baseweb="popover"] [role="listbox"] { background: #FFFFFF !important; border: 1px solid var(--nf-border) !important; border-radius: 10px !important; box-shadow: 0 12px 30px rgba(15, 23, 42, .12) !important; }
[data-baseweb="popover"] [role="option"] { color: var(--nf-text) !important; font-size: 13px !important; }
[data-baseweb="popover"] [aria-selected="true"], [data-baseweb="popover"] [role="option"]:hover { background: #EFF6FF !important; color: #1D4ED8 !important; }
input::placeholder { color: #94A3B8 !important; }

/* Buttons */
.stButton > button, .stDownloadButton > button {
  min-height: 40px !important;
  border-radius: 9px !important;
  padding: 9px 16px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  border: 1px solid var(--nf-border-strong) !important;
  background: var(--nf-surface) !important;
  color: #334155 !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .03) !important;
  transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover { background: #F8FAFC !important; border-color: #94A3B8 !important; color: var(--nf-text) !important; }
.stButton > button[kind="primary"] { background: var(--nf-blue) !important; border-color: var(--nf-blue) !important; color: #FFFFFF !important; box-shadow: 0 3px 8px rgba(37, 99, 235, .18) !important; }
.stButton > button[kind="primary"]:hover { background: var(--nf-blue-dark) !important; border-color: var(--nf-blue-dark) !important; color: #FFFFFF !important; }
button:focus-visible, input:focus-visible, [role="tab"]:focus-visible { outline: 3px solid rgba(37, 99, 235, .25) !important; outline-offset: 2px !important; }

/* Tables */
[data-testid="stDataFrame"] { background: #FFFFFF !important; border: 1px solid var(--nf-border) !important; border-radius: 11px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] [role="columnheader"], [data-testid="stDataFrame"] th { background: #F8FAFC !important; color: #475569 !important; font-size: 11px !important; font-weight: 650 !important; }
[data-testid="stDataFrame"] [role="gridcell"], [data-testid="stDataFrame"] td { color: var(--nf-text) !important; font-size: 12px !important; font-variant-numeric: tabular-nums; }

/* Tabs and expanders */
[data-testid="stTabs"] [role="tablist"] { gap: 20px !important; border-bottom: 1px solid var(--nf-border) !important; }
[data-testid="stTabs"] button[role="tab"] { background: transparent !important; border: 0 !important; border-bottom: 2px solid transparent !important; border-radius: 0 !important; color: var(--nf-secondary) !important; padding: 10px 1px 11px !important; font-size: 13px !important; font-weight: 550 !important; }
[data-testid="stTabs"] button[role="tab"]:hover { color: var(--nf-blue) !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: var(--nf-blue) !important; border-bottom-color: var(--nf-blue) !important; background: transparent !important; }
[data-testid="stTabContent"] { padding: 20px 0 0 !important; background: transparent !important; border: 0 !important; }
[data-testid="stExpander"] { background: var(--nf-surface) !important; border: 1px solid var(--nf-border) !important; border-radius: 12px !important; overflow: hidden !important; }
[data-testid="stExpander"] summary { background: #FFFFFF !important; color: var(--nf-text) !important; padding: 13px 16px !important; font-size: 13px !important; font-weight: 600 !important; }
[data-testid="stExpander"] summary:hover { background: #F8FAFC !important; }

/* Alerts and loading */
.stAlert { border-radius: 10px !important; border: 1px solid var(--nf-border) !important; font-size: 13px !important; }
[data-baseweb="notification"][kind="info"] { background: #EFF6FF !important; border-color: #BFDBFE !important; color: #1E40AF !important; }
[data-baseweb="notification"][kind="success"] { background: #F0FDF4 !important; border-color: #BBF7D0 !important; color: #15803D !important; }
[data-baseweb="notification"][kind="warning"] { background: #FFFBEB !important; border-color: #FDE68A !important; color: #B45309 !important; }
[data-baseweb="notification"][kind="error"] { background: #FEF2F2 !important; border-color: #FECACA !important; color: #B91C1C !important; }
.stSpinner > div { border-top-color: var(--nf-blue) !important; }

/* Responsive */
@media (max-width: 1100px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: 24px 24px 44px !important; }
  .nf-metric-grid.nf-cols-4, .nf-metric-grid.nf-cols-6 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 700px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: 20px 16px 36px !important; }
  .nf-page-title { font-size: 25px; }
  .nf-metric-grid.nf-cols-3, .nf-metric-grid.nf-cols-4, .nf-metric-grid.nf-cols-6 { grid-template-columns: 1fr; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; }
}
</style>
"""


def inject_global_styles() -> None:
    """Inject the shared presentation layer once per rerun."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def init_ui() -> None:
    inject_global_styles()


def page_header(title: str, description: str = "", icon: str = "") -> None:
    """Render the common page title group; legacy icon values are intentionally ignored."""
    st.markdown(
        f'<div class="nf-page-head"><h1 class="nf-page-title">{escape(title)}</h1>'
        + (f'<p class="nf-page-description">{escape(description)}</p>' if description else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def section_header(title: str, level: int = 2) -> None:
    st.markdown(f'<h2 class="nf-section-title">{escape(title)}</h2>', unsafe_allow_html=True)


def metric_grid(metrics: Iterable[dict[str, Any]], columns: int = 4) -> None:
    """Render real values in a responsive, consistently sized KPI grid."""
    cols = columns if columns in (3, 4, 6) else 4
    cards = []
    for metric in metrics:
        note = metric.get("note", "")
        tone = metric.get("tone", "")
        cards.append(
            '<div class="nf-metric-card">'
            f'<div class="nf-metric-label">{escape(str(metric.get("label", "")))}</div>'
            f'<div class="nf-metric-value">{escape(str(metric.get("value", "N/A")))}</div>'
            + (f'<div class="nf-metric-note {escape(tone)}">{escape(str(note))}</div>' if note else '<div class="nf-metric-note">&nbsp;</div>')
            + '</div>'
        )
    st.markdown(f'<div class="nf-metric-grid nf-cols-{cols}">{"".join(cards)}</div>', unsafe_allow_html=True)


def badge(text: str, tone: str = "neutral") -> str:
    return f'<span class="nf-badge {escape(tone)}">{escape(text)}</span>'


def get_status_badge(status: str) -> str:
    normalized = (status or "N/A").lower()
    if normalized in {"excellent", "good", "yes", "efficient"}:
        tone = "success"
    elif normalized in {"average", "warning", "review"}:
        tone = "warning"
    elif normalized in {"weak", "poor", "no"}:
        tone = "danger"
    else:
        tone = "neutral"
    return badge(status or "N/A", tone)


def info_card(title: str, content: str, icon: str = "") -> None:
    st.markdown(f'<div class="nf-info"><strong>{escape(title)}</strong><br>{escape(content)}</div>', unsafe_allow_html=True)


def get_plotly_theme() -> dict[str, Any]:
    return {
        "layout": {
            "font": {"family": "Inter, sans-serif", "color": COLORS["text_secondary"], "size": 12},
            "title": {"text": "", "font": {"family": "Manrope, Inter, sans-serif", "color": COLORS["text_primary"], "size": 16}, "x": 0.01, "xanchor": "left"},
            "paper_bgcolor": "#FFFFFF",
            "plot_bgcolor": "#FFFFFF",
            "colorway": COLORS["chart_palette"],
            "xaxis": {"gridcolor": "#EDF2F7", "zerolinecolor": "#CBD5E1", "linecolor": "#CBD5E1", "tickfont": {"color": "#64748B", "size": 11}, "title": {"font": {"color": "#64748B", "size": 12}}},
            "yaxis": {"gridcolor": "#EDF2F7", "zerolinecolor": "#CBD5E1", "linecolor": "#CBD5E1", "tickfont": {"color": "#64748B", "size": 11}, "title": {"font": {"color": "#64748B", "size": 12}}},
            "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"color": "#475569", "size": 11}},
            "hoverlabel": {"bgcolor": "#172033", "font": {"color": "#FFFFFF", "size": 12, "family": "Inter"}, "bordercolor": "#172033"},
            "margin": {"l": 56, "r": 28, "t": 54, "b": 48},
        }
    }


def apply_plotly_theme(fig, **kwargs) -> None:
    fig.update_layout(get_plotly_theme()["layout"], **kwargs)


def format_currency(value: Any, unit: str = "₹Cr") -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{unit} {float(value):,.0f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: Any, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_number(value: Any, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


__all__ = [
    "COLORS", "SPACING", "inject_global_styles", "init_ui", "page_header",
    "section_header", "metric_grid", "badge", "get_status_badge", "info_card",
    "get_plotly_theme", "apply_plotly_theme", "format_currency",
    "format_percentage", "format_number",
]
