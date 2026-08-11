"""
Day 35: Portfolio Summary PDF Generator.

Generates a single multi-page A4 PDF containing exactly one page per
company, with companies ordered alphabetically by ticker/company_id.

Each company page contains:
  1. Company name
  2. Ticker (company_id)
  3. Sector
  4. Exactly 6 KPIs:
     - ROE
     - ROCE
     - OPM
     - Debt-to-Equity
     - FCF Conversion
     - Revenue CAGR
  5. One trend arrow per KPI:
     ↑ = latest value improved numerically by > 2%
     ↓ = latest value declined numerically by > 2%
     → = change within ±2% (inclusive)

Trend interpretation is purely numerical for all metrics, including
Debt-to-Equity (a decrease in D/E still shows ↓).

KPI sources reuse the existing Day 33 / Day 31 helpers wherever possible.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    BaseDocTemplate,
    Frame,
)

# ── DB helpers ──
from src.dashboard.utils.db import (
    get_company_list,
    get_financial_ratios,
    get_pl,
    get_cashflow_data,
)

# ── Analytics ──
from src.analytics.cashflow import cash_conversion_ratio
from src.analytics.cashflow_kpis import _to_float
from src.analytics.cagr import calculate_cagr

from reportlab.platypus import PageTemplate


# ── Page dimensions ──
PAGE_WIDTH, PAGE_HEIGHT = A4

# ── KPI definitions ─────────────────────────────────────────────────────────
# The 6 KPIs required for the portfolio summary, in display order.
KPI_DEFINITIONS: List[Dict[str, Any]] = [
    {"key": "roe",        "label": "ROE",              "unit": "%", "decimal": 1, "color": "#2563eb"},
    {"key": "roce",       "label": "ROCE",             "unit": "%", "decimal": 1, "color": "#059669"},
    {"key": "opm",        "label": "OPM",              "unit": "%", "decimal": 1, "color": "#dc2626"},
    {"key": "debt_to_equity", "label": "Debt-to-Equity", "unit": "", "decimal": 2, "color": "#7c3aed"},
    {"key": "fcf_conv",   "label": "FCF Conversion",   "unit": "%", "decimal": 1, "color": "#0891b2"},
    {"key": "rev_cagr",   "label": "Revenue CAGR",     "unit": "%", "decimal": 1, "color": "#16a34a"},
]


# ── Styles ──────────────────────────────────────────────────────────────────
_styles = getSampleStyleSheet()

_style_page_title = ParagraphStyle(
    "PortfolioPageTitle",
    parent=_styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=19,
    textColor=colors.HexColor("#1a1a2e"),
    alignment=TA_CENTER,
    spaceAfter=2,
)

_style_company_info = ParagraphStyle(
    "PortfolioCompanyInfo",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    textColor=colors.HexColor("#444444"),
    alignment=TA_CENTER,
    spaceAfter=10,
)

_style_kpi_value = ParagraphStyle(
    "PortfolioKPIValue",
    parent=_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    textColor=colors.HexColor("#1a1a2e"),
    alignment=TA_CENTER,
)

_style_kpi_arrow = ParagraphStyle(
    "PortfolioKPIArrow",
    parent=_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=16,
    alignment=TA_CENTER,
)

_style_kpi_label = ParagraphStyle(
    "PortfolioKPILabel",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#555555"),
    alignment=TA_CENTER,
)

_style_footer = ParagraphStyle(
    "PortfolioFooter",
    parent=_styles["Normal"],
    fontName="Helvetica-Oblique",
    fontSize=7,
    leading=9,
    textColor=colors.HexColor("#999999"),
    alignment=TA_CENTER,
    spaceBefore=6,
)


# ── Pure helpers ────────────────────────────────────────────────────────────

def _calculate_trend_arrow(
    latest_val: Optional[float],
    previous_val: Optional[float],
) -> str:
    """
    Calculate a trend arrow based on numerical change between two values.

    Behavior:
      - If either value is None or NaN → "→"
      - If latest == previous → "→"
      - If previous is 0 (or extremely small) → compare numerically
      - Otherwise: relative_change = (latest - previous) / abs(previous) * 100
        - > 2  → "↑"
        - < -2 → "↓"
        - otherwise → "→"

    Note: ±2.0% exactly is FLAT (→).  Only strictly beyond ±2% becomes an arrow.
    The direction is purely numerical — a decrease in Debt-to-Equity still
    yields "↓".

    Args:
        latest_val: The latest metric value.
        previous_val: The preceding metric value.

    Returns:
        One of "↑", "↓", "→".
    """
    # Handle None / NaN
    if latest_val is None or previous_val is None:
        return "→"
    if math.isnan(latest_val) or math.isnan(previous_val):
        return "→"
    if math.isinf(latest_val) or math.isinf(previous_val):
        return "→"

    # Handle equality
    if latest_val == previous_val:
        return "→"

    # Handle zero / near-zero previous value (avoid division by zero)
    if abs(previous_val) < 1e-12:
        if latest_val > previous_val:
            return "↑"
        elif latest_val < previous_val:
            return "↓"
        else:
            return "→"

    relative_change = (latest_val - previous_val) / abs(previous_val) * 100.0

    if relative_change > 2.0:
        return "↑"
    elif relative_change < -2.0:
        return "↓"
    else:
        return "→"


def _safe_year(value: Any) -> Optional[int]:
    """Safely convert a year value to int, returning None for NaN/errors."""
    v = _to_float(value)
    if v is None:
        return None
    return int(v)


def _get_latest_year(df: pd.DataFrame) -> Optional[int]:
    """Return the latest year present in a DataFrame with a 'year' column."""
    if df is None or df.empty or "year" not in df.columns:
        return None
    try:
        years = df["year"].dropna().apply(lambda y: _safe_year(y)).dropna().tolist()
        if not years:
            return None
        return max(years)
    except Exception:
        return None


def _get_latest_row(df: pd.DataFrame, year: int) -> Optional[pd.Series]:
    """Return the row from *df* whose 'year' matches *year*, safely."""
    if df is None or df.empty or "year" not in df.columns:
        return None
    mask = df["year"].apply(lambda y: _safe_year(y) == year)
    matched = df[mask]
    if matched.empty:
        return None
    return matched.iloc[0]


def _get_previous_year(df: pd.DataFrame, latest: int) -> Optional[int]:
    """Return the year immediately before *latest* that exists in *df*."""
    if df is None or df.empty or "year" not in df.columns:
        return None
    years = sorted(
        set(
            y for y in df["year"].apply(_safe_year).dropna().tolist()
            if y is not None and y < latest
        ),
        reverse=True,
    )
    return years[0] if years else None


def _get_company_sector(company_id: str) -> str:
    """Return the broad sector for a company, or 'Unknown'."""
    try:
        from src.dashboard.utils.db import get_company_profile
        profile = get_company_profile(company_id)
        if profile and profile.get("sector"):
            return profile["sector"]
    except Exception:
        pass
    # Fallback: direct query
    try:
        import sqlite3
        from src.dashboard.utils.db import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT broad_sector FROM sectors WHERE company_id = ?",
            (company_id,),
        ).fetchone()
        conn.close()
        if row and row["broad_sector"]:
            return row["broad_sector"]
    except Exception:
        pass
    return "Unknown"


def _get_company_name(company_id: str) -> str:
    """Return the company name from the DB, falling back to the ID."""
    try:
        companies = get_company_list()
        for co in companies:
            if co["company_id"] == company_id:
                return co.get("company_name", company_id)
    except Exception:
        pass
    return company_id


def _extract_kpi_values(
    company_id: str,
) -> List[Tuple[Optional[float], Optional[float]]]:
    """
    Extract the 6 KPI (latest, previous) value pairs for *company_id*.

    For each KPI, returns a tuple of (latest_val, previous_val) where
    previous_val is the value from the immediately preceding year with data.

    Revenue CAGR uses a special comparison: the latest CAGR is computed
    from the full available sales history (same as Day 33), and the
    "previous" CAGR is computed by excluding the latest year and
    re-computing over the remaining window.  This follows the existing
    repository convention of using calculate_cagr() and does not invent
    a new CAGR formula.

    Returns:
        List of 6 (latest, previous) tuples in KPI_DEFINITIONS order.
    """
    # ── Fetch raw data ──
    try:
        fr_df = get_financial_ratios(company_id)
    except Exception:
        fr_df = pd.DataFrame()
    try:
        pl_df = get_pl(company_id)
    except Exception:
        pl_df = pd.DataFrame()
    try:
        cf_df = get_cashflow_data(company_id)
    except Exception:
        cf_df = pd.DataFrame()

    # ── Determine latest year ──
    latest_year = _get_latest_year(fr_df)
    if latest_year is None:
        latest_year = _get_latest_year(pl_df)
    if latest_year is None:
        latest_year = _get_latest_year(cf_df)

    # ── Determine previous year ──
    prev_year = None
    if latest_year is not None:
        for df in [fr_df, pl_df, cf_df]:
            prev_year = _get_previous_year(df, latest_year)
            if prev_year is not None:
                break

    result: List[Tuple[Optional[float], Optional[float]]] = []

    # ── Metric 1: ROE ──
    latest_roe = previous_roe = None
    if latest_year is not None and not fr_df.empty:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            latest_roe = _to_float(row.get("return_on_equity_pct"))
        if prev_year is not None:
            row = _get_latest_row(fr_df, prev_year)
            if row is not None:
                previous_roe = _to_float(row.get("return_on_equity_pct"))
    result.append((latest_roe, previous_roe))

    # ── Metric 2: ROCE ──
    latest_roce = previous_roce = None
    if latest_year is not None and not fr_df.empty:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            latest_roce = _to_float(row.get("return_on_capital_employed_pct"))
        if prev_year is not None:
            row = _get_latest_row(fr_df, prev_year)
            if row is not None:
                previous_roce = _to_float(row.get("return_on_capital_employed_pct"))
    result.append((latest_roce, previous_roce))

    # ── Metric 3: OPM ──
    latest_opm = previous_opm = None
    if latest_year is not None and not fr_df.empty:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            latest_opm = _to_float(row.get("operating_profit_margin_pct"))
        if prev_year is not None:
            row = _get_latest_row(fr_df, prev_year)
            if row is not None:
                previous_opm = _to_float(row.get("operating_profit_margin_pct"))
    # Fallback to P&L opm_percentage if not in financial_ratios
    if latest_opm is None and latest_year is not None and not pl_df.empty:
        row = _get_latest_row(pl_df, latest_year)
        if row is not None:
            latest_opm = _to_float(row.get("opm_percentage"))
    if previous_opm is None and prev_year is not None and not pl_df.empty:
        row = _get_latest_row(pl_df, prev_year)
        if row is not None:
            previous_opm = _to_float(row.get("opm_percentage"))
    result.append((latest_opm, previous_opm))

    # ── Metric 4: Debt-to-Equity ──
    latest_dte = previous_dte = None
    if latest_year is not None and not fr_df.empty:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            latest_dte = _to_float(row.get("debt_to_equity"))
        if prev_year is not None:
            row = _get_latest_row(fr_df, prev_year)
            if row is not None:
                previous_dte = _to_float(row.get("debt_to_equity"))
    result.append((latest_dte, previous_dte))

    # ── Metric 5: FCF Conversion ──
    # Uses cash_conversion_ratio (CFO / PAT) — same as Day 33 Day 31.
    latest_fcf_conv = previous_fcf_conv = None
    if latest_year is not None:
        latest_cfo = latest_pat = None
        if not cf_df.empty:
            row = _get_latest_row(cf_df, latest_year)
            if row is not None:
                latest_cfo = _to_float(row.get("operating_activity"))
        if not pl_df.empty:
            row = _get_latest_row(pl_df, latest_year)
            if row is not None:
                latest_pat = _to_float(row.get("net_profit"))
        if latest_cfo is not None and latest_pat is not None and latest_pat != 0:
            latest_fcf_conv = cash_conversion_ratio(latest_cfo, latest_pat) * 100

        if prev_year is not None:
            prev_cfo = prev_pat = None
            if not cf_df.empty:
                row = _get_latest_row(cf_df, prev_year)
                if row is not None:
                    prev_cfo = _to_float(row.get("operating_activity"))
            if not pl_df.empty:
                row = _get_latest_row(pl_df, prev_year)
                if row is not None:
                    prev_pat = _to_float(row.get("net_profit"))
            if prev_cfo is not None and prev_pat is not None and prev_pat != 0:
                previous_fcf_conv = cash_conversion_ratio(prev_cfo, prev_pat) * 100
    result.append((latest_fcf_conv, previous_fcf_conv))

    # ── Metric 6: Revenue CAGR ──
    # Uses the same calculate_cagr() as Day 33.
    # Latest CAGR: full available sales history.
    # Previous CAGR: recompute excluding the latest year.
    latest_cagr = previous_cagr = None
    try:
        if not pl_df.empty:
            pl_sorted = pl_df.sort_values("year", ascending=True)
            sales = [_to_float(v) for v in pl_sorted["sales"].tolist()]
            years = [_safe_year(v) for v in pl_sorted["year"].tolist()]

            # Build (year, sales) pairs with valid positive values
            pairs = [
                (y, s) for y, s in zip(years, sales)
                if y is not None and s is not None and s > 0
            ]

            # Latest CAGR: oldest to newest positive
            if len(pairs) >= 2:
                start_year, start_val = pairs[0]
                end_year, end_val = pairs[-1]
                n_years = end_year - start_year
                if n_years > 0:
                    latest_cagr = calculate_cagr(start_val, end_val, n_years)

            # Previous CAGR: exclude the latest year, recompute
            if len(pairs) >= 2:
                # Remove the most recent year's pair
                pairs_prev = pairs[:-1] if len(pairs) > 1 else pairs
                if len(pairs_prev) >= 2:
                    start_year_prev, start_val_prev = pairs_prev[0]
                    end_year_prev, end_val_prev = pairs_prev[-1]
                    n_years_prev = end_year_prev - start_year_prev
                    if n_years_prev > 0:
                        previous_cagr = calculate_cagr(
                            start_val_prev, end_val_prev, n_years_prev
                        )
    except Exception:
        latest_cagr = previous_cagr = None

    result.append((latest_cagr, previous_cagr))

    return result


# ── PDF building ─────────────────────────────────────────────────────────────

def _format_kpi_value(val: Optional[float], decimal: int, unit: str) -> str:
    """Format a KPI value for display."""
    if val is None:
        return "N/A"
    if math.isnan(val) or math.isinf(val):
        return "N/A"
    formatted = f"{val:.{decimal}f}"
    if unit:
        return f"{formatted}{unit}"
    return formatted


def _build_kpi_grid(kpi_values: List[Tuple[Optional[float], Optional[float]]]) -> Table:
    """Build a 2×3 grid of KPI tiles with trend arrows."""
    data = []
    for i, kpi_def in enumerate(KPI_DEFINITIONS):
        latest, previous = kpi_values[i]
        arrow = _calculate_trend_arrow(latest, previous)
        value_str = _format_kpi_value(latest, kpi_def["decimal"], kpi_def["unit"])
        label = kpi_def["label"]

        cell = (
            f"{value_str}\n"
            f"<font size=11 color='{kpi_def['color']}'>{arrow}</font>\n"
            f"<font size=7 color='#555555'>{label}</font>"
        )
        data.append([cell])

    table = Table(data, colWidths=[60 * mm], rowHeights=38 * mm, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUNDCOLOR", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
    ]))
    return table


def _build_kpi_card(
    value: Optional[float],
    previous: Optional[float],
    kpi_def: Dict[str, Any],
) -> Table:
    """Build a single KPI card with value and trend arrow."""
    arrow = _calculate_trend_arrow(value, previous)
    value_str = _format_kpi_value(value, kpi_def["decimal"], kpi_def["unit"])

    # Build cell content with value, arrow, and label
    cell_content = (
        f"<b>{value_str}</b>\n"
        f"<font size=14 color='{kpi_def['color']}'>{arrow}</font>\n"
        f"<font size=7 color='#555555'>{kpi_def['label']}</font>"
    )

    table = Table(
        [[cell_content]],
        colWidths=[40 * mm],
        rowHeights=[45 * mm],
    )
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("BACKGROUNDCOLOR", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def _build_kpi_table(kpi_values: List[Tuple[Optional[float], Optional[float]]]) -> Table:
    """
    Build a 2-column × 3-row table of KPI cards.

    Each cell shows: KPI value, trend arrow, and label.
    """
    # Build cell content for each KPI
    row1_cells = []
    row2_cells = []
    row3_cells = []

    for i, kpi_def in enumerate(KPI_DEFINITIONS):
        latest, previous = kpi_values[i]
        arrow = _calculate_trend_arrow(latest, previous)
        value_str = _format_kpi_value(latest, kpi_def["decimal"], kpi_def["unit"])

        cell_content = (
            f"<b>{value_str}</b>\n"
            f"<font size=14 color='{kpi_def['color']}'>{arrow}</font>\n"
            f"<font size=7 color='#555555'>{kpi_def['label']}</font>"
        )

        if i == 0:
            row1_cells.append(cell_content)
        elif i == 1:
            row1_cells.append(cell_content)
        elif i == 2:
            row2_cells.append(cell_content)
        elif i == 3:
            row2_cells.append(cell_content)
        elif i == 4:
            row3_cells.append(cell_content)
        elif i == 5:
            row3_cells.append(cell_content)

    table = Table(
        [row1_cells, row2_cells, row3_cells],
        colWidths=[75 * mm, 75 * mm],
        hAlign="CENTER",
    )
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d0d0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUNDCOLOR", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ]))
    return table


def _build_company_page(
    company_id: str,
    company_name: str,
    sector: str,
    kpi_values: List[Tuple[Optional[float], Optional[float]]],
) -> List[Any]:
    """Build the story elements for a single company's page."""

    story: List[Any] = []

    # ── Company header ──
    story.append(Paragraph(company_name, _style_page_title))
    story.append(Paragraph(
        f"{company_id}  |  {sector}",
        _style_company_info,
    ))

    # ── KPI table ──
    kpi_table = _build_kpi_table(kpi_values)
    story.append(kpi_table)

    # ── Footer ──
    story.append(Spacer(1, 8 * mm))
    now = datetime.now()
    story.append(Paragraph(
        f"Generated: {now.strftime('%Y-%m-%d')}  |  "
        f"Sprint 5 Portfolio Summary",
        _style_footer,
    ))

    # Force page break after this company (except for the last company)
    story.append(PageBreak())

    return story


def generate_portfolio_summary(output_path: str) -> str:
    """
    Generate a multi-page A4 PDF portfolio summary.

    One page per company, ordered alphabetically by ticker/company_id.

    Args:
        output_path: Path where the PDF will be written.

    Returns:
        The output path on success.
    """
    # ── Fetch all companies ──
    companies = get_company_list()
    # Sort alphabetically by company_id (ticker)
    companies_sorted = sorted(companies, key=lambda c: c["company_id"])

    # ── Ensure output dir exists ──
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # ── Build PDF ──
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    story: List[Any] = []

    for i, company in enumerate(companies_sorted):
        company_id = company["company_id"]
        company_name = company.get("company_name", company_id)
        sector = _get_company_sector(company_id)

        # Extract KPI values
        kpi_values = _extract_kpi_values(company_id)

        # Build page
        page_story = _build_company_page(
            company_id, company_name, sector, kpi_values
        )
        story.extend(page_story)

    # Remove trailing PageBreak
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story)

    return output_path


def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate portfolio summary PDF (Day 35).",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("reports", "portfolio", "portfolio_summary.pdf"),
        help="Output path for the PDF file.",
    )

    args = parser.parse_args()

    path = generate_portfolio_summary(args.output)
    print(f"Generated portfolio summary: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
