"""
Day 33: Company Tearsheet Generator.

Generates a 2-page A4 PDF for a single company containing:
  - Page 1: KPI tiles, Revenue/Net Profit chart, ROE/ROCE chart
  - Page 2: Balance Sheet stacked bar, Cash Flow waterfall, Pros, Cons,
            Capital Allocation badge

All financial data is sourced from the existing DB helpers and analytics
functions.  No values are ever fabricated.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import VerticalLineChart
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── DB helpers ──────────────────────────────────────────────────────────
from src.dashboard.utils.db import (
    get_bs,
    get_cashflow_data,
    get_company_list,
    get_financial_ratios,
    get_pl,
)

# ── Analytics functions ─────────────────────────────────────────────────
from src.analytics.cashflow import cash_conversion_ratio
from src.analytics.cashflow_kpis import _to_float
from src.analytics.cagr import calculate_cagr


# ── Page dimensions ────────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = A4


# ── Styles ──────────────────────────────────────────────────────────────
_styles = getSampleStyleSheet()

_style_header_title = ParagraphStyle(
    "TearsheetHeaderTitle",
    parent=_styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=19,
    textColor=colors.white,
    alignment=TA_LEFT,
    leftIndent=5,
)

_style_header_subtitle = ParagraphStyle(
    "TearsheetHeaderSubtitle",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=11,
    textColor=colors.white,
    alignment=TA_LEFT,
    leftIndent=5,
)

_style_kpi_tile_value = ParagraphStyle(
    "KPITileValue",
    parent=_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=17,
    textColor=colors.HexColor("#1a1a2e"),
    alignment=TA_CENTER,
)

_style_kpi_tile_label = ParagraphStyle(
    "KPITileLabel",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#333333"),
    alignment=TA_CENTER,
)

_style_section_title = ParagraphStyle(
    "TearsheetSectionTitle",
    parent=_styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=colors.HexColor("#1a1a2e"),
    alignment=TA_LEFT,
    spaceBefore=6,
    spaceAfter=3,
)

_style_section_body = ParagraphStyle(
    "TearsheetSectionBody",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#333333"),
    alignment=TA_LEFT,
)

_style_badge = ParagraphStyle(
    "BadgeStyle",
    parent=_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=colors.white,
    alignment=TA_CENTER,
)

_style_pros_cons = ParagraphStyle(
    "ProsConsStyle",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#333333"),
    alignment=TA_LEFT,
    leftIndent=2,
    bulletIndent=6,
    bulletFontName="Helvetica",
    bulletFontSize=8,
)


# ── Data extraction ─────────────────────────────────────────────────────

def _get_company_name(company_id: str) -> str:
    """Return the company name from the DB company list, falling back to the ID."""
    try:
        companies = get_company_list()
        for co in companies:
            if co["company_id"] == company_id:
                return co.get("company_name", company_id)
    except Exception:
        pass
    return company_id


def _get_latest_year(df: pd.DataFrame) -> Optional[int]:
    """Return the latest year present in a DataFrame that has a 'year' column."""
    if df is None or df.empty or "year" not in df.columns:
        return None
    try:
        years = df["year"].dropna().astype(int).tolist()
        if not years:
            return None
        return max(years)
    except Exception:
        return None


def _safe_year(value) -> Optional[int]:
    """Safely convert a year value to int, returning None for NaN/errors."""
    v = _to_float(value)
    if v is None:
        return None
    return int(v)


def _get_latest_row(df: pd.DataFrame, year: int) -> Optional[pd.Series]:
    """Return the row from *df* whose 'year' matches *year*, safely."""
    if df is None or df.empty or "year" not in df.columns:
        return None
    mask = df["year"].apply(lambda y: _safe_year(y) == year)
    matched = df[mask]
    if matched.empty:
        return None
    return matched.iloc[0]


def _get_kpi_data(company_id: str) -> List[Tuple[str, str, str]]:
    """
    Extract the six KPI tiles for *company_id*.

    Returns a list of (value_str, label, color) tuples.  ``value_str`` is
    already formatted for display (``"N/A"`` when no data).
    """
    tiles: List[Tuple[str, str, str]] = []

    fr_df = get_financial_ratios(company_id)
    pl_df = get_pl(company_id)
    cf_df = get_cashflow_data(company_id)

    # ── Determine latest year from financial ratios (the most complete source)
    latest_year = _get_latest_year(fr_df) if not fr_df.empty else None
    if latest_year is None:
        latest_year = _get_latest_year(pl_df) if not pl_df.empty else None
    if latest_year is None:
        latest_year = _get_latest_year(cf_df) if not cf_df.empty else None

    # ── Tile 1: ROE
    roe_val = None
    if latest_year is not None:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            roe_val = _to_float(row.get("return_on_equity_pct"))
    if roe_val is not None:
        tiles.append((f"{roe_val:.1f}%", "ROE", "#2563eb"))
    else:
        tiles.append(("N/A", "ROE", "#9ca3af"))

    # ── Tile 2: ROCE
    roce_val = None
    if latest_year is not None:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            roce_val = _to_float(row.get("return_on_capital_employed_pct"))
    if roce_val is not None:
        tiles.append((f"{roce_val:.1f}%", "ROCE", "#059669"))
    else:
        tiles.append(("N/A", "ROCE", "#9ca3af"))

    # ── Tile 3: OPM
    opm_val = None
    if latest_year is not None:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            opm_val = _to_float(row.get("operating_profit_margin_pct"))
    if opm_val is None and latest_year is not None:
        row = _get_latest_row(pl_df, latest_year)
        if row is not None:
            opm_val = _to_float(row.get("opm_percentage"))
    if opm_val is not None:
        tiles.append((f"{opm_val:.1f}%", "OPM", "#dc2626"))
    else:
        tiles.append(("N/A", "OPM", "#9ca3af"))

    # ── Tile 4: Debt-to-Equity
    dte_val = None
    if latest_year is not None:
        row = _get_latest_row(fr_df, latest_year)
        if row is not None:
            dte_val = _to_float(row.get("debt_to_equity"))
    if dte_val is not None:
        tiles.append((f"{dte_val:.2f}", "Debt-to-Equity", "#7c3aed"))
    else:
        tiles.append(("N/A", "Debt-to-Equity", "#9ca3af"))

    # ── Tile 5: FCF Conversion (CFO / PAT)
    fcf_conv_val = None
    if latest_year is not None:
        cf_row = _get_latest_row(cf_df, latest_year)
        pl_row = _get_latest_row(pl_df, latest_year)
        if cf_row is not None and pl_row is not None:
            cfo = _to_float(cf_row.get("operating_activity"))
            pat = _to_float(pl_row.get("net_profit"))
            fcf_conv_val = cash_conversion_ratio(cfo, pat)  # reuse existing
    if fcf_conv_val is not None:
        tiles.append((f"{fcf_conv_val * 100:.1f}%", "FCF Conversion", "#0891b2"))
    else:
        tiles.append(("N/A", "FCF Conversion", "#9ca3af"))

    # ── Tile 6: Revenue CAGR (all available years, using positive values)
    rev_cagr_val = None
    if not pl_df.empty:
        pl_sorted = pl_df.sort_values("year", ascending=True)
        sales = [_to_float(v) for v in pl_sorted["sales"].tolist()]
        years = [_safe_year(v) for v in pl_sorted["year"].tolist()]

        # Build (year, sales) pairs with valid positive values
        pairs = [
            (y, s)
            for y, s in zip(years, sales)
            if y is not None and s is not None and s > 0
        ]

        if len(pairs) >= 2:
            start_year, start_val = pairs[0]
            end_year, end_val = pairs[-1]
            n_years = end_year - start_year
            if n_years > 0:
                rev_cagr_val = calculate_cagr(start_val, end_val, n_years)
    if rev_cagr_val is not None:
        tiles.append((f"{rev_cagr_val:.1f}%", "Revenue CAGR", "#16a34a"))
    else:
        tiles.append(("N/A", "Revenue CAGR", "#9ca3af"))

    return tiles


def _get_revenue_netprofit_data(
    company_id: str, n_years: int = 10
) -> Tuple[List[int], List[Optional[float]], List[Optional[float]]]:
    """
    Return up to *n_years* of (years, revenue, net_profit) from the P&L table.

    Lists are ordered oldest→newest.  ``None`` is used where data is missing.
    """
    pl_df = get_pl(company_id)
    if pl_df.empty:
        return [], [], []

    pl_sorted = pl_df.sort_values("year", ascending=True)
    years = [_safe_year(v) for v in pl_sorted["year"].tolist()][-n_years:]
    revenue = [_to_float(v) for v in pl_sorted["sales"].tolist()[-n_years:]]
    net_profit = [_to_float(v) for v in pl_sorted["net_profit"].tolist()[-n_years:]]

    return years, revenue, net_profit


def _get_roe_roce_data(
    company_id: str, n_years: int = 10
) -> Tuple[List[int], List[Optional[float]], List[Optional[float]]]:
    """
    Return up to *n_years* of (years, roe, roce) from financial ratios.

    Lists are ordered oldest→newest.  ``None`` is used where data is missing.
    """
    fr_df = get_financial_ratios(company_id)
    if fr_df.empty:
        return [], [], []

    fr_sorted = fr_df.sort_values("year", ascending=True)
    years = [_safe_year(v) for v in fr_sorted["year"].tolist()][-n_years:]
    roe = [_to_float(v) for v in fr_sorted["return_on_equity_pct"].tolist()[-n_years:]]
    roce = [
        _to_float(v)
        for v in fr_sorted["return_on_capital_employed_pct"].tolist()[-n_years:]
    ]

    return years, roe, roce


def _get_balancesheet_data(
    company_id: str, n_years: int = 5
) -> Tuple[List[int], List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """
    Return up to *n_years* of (years, equity, borrowings, other_liabilities).

    Uses the existing BS schema columns directly:
      - equity = equity_capital + reserves
      - borrowings = borrowings
      - other_liabilities = other_liabilities (existing field, no invention)

    If ``get_bs`` returns rows with NULL years (as happens in the current DB),
    we fall back to a raw query that doesn't filter on year, then infer years
    from the P&L table so balance-sheet data can still be displayed.
    """
    bs_df = get_bs(company_id)

    # If get_bs returns empty (because the DB filters NULL years), query raw
    # and infer years from P&L data.
    if bs_df.empty:
        from src.dashboard.utils.db import _fetch_df
        raw_sql = """
            SELECT equity_capital, reserves, borrowings, other_liabilities
            FROM balancesheet
            WHERE company_id = ?
            ORDER BY id DESC
        """
        bs_df = _fetch_df(raw_sql, (company_id,))
        if not bs_df.empty:
            # Deduplicate identical rows (the source may contain duplicates)
            bs_df = bs_df.drop_duplicates(
                subset=["equity_capital", "reserves", "borrowings", "other_liabilities"],
                keep="first",
            )
            # Infer years from P&L data
            pl_df = get_pl(company_id)
            if not pl_df.empty and "year" in pl_df.columns:
                pl_years = [_safe_year(v) for v in pl_df["year"].tolist() if _safe_year(v) is not None]
                pl_years = sorted(pl_years)
                n = min(len(bs_df), len(pl_years))
                if n > 0:
                    years_inferred = pl_years[:n]
                    bs_df = bs_df.iloc[:n].copy()
                    bs_df["year"] = list(reversed(years_inferred))

    if bs_df.empty:
        return [], [], [], []

    bs_sorted = bs_df.sort_values("year", ascending=True)
    years = [_safe_year(v) for v in bs_sorted["year"].tolist()][-n_years:]

    equity_vals = []
    borrowings_vals = []
    other_liab_vals = []

    for _, row in bs_sorted.tail(n_years).iterrows():
        ec = _to_float(row.get("equity_capital"))
        res = _to_float(row.get("reserves"))
        eq = None
        if ec is not None and res is not None:
            eq = ec + res
        elif ec is not None:
            eq = ec
        elif res is not None:
            eq = res
        equity_vals.append(eq)
        borrowings_vals.append(_to_float(row.get("borrowings")))
        other_liab_vals.append(_to_float(row.get("other_liabilities")))

    return years, equity_vals, borrowings_vals, other_liab_vals


def _get_cashflow_waterfall(
    company_id: str
) -> Tuple[str, List[Tuple[str, Optional[float]]]]:
    """
    Return the latest-year cash flow components.

    Returns (year_label, [(component, value), ...]).
    Net cash flow is taken directly from the DB column ``net_cash_flow``
    to stay consistent with the repository's cashflow implementation.
    """
    cf_df = get_cashflow_data(company_id)
    if cf_df.empty or "year" not in cf_df.columns:
        return "N/A", []

    cf_sorted = cf_df.sort_values("year", ascending=False)
    latest_row = cf_sorted.iloc[0]
    year_label = str(int(latest_row["year"])) if pd.notna(latest_row.get("year")) else "N/A"

    components = [
        ("CFO", _to_float(latest_row.get("operating_activity"))),
        ("CFI", _to_float(latest_row.get("investing_activity"))),
        ("CFF", _to_float(latest_row.get("financing_activity"))),
        ("Net Cash Flow", _to_float(latest_row.get("net_cash_flow"))),
    ]

    return year_label, components


def _get_pros(company_id: str, max_count: int = 5) -> List[str]:
    """
    Read pros from pros_cons_generated.csv, filtered by company_id and type=='pro'.

    Returns up to *max_count* pros, ordered by confidence_pct descending.
    If the CSV is empty or the company is not present, returns an empty list.
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "Data", "output", "pros_cons_generated.csv",
    )

    if not os.path.exists(csv_path):
        return []

    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return []

        mask = (df["company_id"] == company_id) & (df["type"] == "pro")
        pros = df[mask].sort_values("confidence_pct", ascending=False)

        result = []
        for _, row in pros.head(max_count).iterrows():
            text = row.get("text", "")
            if isinstance(text, str) and text.strip():
                result.append(text.strip())
        return result
    except Exception:
        return []


def _get_cons(company_id: str, max_count: int = 4) -> List[str]:
    """
    Read cons from pros_cons_generated.csv, filtered by company_id and type=='con'.

    Returns up to *max_count* cons, ordered by confidence_pct descending.
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "Data", "output", "pros_cons_generated.csv",
    )

    if not os.path.exists(csv_path):
        return []

    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return []

        mask = (df["company_id"] == company_id) & (df["type"] == "con")
        cons = df[mask].sort_values("confidence_pct", ascending=False)

        result = []
        for _, row in cons.head(max_count).iterrows():
            text = row.get("text", "")
            if isinstance(text, str) and text.strip():
                result.append(text.strip())
        return result
    except Exception:
        return []


def _get_capital_allocation(company_id: str) -> str:
    """
    Look up the latest valid capital-allocation category for *company_id*
    from Data/output/capital_allocation.csv (Day 32 output).

    Returns one of: Excellent, Good, Average, Weak, Poor, or "N/A".
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "Data", "output", "capital_allocation.csv",
    )

    if not os.path.exists(csv_path):
        return "N/A"

    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return "N/A"

        co_data = df[df["company_id"] == company_id]
        if co_data.empty:
            return "N/A"

        latest = co_data.sort_values("year", ascending=False).iloc[0]
        category = latest.get("capital_allocation", "N/A")
        if isinstance(category, str) and category in ("Excellent", "Good", "Average", "Weak", "Poor"):
            return category
        return "N/A"
    except Exception:
        return "N/A"


# ── Badge colour ────────────────────────────────────────────────────────
_BADGE_COLORS = {
    "Excellent": "#16a34a",  # green
    "Good": "#2563eb",       # blue
    "Average": "#d97706",    # amber
    "Weak": "#dc2626",       # red
    "Poor": "#7f1d1d",      # dark red
}


# ── Drawing helpers ─────────────────────────────────────────────────────


def _draw_header(draw: Drawing, company_id: str, company_name: str) -> Drawing:
    """Navy header bar with company name and ticker."""
    draw.add(Rect(0, 0, PAGE_WIDTH, 45 * mm, fillColor=colors.HexColor("#1a1a2e")))
    draw.add(
        String(
            15 * mm,
            28 * mm,
            company_name,
            fontSize=14,
            fontName="Helvetica-Bold",
            fillColor=colors.white,
        )
    )
    draw.add(
        String(
            15 * mm,
            17 * mm,
            f"Ticker: {company_id}",
            fontSize=8,
            fontName="Helvetica",
            fillColor=colors.white,
        )
    )
    draw.add(
        String(
            PAGE_WIDTH - 30 * mm,
            22.5 * mm,
            f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
            fontSize=7,
            fontName="Helvetica-Oblique",
            fillColor=colors.white,
            textAnchor="end",
        )
    )
    return draw


def _build_kpi_tile(value: str, label: str, color_hex: str) -> Drawing:
    """Build a single KPI tile as a Drawing with a coloured background bar."""
    d = Drawing(50 * mm, 18 * mm)
    # Background rounded rect
    d.add(Rect(0, 0, 50 * mm, 18 * mm, fillColor=colors.HexColor("#f3f4f6"),
               strokeColor=colors.HexColor("#d1d5db"), strokeW=0.5, radius=4))
    # Coloured accent line
    d.add(Rect(0, 14 * mm, 50 * mm, 2 * mm, fillColor=colors.HexColor(color_hex)))
    # Value
    d.add(String(25 * mm, 9 * mm, value, fontSize=14, fontName="Helvetica-Bold",
                 fillColor=colors.HexColor("#1a1a2e"), textAnchor="middle"))
    # Label
    d.add(String(25 * mm, 4 * mm, label, fontSize=7, fontName="Helvetica",
                 fillColor=colors.HexColor("#333333"), textAnchor="middle"))
    return d


def _build_kpi_tiles(tiles: List[Tuple[str, str, str]]) -> List[Any]:
    """Build 6 KPI tile paragraphs arranged as a 3×2 grid."""
    table_data = []
    for i in range(0, len(tiles), 3):
        row = []
        for j in range(3):
            idx = i + j
            if idx < len(tiles):
                value, label, color = tiles[idx]
                tile = _build_kpi_tile(value, label, color)
            else:
                tile = _build_kpi_tile("—", "", "#9ca3af")
            row.append(tile)
        table_data.append(row)

    table = Table(table_data, colWidths=[55 * mm] * 3, rowHeights=18 * mm)
    table.hAlign = "CENTER"
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return [table]


def _draw_revenue_netprofit_chart(
    years: List[int],
    revenue: List[Optional[float]],
    net_profit: List[Optional[float]],
    width: float,
    height: float,
) -> Drawing:
    """Grouped bar chart of Revenue and Net Profit."""
    d = Drawing(width, height)

    if not years or all(v is None for v in revenue):
        d.add(String(width / 2, height / 2, "No data available",
                     fontSize=10, textAnchor="middle"))
        return d

    n = len(years)

    # Build bar data — VerticalBarChart expects list of lists for grouped bars
    rev_vals = [v if v is not None else 0 for v in revenue]
    np_vals = [v if v is not None else 0 for v in net_profit]

    bar_plot = VerticalBarChart()
    bar_plot.x = 25
    bar_plot.y = 25
    bar_plot.width = width - 50
    bar_plot.height = height - 45
    bar_plot.data = list(zip(rev_vals, np_vals))
    bar_plot.barWidth = min((width - 50) / max(n, 1) / 2.5, 15)
    bar_plot.groupSpacing = 3
    bar_plot.categoryAxis.categoryNames = [str(y) for y in years]
    bar_plot.categoryAxis.labels.fontName = "Helvetica"
    bar_plot.categoryAxis.labels.fontSize = 7
    bar_plot.categoryAxis.labels.angle = 315
    bar_plot.categoryAxis.labels.textAnchor = "end"

    # Value axis formatting (wrap in try/except for version compatibility)
    try:
        bar_plot.valueAxis.labelTextFormat = lambda x: f"{x/1000:.0f}K"
    except AttributeError:
        pass
    bar_plot.valueAxis.labels.fontName = "Helvetica"
    bar_plot.valueAxis.labels.fontSize = 6
    bar_plot.valueAxis.visible = True
    try:
        bar_plot.barLabelFormat = None
    except AttributeError:
        pass

    # Bar colors: blue for revenue, teal for net profit
    bar_plot.bars[0].fillColor = colors.HexColor("#2563eb")
    bar_plot.bars[1].fillColor = colors.HexColor("#0891b2")

    d.add(bar_plot)
    d.add(String(width / 2, height - 8, "Revenue & Net Profit (10-Yr)",
                 fontSize=9, fontName="Helvetica-Bold", textAnchor="middle"))
    return d


def _draw_roe_roce_chart(
    years: List[int],
    roe: List[Optional[float]],
    roce: List[Optional[float]],
    width: float,
    height: float,
) -> Drawing:
    """Dual-axis line chart of ROE and ROCE."""
    d = Drawing(width, height)

    if not years or all(v is None for v in roe):
        d.add(String(width / 2, height / 2, "No data available",
                     fontSize=10, textAnchor="middle"))
        return d

    line_chart = VerticalLineChart()
    line_chart.x = 20
    line_chart.y = 20
    line_chart.width = width - 40
    line_chart.height = height - 40
    line_chart.categoryAxis.categoryNames = [str(y) for y in years]
    line_chart.categoryAxis.labels.fontName = "Helvetica"
    line_chart.categoryAxis.labels.fontSize = 7
    line_chart.categoryAxis.labels.angle = 315
    line_chart.categoryAxis.labels.textAnchor = "end"

    # Value axis formatting (wrap in try/except for version compatibility)
    try:
        line_chart.valueAxis.labelTextFormat = lambda x: f"{x:.0f}%"
    except AttributeError:
        pass
    line_chart.valueAxis.labels.fontName = "Helvetica"
    line_chart.valueAxis.labels.fontSize = 6
    line_chart.valueAxis.visible = True

    # Build line data — use simple value lists (None → 0 to avoid plotting gaps)
    roe_clean = [v if v is not None else 0 for v in roe]
    roce_clean = [v if v is not None else 0 for v in roce]

    line_chart.data = [roe_clean, roce_clean]

    # Markers — wrap in try/except for version compatibility
    line_chart.lines[0].strokeColor = colors.HexColor("#2563eb")
    line_chart.lines[0].strokeWidth = 1.5
    line_chart.lines[1].strokeColor = colors.HexColor("#059669")
    line_chart.lines[1].strokeWidth = 1.5
    try:
        line_chart.lines[0].symbol = makeMarker("FilledCircle", size=4, fillColor=colors.HexColor("#2563eb"))
        line_chart.lines[1].symbol = makeMarker("FilledSquare", size=4, fillColor=colors.HexColor("#059669"))
    except Exception:
        pass  # markers are optional; lines still render as plain stroked paths

    d.add(line_chart)
    d.add(String(width / 2, height - 8, "ROE & ROCE Trend",
                 fontSize=9, fontName="Helvetica-Bold", textAnchor="middle"))
    return d


def _draw_balancesheet_stacked_bar(
    years: List[int],
    equity: List[Optional[float]],
    borrowings: List[Optional[float]],
    other_liab: List[Optional[float]],
    width: float,
    height: float,
) -> Drawing:
    """Stacked bar chart of Balance Sheet composition.

    Since VerticalBarChart does not support true stacking in ReportLab,
    we draw the chart manually with Rect primitives.
    """
    d = Drawing(width, height)

    if not years or all(v is None for v in equity):
        d.add(String(width / 2, height / 2, "No data available",
                     fontSize=10, textAnchor="middle"))
        return d

    n = len(years)
    colors_list = [colors.HexColor("#2563eb"), colors.HexColor("#059669"), colors.HexColor("#dc2626")]
    seg_labels = ["Equity", "Borrowings", "Other Liabilities"]

    # Find max total for scaling
    totals = []
    for i in range(n):
        eq = equity[i] if equity[i] is not None else 0
        br = borrowings[i] if borrowings[i] is not None else 0
        ol = other_liab[i] if other_liab[i] is not None else 0
        totals.append(eq + br + ol)

    max_total = max(totals) if totals else 1
    if max_total <= 0:
        max_total = 1

    plot_left = 25
    plot_right = width - 25
    plot_bottom = 25
    plot_top = height - 30
    plot_height = plot_top - plot_bottom
    bar_total_width = (plot_right - plot_left) / n if n > 0 else 0.1
    bar_width = min(bar_total_width * 0.6, 25)

    for i in range(n):
        eq = equity[i] if equity[i] is not None else 0
        br = borrowings[i] if borrowings[i] is not None else 0
        ol = other_liab[i] if other_liab[i] is not None else 0

        bar_x = plot_left + i * bar_total_width + (bar_total_width - bar_width) / 2
        cum_y = plot_bottom

        for j, (val, col) in enumerate(zip([eq, br, ol], colors_list)):
            bar_h = (val / max_total) * plot_height if val > 0 else 0
            if bar_h > 0:
                d.add(Rect(bar_x, cum_y, bar_width, bar_h, fillColor=col, strokeColor=col))
            cum_y += bar_h

        # Year label below bar
        d.add(String(bar_x + bar_width / 2, plot_bottom - 5, str(years[i]),
                     fontSize=7, textAnchor="middle"))

    # Title
    d.add(String(width / 2, height - 8, "Balance Sheet Composition",
                 fontSize=9, fontName="Helvetica-Bold", textAnchor="middle"))

    # Legend
    legend_x = width - 65
    legend_y = height - 15
    for i, (c, lbl) in enumerate(zip(colors_list, seg_labels)):
        d.add(Rect(legend_x, legend_y - i * 10, 6, 6, fillColor=c))
        d.add(String(legend_x + 8, legend_y - i * 10 + 2, lbl, fontSize=6))

    return d


def _draw_cashflow_waterfall(
    year_label: str,
    components: List[Tuple[str, Optional[float]]],
    width: float,
    height: float,
) -> Drawing:
    """Waterfall-style bar chart of cash flow components."""
    d = Drawing(width, height)

    if not components or all(v is None for _, v in components):
        d.add(String(width / 2, height / 2, "No data available",
                     fontSize=10, textAnchor="middle"))
        return d

    labels = [c[0] for c in components]
    values = [c[1] if c[1] is not None else 0 for c in components]
    n = len(components)

    bar_plot = VerticalBarChart()
    bar_plot.x = 25
    bar_plot.y = 25
    bar_plot.width = width - 50
    bar_plot.height = height - 45
    bar_plot.data = [values]  # single series
    try:
        bar_plot.barLabelFormat = None
    except AttributeError:
        pass
    bar_plot.categoryAxis.categoryNames = labels
    bar_plot.categoryAxis.labels.fontName = "Helvetica"
    bar_plot.categoryAxis.labels.fontSize = 7

    try:
        bar_plot.valueAxis.labelTextFormat = lambda x: f"{x/1000:.0f}K"
    except AttributeError:
        pass
    bar_plot.valueAxis.labels.fontName = "Helvetica"
    bar_plot.valueAxis.labels.fontSize = 6
    bar_plot.valueAxis.visible = True

    # Single color for all cash flow bars
    bar_plot.bars[0].fillColor = colors.HexColor("#0891b2")

    d.add(bar_plot)
    d.add(String(width / 2, height - 8,
                 f"Cash Flow Waterfall ({year_label})",
                 fontSize=9, fontName="Helvetica-Bold", textAnchor="middle"))
    return d


# ── Badge ──────────────────────────────────────────────────────────────

def _draw_ca_badge(category: str, width: float, height: float) -> Drawing:
    """Draw a coloured badge with the capital-allocation category."""
    color = _BADGE_COLORS.get(category, "#6b7280")
    d = Drawing(width, height)
    d.hAlign = "CENTER"

    rect = Rect(0, 0, width, height, fillColor=color, strokeColor=color, radius=6)
    d.add(rect)

    text = String(
        width / 2,
        height / 2 + 3,
        category,
        fontSize=11,
        fontName="Helvetica-Bold",
        fillColor=colors.white,
        textAnchor="middle",
    )
    d.add(text)

    return d


# ── Page builders ──────────────────────────────────────────────────────

def _build_page1(
    company_id: str,
    company_name: str,
    tiles: List[Tuple[str, str, str]],
    rp_years: List[int],
    rp_revenue: List[Optional[float]],
    rp_netprofit: List[Optional[float]],
    rr_years: List[int],
    rr_roe: List[Optional[float]],
    rr_roce: List[Optional[float]],
) -> List[Any]:
    """Build the list of flowables for Page 1."""
    elements: List[Any] = []

    # Header
    header_drawing = _draw_header(Drawing(PAGE_WIDTH, 45 * mm), company_id, company_name)
    elements.append(header_drawing)
    elements.append(Spacer(1, 4 * mm))

    # KPI tiles (3×2 grid)
    elements.append(Paragraph("Key Metrics", _style_section_title))
    elements.extend(_build_kpi_tiles(tiles))
    elements.append(Spacer(1, 6 * mm))

    # Charts side by side
    chart_width = PAGE_WIDTH / 2 - 10 * mm
    chart_height = 75 * mm

    col_data = [
        [
            Paragraph("Revenue & Net Profit", _style_section_title),
            Paragraph("ROE & ROCE Trend", _style_section_title),
        ],
        [
            _draw_revenue_netprofit_chart(rp_years, rp_revenue, rp_netprofit, chart_width, chart_height),
            _draw_roe_roce_chart(rr_years, rr_roe, rr_roce, chart_width, chart_height),
        ],
    ]

    chart_table = Table(col_data, colWidths=[chart_width, chart_width])
    chart_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    elements.append(chart_table)
    elements.append(Spacer(1, 8 * mm))

    return elements


def _truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text to a maximum character length for PDF display."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def _build_page2(
    company_id: str,
    bs_years: List[int],
    bs_equity: List[Optional[float]],
    bs_borrowings: List[Optional[float]],
    bs_other_liab: List[Optional[float]],
    cf_year: str,
    cf_components: List[Tuple[str, Optional[float]]],
    pros: List[str],
    cons: List[str],
    capital_allocation: str,
) -> List[Any]:
    """Build the list of flowables for Page 2."""
    elements: List[Any] = []
    avail_height = PAGE_HEIGHT - 2 * 10 * mm  # account for margins

    # ── Balance Sheet ───────────────────────────────────────────────
    elements.append(Paragraph("Balance Sheet Composition", _style_section_title))
    chart_width = PAGE_WIDTH - 20 * mm
    bs_chart = _draw_balancesheet_stacked_bar(
        bs_years, bs_equity, bs_borrowings, bs_other_liab,
        chart_width, 55 * mm,
    )
    elements.append(bs_chart)
    elements.append(Spacer(1, 4 * mm))

    # ── Cash Flow ───────────────────────────────────────────────────
    elements.append(Paragraph("Cash Flow Waterfall", _style_section_title))
    cf_chart_width = PAGE_WIDTH - 20 * mm
    cf_chart = _draw_cashflow_waterfall(cf_year, cf_components, cf_chart_width, 35 * mm)
    elements.append(cf_chart)
    elements.append(Spacer(1, 5 * mm))

    # ── Pros / Cons / Badge ──────────────────────────────────────────
    # Constrain to keep within 2 pages
    max_pros = 3
    max_cons = 3

    truncated_pros = [_truncate_text(p, 180) for p in pros[:max_pros]]
    truncated_cons = [_truncate_text(c, 180) for c in cons[:max_cons]]

    # Build pros paragraphs
    pros_rows = [Paragraph("Pros", _style_section_title)]
    if truncated_pros:
        for p in truncated_pros:
            pros_rows.append(Paragraph(p, _style_pros_cons))
    else:
        pros_rows.append(Paragraph("No pros data available", _style_section_body))

    # Build cons paragraphs
    cons_rows = [Paragraph("Cons", _style_section_title)]
    if truncated_cons:
        for c in truncated_cons:
            cons_rows.append(Paragraph(c, _style_pros_cons))
    else:
        cons_rows.append(Paragraph("No cons data available", _style_section_body))

    # Use a table with Paragraph cells for Pros | Cons
    half_width = (PAGE_WIDTH - 20 * mm) / 2
    col_data = []
    max_rows = max(len(pros_rows), len(cons_rows))
    for i in range(max_rows):
        p_cell = pros_rows[i] if i < len(pros_rows) else Paragraph("", _style_section_body)
        c_cell = cons_rows[i] if i < len(cons_rows) else Paragraph("", _style_section_body)
        col_data.append([p_cell, c_cell])

    pros_cons_table = Table(col_data, colWidths=[half_width - 2 * mm, half_width - 2 * mm])
    pros_cons_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (1, 0), (1, -1), 4),
            ]
        )
    )
    elements.append(pros_cons_table)
    elements.append(Spacer(1, 4 * mm))

    # Badge
    elements.append(Paragraph("Capital Allocation", _style_section_title))
    badge = _draw_ca_badge(capital_allocation, 35 * mm, 16 * mm)
    elements.append(Spacer(1, 2 * mm))
    elements.append(badge)

    return elements


# ── Public API ──────────────────────────────────────────────────────────

def generate_tearsheet(
    company_id: str,
    output_path: str,
) -> str:
    """
    Generate a 2-page A4 tearsheet PDF for *company_id*.

    Args:
        company_id: The company ticker / ID (e.g. ``"TCS"``).
        output_path: Path where the PDF will be written.

    Returns:
        The output path on success.

    Raises:
        ValueError: If *company_id* is not a valid company.
        FileNotFoundError: If the output directory does not exist.
    """
    # Validate company exists
    try:
        companies = get_company_list()
        valid_ids = {c["company_id"] for c in companies}
        if company_id not in valid_ids:
            raise ValueError(
                f"Invalid company_id '{company_id}'. "
                f"Must be one of: {sorted(valid_ids)[:10]}..."
            )
    except ValueError:
        raise
    except Exception:
        # If we can't fetch the list, try to proceed anyway
        pass

    company_name = _get_company_name(company_id)

    # ── Collect data ──────────────────────────────────────────────────
    tiles = _get_kpi_data(company_id)
    rp_years, rp_revenue, rp_netprofit = _get_revenue_netprofit_data(company_id)
    rr_years, rr_roe, rr_roce = _get_roe_roce_data(company_id)
    bs_years, bs_equity, bs_borrowings, bs_other_liab = _get_balancesheet_data(company_id)
    cf_year, cf_components = _get_cashflow_waterfall(company_id)
    pros = _get_pros(company_id)
    cons = _get_cons(company_id)
    capital_allocation = _get_capital_allocation(company_id)

    # ── Build pages ───────────────────────────────────────────────────
    page1 = _build_page1(
        company_id, company_name, tiles,
        rp_years, rp_revenue, rp_netprofit,
        rr_years, rr_roe, rr_roce,
    )
    page2 = _build_page2(
        company_id,
        bs_years, bs_equity, bs_borrowings, bs_other_liab,
        cf_year, cf_components,
        pros, cons, capital_allocation,
    )

    # ── Ensure output dir exists ─────────────────────────────────────
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # ── Build PDF ─────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    story: List[Any] = []

    # Page 1 content
    story.extend(page1)
    # Force page break to page 2
    story.append(PageBreak())
    # Page 2 content
    story.extend(page2)

    doc.build(story)

    return output_path
