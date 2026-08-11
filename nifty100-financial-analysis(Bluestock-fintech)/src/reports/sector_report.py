"""
Day 34: Sector Report PDF Generator.

Generates a multi-page A4 PDF summarizing the financial health and
metrics of all companies within a single broad sector.

Eight sector-level metrics are computed for each sector:
  1. Average ROE (%)
  2. Average ROCE (%)
  3. Average Net Profit Margin (%)
  4. Average Debt-to-Equity
  5. Average Dividend Yield (%)
  6. Average FCF Conversion (%)
  7. Average CapEx Intensity (%)
  8. Average Revenue CAGR (%)

Metrics 1–5 are sourced directly from the database.  Metrics 6–8 are
derived by reusing the existing Day 31 / Day 32 analytics functions.

All financial data is sourced from the existing DB helpers and analytics
functions.  No values are ever fabricated.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
)

# ── DB helpers ──
from src.dashboard.utils.db import (
    get_bs,
    get_cashflow_data,
    get_company_list,
    get_financial_ratios,
    get_pl,
    get_sectors,
)

# ── Analytics ──
from src.analytics.cashflow_kpis import build_company_kpis
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow import cash_conversion_ratio

# ── Page dimensions ──
PAGE_WIDTH, PAGE_HEIGHT = A4

# ── Styles ──
_styles = getSampleStyleSheet()

_style_header = ParagraphStyle(
    "SectorHeader",
    parent=_styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#1a1a2e"),
    alignment=TA_CENTER,
    spaceAfter=6,
)

_style_subheader = ParagraphStyle(
    "SectorSubheader",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    textColor=colors.HexColor("#666666"),
    alignment=TA_CENTER,
    spaceAfter=12,
)

_style_section_title = ParagraphStyle(
    "SectorSectionTitle",
    parent=_styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=15,
    textColor=colors.HexColor("#1a1a2e"),
    alignment=TA_LEFT,
    spaceBefore=12,
    spaceAfter=4,
)

_style_table_header = ParagraphStyle(
    "SectorTableHeader",
    parent=_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#ffffff"),
    alignment=TA_CENTER,
)

_style_table_cell = ParagraphStyle(
    "SectorTableCell",
    parent=_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#333333"),
    alignment=TA_CENTER,
)

_style_note = ParagraphStyle(
    "SectorNote",
    parent=_styles["Normal"],
    fontName="Helvetica-Oblique",
    fontSize=7,
    leading=9,
    textColor=colors.HexColor("#999999"),
    alignment=TA_LEFT,
    spaceBefore=6,
)


# ── Metric definitions ────────────────────────────────────────────────────

METRIC_NAMES = [
    "Avg ROE %",
    "Avg ROCE %",
    "Avg Net Profit Margin %",
    "Avg Debt-to-Equity",
    "Avg Dividend Yield %",
    "Avg FCF Conversion %",
    "Avg CapEx Intensity %",
    "Avg Revenue CAGR %",
]


# ── Data extraction ─────────────────────────────────────────────────────────

def _to_float(val: Any) -> Optional[float]:
    """Coerce *val* to a float, returning ``None`` on failure."""
    if val is None:
        return None
    try:
        f = float(val)
        if pd.isna(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _get_company_sector_map() -> Dict[str, str]:
    """Return a mapping of company_id → broad_sector."""
    sectors = get_sectors()
    return {s["company_id"]: s["broad_sector"] for s in sectors}


def _latest_year_from_df(df: pd.DataFrame) -> Optional[int]:
    """Return the latest fiscal year represented in *df*."""
    if df.empty or "year" not in df.columns:
        return None
    years = []
    for v in df["year"].tolist():
        if v is None:
            continue
        if isinstance(v, (int, float)):
            years.append(int(v))
        elif isinstance(v, str):
            # Extract year from fiscal-year strings like "2024-03-01"
            try:
                years.append(int(v[:4]))
            except (ValueError, IndexError):
                continue
    return max(years) if years else None


def _safe_year(value: Any) -> Optional[int]:
    """Extract an integer year from various stored formats."""
    if value is None:
        return None
    if isinstance(value, float) and (pd.isna(value) if pd is not None else False):
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    if isinstance(value, str):
        try:
            return int(value[:4])
        except (ValueError, IndexError):
            return None
    return None


def _get_company_metrics(company_id: str) -> List[Optional[float]]:
    """
    Compute the 8 metric values for a single company.

    Returns a list of 8 floats (or ``None`` when data is unavailable),
    in the same order as ``METRIC_NAMES``.
    """
    values: List[Optional[float]] = []

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

    latest_year = _latest_year_from_df(fr_df)
    if latest_year is None:
        latest_year = _latest_year_from_df(pl_df)
    if latest_year is None:
        latest_year = _latest_year_from_df(cf_df)

    # ── Metric 1: ROE ──
    if not fr_df.empty and latest_year is not None:
        mask = fr_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)
        rows = fr_df[mask]
        if not rows.empty:
            roe = _to_float(rows.iloc[0].get("return_on_equity_pct"))
            values.append(roe)
        else:
            values.append(None)
    else:
        values.append(None)

    # ── Metric 2: ROCE (from financial_ratios table, stored as return_on_capital_employed_pct) ──
    if not fr_df.empty and latest_year is not None:
        mask = fr_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)
        rows = fr_df[mask]
        if not rows.empty:
            roce_col = "return_on_capital_employed_pct" if "return_on_capital_employed_pct" in rows.columns else "roce_percentage"
            roce = _to_float(rows.iloc[0].get(roce_col))
            values.append(roce)
        else:
            values.append(None)
    else:
        values.append(None)

    # ── Metric 3: Net Profit Margin ──
    if not fr_df.empty and latest_year is not None:
        mask = fr_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)
        rows = fr_df[mask]
        if not rows.empty:
            npm = _to_float(rows.iloc[0].get("net_profit_margin_pct"))
            values.append(npm)
        else:
            values.append(None)
    else:
        values.append(None)

    # ── Metric 4: Debt-to-Equity ──
    if not fr_df.empty and latest_year is not None:
        mask = fr_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)
        rows = fr_df[mask]
        if not rows.empty:
            dte = _to_float(rows.iloc[0].get("debt_to_equity"))
            values.append(dte)
        else:
            values.append(None)
    else:
        values.append(None)

    # ── Metric 5: Dividend Yield ──
    # Sourced from market_cap table via get_valuation helper
    try:
        from src.dashboard.utils.db import get_valuation
        val_df = get_valuation(company_id)
        if not val_df.empty and "dividend_yield_pct" in val_df.columns:
            val_latest = _latest_year_from_df(val_df)
            if val_latest is not None:
                mask = val_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == val_latest)
                rows = val_df[mask]
                if not rows.empty:
                    dy = _to_float(rows.iloc[0].get("dividend_yield_pct"))
                    values.append(dy)
                else:
                    values.append(_to_float(val_df.iloc[0].get("dividend_yield_pct")))
            else:
                values.append(_to_float(val_df.iloc[0].get("dividend_yield_pct")))
        else:
            values.append(None)
    except Exception:
        values.append(None)

    # ── Metric 6: FCF Conversion (CFO / PAT) ──
    fcf_conv = None
    if latest_year is not None:
        try:
            cf_row = cf_df[cf_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)]
            pl_row = pl_df[pl_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)]
            if not cf_row.empty and not pl_row.empty:
                cfo = _to_float(cf_row.iloc[0].get("operating_activity"))
                pat = _to_float(pl_row.iloc[0].get("net_profit"))
                fcf_conv = cash_conversion_ratio(cfo, pat)
        except Exception:
            fcf_conv = None
    values.append(fcf_conv * 100 if fcf_conv is not None else None)

    # ── Metric 7: CapEx Intensity ──
    capex_intensity = None
    if latest_year is not None:
        try:
            if not cf_df.empty and not pl_df.empty:
                cf_row = cf_df[cf_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)]
                pl_row = pl_df[pl_df["year"].apply(lambda y: _safe_year(y) is not None and _safe_year(y) == latest_year)]
                if not cf_row.empty and not pl_row.empty:
                    capex = _to_float(cf_row.iloc[0].get("investing_activity"))
                    sales = _to_float(pl_row.iloc[0].get("sales"))
                    if capex is not None and sales is not None and sales > 0:
                        capex_intensity = abs(capex) / sales * 100
        except Exception:
            capex_intensity = None
    values.append(capex_intensity)

    # ── Metric 8: Revenue CAGR ──
    rev_cagr = None
    try:
        if not pl_df.empty:
            pl_sorted = pl_df.sort_values("year", ascending=True)
            sales = [_to_float(v) for v in pl_sorted["sales"].tolist()]
            years = [_safe_year(v) for v in pl_sorted["year"].tolist()]
            pairs = [
                (y, s) for y, s in zip(years, sales)
                if y is not None and s is not None and s > 0
            ]
            if len(pairs) >= 2:
                start_year, start_val = pairs[0]
                end_year, end_val = pairs[-1]
                n_years = end_year - start_year
                if n_years > 0:
                    rev_cagr = calculate_cagr(start_val, end_val, n_years)
    except Exception:
        rev_cagr = None
    values.append(rev_cagr * 100 if rev_cagr is not None else None)

    return values


def _compute_sector_aggregates(sector: str) -> Dict[str, Any]:
    """
    Compute sector-level aggregates for all 8 metrics.

    Returns a dict with:
      - ``sector``: sector name
      - ``company_count``: number of companies in sector
      - ``companies``: list of company_ids
      - ``metrics``: list of 8 dicts: {name, avg, values, unit}
    """
    sector_map = _get_company_sector_map()
    companies_in_sector = [
        cid for cid, sec in sector_map.items() if sec == sector
    ]

    all_values: List[List[Optional[float]]] = []
    for cid in companies_in_sector:
        try:
            vals = _get_company_metrics(cid)
            all_values.append(vals)
        except Exception:
            all_values.append([None] * 8)

    metrics: List[Dict[str, Any]] = []
    for i, name in enumerate(METRIC_NAMES):
        col = [row[i] for row in all_values]
        valid = [v for v in col if v is not None]
        avg = sum(valid) / len(valid) if valid else None
        metrics.append({
            "name": name,
            "avg": avg,
            "values": col,
            "valid_count": len(valid),
        })

    return {
        "sector": sector,
        "company_count": len(companies_in_sector),
        "companies": companies_in_sector,
        "metrics": metrics,
    }


def _format_metric_value(val: Optional[float], metric_name: str) -> str:
    """Format a metric value for table display."""
    if val is None:
        return "N/A"
    if "CAGR" in metric_name or "Yield" in metric_name or "ROE" in metric_name or "ROCE" in metric_name or "Margin" in metric_name:
        return f"{val:.1f}%"
    if "CapEx" in metric_name:
        return f"{val:.1f}%"
    return f"{val:.2f}"


def _percentile_50(values: List[Optional[float]]) -> Optional[float]:
    """Return the median of non-None values."""
    valid = sorted(v for v in values if v is not None)
    if not valid:
        return None
    n = len(valid)
    mid = n // 2
    if n % 2 == 0:
        return (valid[mid - 1] + valid[mid]) / 2
    return valid[mid]


# ── PDF building ──

def _build_company_table(
    companies: List[str],
    metrics: List[Dict[str, Any]],
    sector: str,
) -> Table:
    """Build the per-company detail table."""
    headers = ["Company"] + METRIC_NAMES
    rows: List[List[Any]] = [headers]

    # Transpose metrics so values[i] is the list for company i
    for i, cid in enumerate(companies):
        row = [cid]
        for m in metrics:
            val = m["values"][i] if i < len(m["values"]) else None
            row.append(_format_metric_value(val, m["name"]))
        rows.append(row)

    # Add median row
    median_row = ["Sector Median"]
    for m in metrics:
        med = _percentile_50(m["values"])
        median_row.append(_format_metric_value(med, m["name"]))
    rows.append(median_row)

    col_widths = [25 * mm] + [18 * mm] * 8
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUNDCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),  # center
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -2), 7),
        ("BACKGROUNDCOLOR", (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDCOLOR", (0, 1), (-1, -2), colors.HexColor("#fafafa")),
    ]))
    return table


def _build_sector_report(
    sector: str,
    aggregate: Dict[str, Any],
) -> List[Any]:
    """Build the story (list of flowables) for a single sector report."""
    story: List[Any] = []

    # ── Title ──
    story.append(Paragraph(f"{sector} Sector Report", _style_header))
    story.append(Paragraph(
        f"{aggregate['company_count']} companies · 8 financial metrics",
        _style_subheader,
    ))

    # ── Summary table (8 metrics with averages) ──
    story.append(Paragraph("Sector Averages", _style_section_title))

    summary_rows = [("Metric", "Average", "Companies with Data")]
    for m in aggregate["metrics"]:
        avg_str = f"{m['avg']:.2f}" if m["avg"] is not None else "N/A"
        summary_rows.append((m["name"], avg_str, f"{m['valid_count']}/{aggregate['company_count']}"))

    summary_table = Table(
        summary_rows,
        colWidths=[55 * mm, 30 * mm, 35 * mm],
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUNDCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),  # center
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BACKGROUNDCOLOR", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ("ROWBACKGROUNDCOLOR", (0, 1), (-2, -1), colors.HexColor("#e8f5e9")),
        ("FONTNAME", (-1, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(summary_table)

    story.append(Spacer(1, 4 * mm))

    # ── Company-level detail table ──
    story.append(Paragraph("Company-Level Metrics", _style_section_title))
    company_table = _build_company_table(
        aggregate["companies"], aggregate["metrics"], sector
    )
    story.append(company_table)

    # ── Notes ──
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "Notes: ROE and ROCE from financial ratios; Net Profit Margin and "
        "Debt-to-Equity from financial_ratios table; Dividend Yield from "
        "market_cap table; FCF Conversion = CFO / PAT; CapEx Intensity = "
        "|investing activity| / sales; Revenue CAGR = CAGR of sales over "
        "available years. Median row shows sector median (50th percentile).",
        _style_note,
    ))

    return story


def generate_sector_report(
    sector: str,
    output_path: str,
) -> str:
    """
    Generate a multi-page A4 PDF sector report for *sector*.

    Args:
        sector: The broad sector name (e.g. ``"Financials"``).
        output_path: Path where the PDF will be written.

    Returns:
        The output path on success.

    Raises:
        ValueError: If *sector* is not a valid sector.
        FileNotFoundError: If the output directory does not exist.
    """
    # Validate sector exists
    sectors = get_sectors()
    valid_sectors = {s["broad_sector"] for s in sectors}
    if sector not in valid_sectors:
        raise ValueError(
            f"Invalid sector '{sector}'. "
            f"Must be one of: {sorted(valid_sectors)}"
        )

    # Compute aggregate data
    aggregate = _compute_sector_aggregates(sector)

    # ── Ensure output dir exists ──
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # ── Build PDF ──
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = _build_sector_report(sector, aggregate)
    doc.build(story)

    return output_path


def generate_all_sector_reports(
    output_dir: str,
) -> Dict[str, str]:
    """
    Generate sector reports for all sectors.

    Args:
        output_dir: Directory where PDF files will be written.

    Returns:
        Dict mapping sector name → output path.
    """
    os.makedirs(output_dir, exist_ok=True)
    sectors = get_sectors()
    sector_names = sorted({s["broad_sector"] for s in sectors if s["broad_sector"]})

    results: Dict[str, str] = {}
    for sector in sector_names:
        safe_name = sector.replace(" ", "_").replace("/", "_")
        path = os.path.join(output_dir, f"sector_{safe_name}.pdf")
        generate_sector_report(sector, path)
        results[sector] = path

    return results
