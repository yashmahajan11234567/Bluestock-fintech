"""
Analyst Guide PDF Generator for Bluestock Fintech.

Creates a comprehensive analyst guide covering dashboard usage, screener
features, PDF tearsheets, API usage, and troubleshooting.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    PageTemplate,
    BaseDocTemplate,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

PAGE_WIDTH, PAGE_HEIGHT = A4


def _make_style(name, **kw):
    """Create a paragraph style with base settings."""
    base_kw = dict(fontSize=10, leading=14, textColor=colors.HexColor("#333333"), alignment=TA_LEFT)
    base_kw.update(kw)
    return ParagraphStyle(name, **base_kw)


_STYLE_H1 = _make_style("AnalystH1", fontName="Helvetica-Bold", fontSize=18, leading=21,
                        textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER, spaceAfter=12)
_STYLE_H2 = _make_style("AnalystH2", fontName="Helvetica-Bold", fontSize=14, leading=17,
                        textColor=colors.HexColor("#1a1a2e"), spaceAfter=8, spaceBefore=16)
_STYLE_H3 = _make_style("AnalystH3", fontName="Helvetica-Bold", fontSize=12, leading=15,
                        textColor=colors.HexColor("#333333"), spaceAfter=4, spaceBefore=10)
_STYLE_BODY = _make_style("AnalystBody", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=6)
_STYLE_BULLET = _make_style("AnalystBullet", fontName="Helvetica", fontSize=10, leading=14,
                            leftIndent=12, bulletIndent=6, spaceAfter=3)
_STYLE_CODE = _make_style("AnalystCode", fontName="Courier", fontSize=9, leading=12,
                          textColor=colors.HexColor("#dc2626"), leftIndent=12,
                          backColor=colors.HexColor("#f3f4f6"), borderPadding=4, spaceAfter=6)
_STYLE_FOOTER = _make_style("AnalystFooter", fontName="Helvetica", fontSize=8,
                            textColor=colors.HexColor("#6b7280"), alignment=TA_CENTER, spaceBefore=10)


def add_page_number(canvas, story):
    """Add page number to footer."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawCentredString(PAGE_WIDTH / 2, 15 * mm, "Page %d" % canvas.getPageNumber())
    canvas.restoreState()


def build_analyst_guide(output_path: str) -> str:
    """Generate the analyst guide PDF with page numbers."""
    from reportlab.platypus import Frame
    from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate

    frame = Frame(20 * mm, 20 * mm, PAGE_WIDTH - 40 * mm, PAGE_HEIGHT - 45 * mm, id="normal")
    template = PageTemplate(id="normal", frames=frame, onPage=add_page_number)
    doc = BaseDocTemplate(
        output_path,
        pageTemplates=[template],
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    doc.build(_build_story())
    return output_path


def _build_story():
    """Build the story elements for the analyst guide."""
    story = []

    # ---- PAGE 1: Title / Overview ----
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph("Bluestock Fintech", _STYLE_H1))
    story.append(Paragraph("Analyst Guide — Nifty100 Financial Analysis", _STYLE_H2))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Version 1.0 &nbsp;|&nbsp; August 2026", _STYLE_BODY))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("Purpose", _STYLE_H3))
    story.append(Paragraph(
        "This guide explains how to use the Bluestock Fintech Nifty100 Financial "
        "Analysis platform. It covers the Streamlit dashboard, the Stock Screener, "
        "peer comparison, sector analysis, PDF tearsheet generation, the FastAPI "
        "REST API, and common troubleshooting steps.",
        _STYLE_BODY,
    ))
    story.append(Paragraph(
        "The platform provides financial analytics for 92 Nifty 100 companies, "
        "backed by a SQLite database containing profit-and-loss statements, "
        "balance sheets, cash flow data, financial ratios, market capitalisation, "
        "and peer-group mappings.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Contents", _STYLE_H3))
    contents = [
        "1. Getting Started &mdash; Environment, installation, and startup",
        "2. Dashboard Overview &mdash; Navigation and the eight screens",
        "3. Home Dashboard &mdash; KPIs, sector view, top companies",
        "4. Company Profile &mdash; Selection, tabs, financial information",
        "5. Stock Screener &mdash; Presets, filters, sorting, pagination, CSV export",
        "6. Peer Comparison &mdash; Relative metrics and interpretation",
        "7. Financial Trends &mdash; Historical performance charts",
        "8. Sector Analysis &mdash; Sector-level aggregates",
        "9. Capital Allocation &mdash; Investment strategy insights",
        "10. Reports &mdash; PDF tearsheets and report generation",
        "11. API Guide &mdash; curl examples for REST endpoints",
        "12. Troubleshooting &mdash; Common issues and solutions",
        "13. Operational Reference &mdash; ETL, testing, and command reference",
    ]
    for line in contents:
        story.append(Paragraph(line, _STYLE_BULLET))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("Page 1 of 12", _STYLE_FOOTER))

    # ---- PAGE 2: Getting Started ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Getting Started", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Environment", _STYLE_H3))
    story.append(Paragraph(
        "The platform runs on Python 3.12 with the following key dependencies:",
        _STYLE_BODY,
    ))
    deps = [
        "Streamlit 1.58.0 (web dashboard)",
        "FastAPI 0.116.1 (REST API)",
        "pandas 2.3.3 (data manipulation)",
        "numpy 1.26.4 (numerical computing)",
        "scikit-learn 1.3.0 (clustering)",
        "Plotly 5.18.0 (charting)",
        "ReportLab 5.0.0 (PDF generation)",
        "SQLite3 (database, built into Python)",
    ]
    for dep in deps:
        story.append(Paragraph(f"&#8226; {dep}", _STYLE_BULLET))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Installation", _STYLE_H3))
    story.append(Paragraph("Create and activate a virtual environment:", _STYLE_BODY))
    story.append(Paragraph(
        'python -m venv .venv<br/>'
        'source .venv/bin/activate  <i>(Linux/macOS)</i><br/>'
        '.venv\\Scripts\\activate  <i>(Windows)</i>',
        _STYLE_CODE,
    ))
    story.append(Paragraph("Install dependencies:", _STYLE_BODY))
    story.append(Paragraph("pip install -r requirements.txt", _STYLE_CODE))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Startup", _STYLE_H3))
    story.append(Paragraph("To start the Streamlit dashboard:", _STYLE_BODY))
    story.append(Paragraph("streamlit run src/dashboard/app.py", _STYLE_CODE))
    story.append(Paragraph("To start the FastAPI backend:", _STYLE_BODY))
    story.append(Paragraph("uvicorn src.api.main:app --reload", _STYLE_CODE))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("The dashboard opens at http://localhost:8501 and the API at http://localhost:8000.", _STYLE_BODY))
    story.append(Paragraph("API documentation is available at http://localhost:8000/docs.", _STYLE_BODY))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 2 of 12", _STYLE_FOOTER))

    # ---- PAGE 3: Dashboard Overview ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Dashboard Overview", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The Streamlit dashboard provides eight navigation screens accessible via "
        "the sidebar menu. Each screen serves a distinct analytical purpose.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    screens = [
        ("Home", "KPI overview with sector distribution and top companies"),
        ("Company Profile", "Detailed financial analysis for a selected company"),
        ("Screener", "Filter and rank companies by financial criteria"),
        ("Peer Comparison", "Compare a company against its peer group"),
        ("Financial Trends", "Historical financial performance charts (5&ndash;10 years)"),
        ("Sector Analysis", "Sector-level aggregation and comparison"),
        ("Capital Allocation", "Investment classification and strategy"),
        ("Reports", "Report generation and tearsheet management"),
    ]
    screen_data = [["Screen", "Description"]]
    for name, desc in screens:
        screen_data.append([name, desc])
    screen_table = Table(screen_data, colWidths=[50 * mm, 100 * mm])
    screen_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(screen_table)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "Navigation: Use the sidebar on the left to switch between screens. "
        "Some screens require selecting a company or year before data loads.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 3 of 12", _STYLE_FOOTER))

    # ---- PAGE 4: Home Dashboard ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Home Dashboard", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The Home screen provides a high-level overview of the Nifty 100 market. "
        "It displays six KPI cards, a sector distribution donut chart, and a "
        "top-5 companies table.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("KPI Cards", _STYLE_H3))
    kpikpis = [
        "Average ROE &mdash; mean return on equity across all companies",
        "Median P/E &mdash; price-to-earnings ratio median",
        "Median Debt/Equity &mdash; median leverage ratio",
        "Total Companies &mdash; count of companies in the dataset",
        "Median Revenue CAGR (5yr) &mdash; median 5-year revenue growth",
        "Debt-Free Companies &mdash; count of companies with zero or null debt",
    ]
    for kpi in kpikpis:
        story.append(Paragraph(f"&#8226; {kpi}", _STYLE_BULLET))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Sector Distribution", _STYLE_H3))
    story.append(Paragraph(
        "A donut chart visualises the distribution of companies across broad "
        "sectors. Hover over segments for sector names and percentages.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Top 5 Companies", _STYLE_H3))
    story.append(Paragraph(
        "A table ranks the top 5 companies by a composite quality score that "
        "weights profitability (35%), cash quality (30%), growth (20%), and "
        "leverage (15%).",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Year Selector", _STYLE_H3))
    story.append(Paragraph(
        "Use the year dropdown in the sidebar to view KPIs for a specific fiscal year.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 4 of 12", _STYLE_FOOTER))

    # ---- PAGE 5: Company Profile ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Company Profile", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The Company Profile screen provides detailed financial analysis for a "
        "single selected company. Begin by selecting a company from the dropdown, "
        "then click 'Load Profile'.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Company Selection", _STYLE_H3))
    story.append(Paragraph(
        "Use the 'Select Company' dropdown to choose from the 92 available companies. "
        "Company tickers are unique IDs (e.g., 'TCS', 'RELIANCE').",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Profile Header", _STYLE_H3))
    story.append(Paragraph(
        "The header displays the company name, ticker, sector, industry, and market capitalisation.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Tabs", _STYLE_H3))
    tabs = [
        ("Financial Ratios", "Annual financial ratios including ROE, ROCE, debt-to-equity, interest coverage, and more"),
        ("Cash Flow", "Annual cash flow data: operating, investing, and financing activities"),
        ("Capital Allocation", "Capital allocation metrics: ROE, debt-to-equity, free cash flow, and cash conversion ratio"),
        ("Raw Financials", "Placeholder for full P&L and balance sheet data"),
    ]
    for name, desc in tabs:
        story.append(Paragraph(f"<b>{name}</b>: {desc}", _STYLE_BULLET))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Key Ratio Cards", _STYLE_H3))
    story.append(Paragraph(
        "The Financial Ratios tab displays four key metric cards for the latest year: "
        "ROE, ROCE, Debt/Equity, and Interest Coverage.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 5 of 12", _STYLE_FOOTER))

    # ---- PAGE 6: Stock Screener ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Stock Screener", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The Stock Screener allows you to filter and rank the 92 Nifty 100 companies "
        "by up to 12 financial criteria. Results are scored by a composite quality "
        "metric and can be sorted, paginated, and exported.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Preset Filters", _STYLE_H3))
    presets = [
        "Quality Compounder",
        "Value Pick",
        "Growth Accelerator",
        "Dividend Champion",
        "Debt Free Blue Chip",
        "Turnaround Watch",
    ]
    for preset in presets:
        story.append(Paragraph(f"&#8226; {preset}", _STYLE_BULLET))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Filter Criteria", _STYLE_H3))
    filters_list = [
        "ROE &mdash; Return on Equity %",
        "Debt to Equity &mdash; Leverage ratio",
        "Operating Profit Margin &mdash; OPM %",
        "Market Cap &mdash; Market capitalisation (crore INR)",
        "Free Cash Flow &mdash; FCF in crore INR",
        "Revenue CAGR &mdash; Compound sales growth",
        "PAT CAGR &mdash; Compound profit growth",
        "Dividend Yield &mdash; Annual dividend yield %",
        "PE Ratio &mdash; Price to earnings",
        "PB Ratio &mdash; Price to book",
        "Interest Coverage &mdash; Interest coverage ratio",
    ]
    for f in filters_list:
        story.append(Paragraph(f"&#8226; {f}", _STYLE_BULLET))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Sorting and Pagination", _STYLE_H3))
    story.append(Paragraph(
        "Results are sorted by the composite quality score by default. Use the sort dropdown "
        "to change the sort field and direction. The table supports pagination with "
        "configurable page size (default: 50 per page).",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("CSV Export", _STYLE_H3))
    story.append(Paragraph(
        "Click the 'Download CSV' button below the results table to export the current "
        "filtered and sorted results as a CSV file.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 6 of 12", _STYLE_FOOTER))

    # ---- PAGE 7: Peer Comparison ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Peer Comparison", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The Peer Comparison screen allows you to assess a company relative to its "
        "peer group. Percentile rankings show how the selected company ranks on key "
        "financial metrics within its peer cohort.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Usage", _STYLE_H3))
    story.append(Paragraph(
        "1. Select a company from the dropdown.<br/>"
        "2. Click 'Load Profile'.<br/>"
        "3. The screen displays percentile rankings for ROE, NPM, Debt/Equity, FCF, "
        "PE, and PB against the company's peer group.<br/>"
        "4. The overall peer score is the average of all available percentile rankings.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Interpretation", _STYLE_H3))
    story.append(Paragraph(
        "A percentile above 50 indicates the company outperforms its peers on that metric. "
        "For Debt/Equity, PE, and PB, lower values are better, so percentile scores are "
        "inverted accordingly.",
        _STYLE_BODY,
    ))

    # ---- PAGE 8: Financial Trends ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Financial Trends", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The Financial Trends screen displays multi-year historical charts for a selected "
        "company. Charts cover up to 10 years of revenue, net profit, ROE, and ROCE data.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Charts", _STYLE_H3))
    trends_charts = [
        ("Revenue &amp; Net Profit", "Grouped bar chart showing annual revenue and net profit over up to 10 years"),
        ("ROE &amp; ROCE Trend", "Dual-axis line chart showing annual ROE and ROCE trends"),
    ]
    for name, desc in trends_charts:
        story.append(Paragraph(f"<b>{name}</b><br/>{desc}", _STYLE_BULLET))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Use the company dropdown to select a company and view its historical performance. "
        "Missing years are excluded from the charts to maintain data integrity.",
        _STYLE_BODY,
    ))

    # ---- PAGE 8b: Sector Analysis ----
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Sector Analysis", _STYLE_H3))
    story.append(Paragraph(
        "The Sector Analysis screen aggregates financial metrics across all broad sectors. "
        "It displays company counts, average ROE, average ROCE, average net profit margin, "
        "average debt-to-equity, average PE ratio, and total sector market capitalisation.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Sector-level Aggregates", _STYLE_H3))
    story.append(Paragraph(
        "Sector aggregates are computed across the most recent market capitalisation year. "
        "Use the sector table to compare sector performance side by side.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 7 of 12", _STYLE_FOOTER))

    # ---- PAGE 9: Capital Allocation ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Capital Allocation", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The Capital Allocation screen provides insights into how companies allocate "
        "capital, including investment classifications and strategic recommendations.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Capital Allocation Categories", _STYLE_H3))
    categories = [
        ("Excellent", "Companies with superior capital allocation practices"),
        ("Good", "Companies with strong capital allocation"),
        ("Average", "Companies with acceptable capital allocation"),
        ("Weak", "Companies with suboptimal capital allocation"),
        ("Poor", "Companies with poor capital allocation"),
    ]
    for cat, desc in categories:
        story.append(Paragraph(f"<b>{cat}</b><br/>{desc}", _STYLE_BULLET))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Usage", _STYLE_H3))
    story.append(Paragraph(
        "Select a company and click 'Load Profile' to view its capital allocation "
        "classification. The badge colour indicates the quality of capital allocation.",
        _STYLE_BODY,
    ))

    # ---- PAGE 9b: Reports ----
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Reports", _STYLE_H3))
    story.append(Paragraph(
        "The Reports screen offers three tabs: Peer Comparison Report (Excel), "
        "Custom Report Builder, and Generated Reports listing.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Peer Comparison Excel Report", _STYLE_H3))
    story.append(Paragraph(
        "Click 'Generate Peer Comparison Report' to create an Excel file with one "
        "worksheet per peer group. Each sheet includes company name, peer group, "
        "overall peer score, and all percentile metrics with conditional formatting "
        "(green for top 20%, yellow for middle 60%, red for bottom 20%).",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Custom Report Builder", _STYLE_H3))
    story.append(Paragraph(
        "Select multiple companies and metrics to build a custom report. Currently "
        "in preview mode.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Generated Reports", _STYLE_H3))
    story.append(Paragraph(
        "Lists all previously generated reports in the Data/output directory.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 8 of 12", _STYLE_FOOTER))

    # ---- PAGE 10: PDF Tearsheets ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("PDF Tearsheets", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "A tearsheet is a two-page A4 PDF summary for a single company, generated "
        "using ReportLab. It includes KPI tiles, financial trend charts, balance sheet "
        "composition, cash flow waterfall, pros/cons, and a capital allocation badge.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("What Is in a Tearsheet?", _STYLE_H3))
    tearsheet_contents = [
        ("Page 1", "KPI tiles (ROE, ROCE, OPM, Debt/Equity, FCF Conversion, Revenue CAGR), Revenue &amp; Net Profit bar chart, ROE &amp; ROCE trend chart"),
        ("Page 2", "Balance sheet composition stacked bar, cash flow waterfall, pros and cons list, capital allocation badge"),
    ]
    for page, content in tearsheet_contents:
        story.append(Paragraph(f"<b>{page}</b><br/>{content}", _STYLE_BULLET))

    # ---- PAGE 10b: Tearsheet Generation ----
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Generation Method", _STYLE_H3))
    story.append(Paragraph(
        "Tearsheets are generated programmatically using the "
        "reportlab library. The generate_tearsheet function in "
        "src/reports/tearsheet.py creates a 2-page PDF.",
        _STYLE_BODY,
    ))
    story.append(Paragraph("Output Location", _STYLE_H3))
    story.append(Paragraph(
        "PDFs are saved to a specified output path. Example:",
        _STYLE_BODY,
    ))
    story.append(Paragraph(
        "from src.reports.tearsheet import generate_tearsheet<br/>"
        'generate_tearsheet("TCS", "output/tearsheets/tcs_tearsheet.pdf")',
        _STYLE_CODE,
    ))
    story.append(Paragraph("Required Parameters", _STYLE_H3))
    story.append(Paragraph(
        "company_id: The company ticker (e.g., 'TCS'). must exist in the database.<br/>"
        "output_path: File path where the PDF will be written.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 9 of 12", _STYLE_FOOTER))

    # ---- PAGE 11: API Guide ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("API Guide", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "The FastAPI backend exposes REST endpoints at http://localhost:8000/api/v1/. "
        "Below are curl examples for each major endpoint.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    api_endpoints = [
        ("Health Check", "GET /api/v1/health",
         "curl -s http://localhost:8000/api/v1/health | jq ."),
        ("List Companies", "GET /api/v1/companies",
         "curl -s http://localhost:8000/api/v1/companies | jq ."),
        ("Company Profile", "GET /api/v1/companies/{company_id}",
         "curl -s http://localhost:8000/api/v1/companies/TCS | jq ."),
        ("Financials", "GET /api/v1/companies/{company_id}/financials",
         "curl -s http://localhost:8000/api/v1/companies/TCS/financials | jq ."),
        ("Ratios", "GET /api/v1/companies/{company_id}/ratios",
         "curl -s http://localhost:8000/api/v1/companies/TCS/ratios | jq ."),
        ("Cashflow", "GET /api/v1/companies/{company_id}/cashflow",
         "curl -s http://localhost:8000/api/v1/companies/TCS/cashflow | jq ."),
        ("Peers", "GET /api/v1/companies/{company_id}/peers",
         "curl -s http://localhost:8000/api/v1/companies/TCS/peers | jq ."),
        ("Pros &amp; Cons", "GET /api/v1/companies/{company_id}/pros-cons",
         "curl -s http://localhost:8000/api/v1/companies/TCS/pros-cons | jq ."),
        ("Documents", "GET /api/v1/companies/{company_id}/documents",
         "curl -s http://localhost:8000/api/v1/companies/TCS/documents | jq ."),
        ("Screener", "GET /api/v1/screener?min_roe=15&sort=return_on_equity_pct&sort_dir=desc&page=1&page_size=20",
         "curl -s 'http://localhost:8000/api/v1/screener?min_roe=15&sort=return_on_equity_pct&sort_dir=desc' | jq ."),
        ("Sector Aggregates", "GET /api/v1/sectors",
         "curl -s http://localhost:8000/api/v1/sectors | jq ."),
    ]
    for name, path, curl_cmd in api_endpoints:
        story.append(Paragraph(f"<b>{name}</b>", _STYLE_BULLET))
        story.append(Paragraph(f"Endpoint: {path}", _STYLE_BODY))
        story.append(Paragraph(curl_cmd, _STYLE_CODE))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 10 of 12", _STYLE_FOOTER))

    # ---- PAGE 12: Troubleshooting ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Troubleshooting", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "This section covers common issues and their solutions.",
        _STYLE_BODY,
    ))
    story.append(Spacer(1, 6 * mm))
    issues = [
        ("Dashboard not loading",
         "Ensure the virtual environment is activated and all dependencies are installed. "
         "Run 'pip install -r requirements.txt' to install or update dependencies."),
        ("Database not found",
         "The database file db/nifty100.db must exist. Run the ETL pipeline to create it: "
         "'python src/etl/loader.py'."),
        ("Company list empty",
         "The database may not have data loaded yet. Run the ETL pipeline and verify "
         "the companies table has records."),
        ("Port conflicts",
         "If localhost:8501 or localhost:8000 is in use, pass a different port: "
         "'streamlit run src/dashboard/app.py --server.port 8502' or "
         "'uvicorn src.api.main:app --port 8001'."),
        ("PDF tearsheet generation failed",
         "Ensure the company_id exists in the database. Check the output directory "
         "exists and is writable."),
        ("Streamlit charts not rendering",
         "Ensure Plotly and Streamlit are installed and up to date. Clear the Streamlit "
         "cache: 'rm -rf .streamlit/cache'.'"),
        ("API CORS errors",
         "The API allows all origins by default. If you see CORS errors behind a proxy, "
         "configure your reverse proxy to pass through headers."),
        ("Screener filters returning empty",
         "Filters use strict min/max bounds. Verify the filter values are within the "
         "range of the data. The screener uses the most recent year available."),
    ]
    for issue, solution in issues:
        story.append(Paragraph(f"<b>{issue}</b>", _STYLE_H3))
        story.append(Paragraph(solution, _STYLE_BULLET))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 11 of 12", _STYLE_FOOTER))

    # ---- PAGE 12b: Operational Reference ----
    story.append(PageBreak())
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Operational Reference", _STYLE_H1))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Testing", _STYLE_H3))
    story.append(Paragraph(
        "Run the test suite with pytest:",
        _STYLE_BODY,
    ))
    story.append(Paragraph(
        "pytest tests/api -v<br/>"
        "pytest tests/analytics -v<br/>"
        "pytest tests/ -v",
        _STYLE_CODE,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("ETL Pipeline", _STYLE_H3))
    story.append(Paragraph(
        "The ETL pipeline loads data from Excel files in data/raw/ into db/nifty100.db:",
        _STYLE_BODY,
    ))
    story.append(Paragraph("python src/etl/loader.py", _STYLE_CODE))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Code Quality", _STYLE_H3))
    story.append(Paragraph(
        "Format code with Black and lint with Ruff:",
        _STYLE_BODY,
    ))
    story.append(Paragraph(
        "black src/ tests/<br/>"
        "ruff check src/ tests/",
        _STYLE_CODE,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Database Schema", _STYLE_H3))
    story.append(Paragraph(
        "The database is defined in db/schema.sql and contains tables for companies, "
        "sectors, financial ratios, market cap, profit and loss, balance sheet, "
        "cashflow, peer groups, documents, and pros/cons.",
        _STYLE_BODY,
    ))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Useful Commands", _STYLE_H3))
    commands = [
        ("Start Dashboard", "streamlit run src/dashboard/app.py"),
        ("Start API", "uvicorn src.api.main:app --reload"),
        ("Run ETL", "python src/etl/loader.py"),
        ("Run Tests", "pytest tests/ -v"),
        ("Format Code", "black src/ tests/"),
        ("Lint Code", "ruff check src/ tests/"),
        ("API Docs", "http://localhost:8000/docs"),
        ("API Health", "curl http://localhost:8000/api/v1/health"),
    ]
    cmd_data = [["Command", "Description", "Syntax"]]
    for desc, cmd in commands:
        cmd_data.append([desc, cmd, ""])
    cmd_table = Table(cmd_data, colWidths=[35 * mm, 65 * mm, 40 * mm])
    cmd_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(cmd_table)
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Page 12 of 12", _STYLE_FOOTER))

    return story


if __name__ == "__main__":
    out = build_analyst_guide("docs/analyst_guide.pdf")
    print(f"Analyst guide generated at: {out}")
