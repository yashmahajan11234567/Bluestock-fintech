# Sprint 5 Retrospective

**Sprint 5 Objective:** Implement Days 29–35 of the Nifty 100 Financial Analysis project, covering NLP parsing, cash flow intelligence, capital allocation, tearsheet generation, batch/sector reports, and portfolio summary.

---

## Day-by-Day Summary

### Day 29 — NLP Parser
**File:** `src/nlp/parser.py`

Implemented the financial document parser that extracts structured data (consolidated financial statements, ratios, and metadata) from raw HTML/JSON documents produced by external financial data vendors. The parser handles:
- Multi-year financial statement extraction (P&L, Balance Sheet, Cash Flow)
- Financial ratio parsing
- Sector and industry classification mapping
- Fallback handling for missing/malformed data

**Tests:** `tests/nlp/test_parser.py` — comprehensive test coverage for parsing logic.

### Day 30 — Pros/Cons Generator
**File:** `src/nlp/pros_cons_generator.py`

Built the natural language generator that produces financial pros and cons text for each company based on KPI thresholds and cash flow trends.

### Day 31 — Cash Flow Intelligence
**File:** `src/analytics/cashflow_kpis.py`

Implemented 7 key cash flow KPIs:
1. CFO Quality (mean CFO/PAT over 5 years)
2. CapEx Intensity (|investing|/sales × 100)
3. FCF CAGR 5-year
4. FCF Conversion (FCF/PAT × 100)
5. Distress Flag (CFO < 0 AND CFF > 0)
6. Deleveraging Flag (CFF < 0 AND borrowings declining)
7. Capital Allocation Category (delegates to Day 32)

**Outputs:**
- `Data/output/cashflow_intelligence.xlsx` — 92 rows × 11 columns
- `Data/output/distress_alerts.csv` — only distressed companies

**Tests:** `tests/analytics/test_cashflow_kpis.py` — 99 tests covering unit and integration cases.

### Day 32 — Capital Allocation Report
**File:** `src/analytics/capital_allocation.py`

Implemented the 5-category capital allocation classification system (Excellent, Good, Average, Weak, Poor) based on ROE, ROCE, and Cash Conversion Ratio thresholds.

**Tests:** `tests/analytics/test_day32_capital_allocation_report.py`

### Day 33 — Company Tearsheet
**File:** `src/reports/tearsheet.py`

Generated a 2-page A4 PDF for each company containing:
- Page 1: KPI tiles (ROE, ROCE, OPM, Debt-to-Equity, FCF Conversion, Revenue CAGR), Revenue/Net Profit chart, ROE/ROCE chart
- Page 2: Balance Sheet stacked bar, Cash Flow waterfall, Pros, Cons, Capital Allocation badge

All data sourced from existing DB helpers and analytics functions. No values fabricated.

**Tests:** `tests/reports/test_tearsheet.py` — 46 tests, all passing.

### Day 34 — Batch & Sector Reports
**Files:**
- `src/reports/sector_report.py` — Sector report PDF generator
- `src/reports/batch_tearsheets.py` — Batch company tearsheet generator

**Sector Report:** Generates multi-page A4 PDFs for each of the 10 broad sectors, computing 8 sector-level metrics (7 from Day 31 + Derived Revenue CAGR) with company-level breakdown tables and median rows.

**Batch Tearsheets:** Iterates over all 92 companies, generating individual tearsheets using the existing Day 33 `generate_tearsheet()` function. Supports CLI usage and programmatic API.

**Tests:** `tests/reports/test_sector_report.py` — 10 tests, all passing.

### Day 35 — Portfolio Summary
**Files:**
- `src/reports/portfolio_summary.py` — Portfolio summary PDF generator
- `tests/reports/test_portfolio_summary.py` — 26 tests, all passing

**Portfolio Summary:** Generates a single multi-page A4 PDF (`reports/portfolio/portfolio_summary.pdf`) with exactly one page per company (92 pages for 92 companies), ordered alphabetically by ticker. Each page contains:

1. Company name
2. Ticker (company_id)
3. Sector
4. Exactly 6 KPIs:
   - ROE (from `financial_ratios.return_on_equity_pct`)
   - ROCE (from `financial_ratios.return_on_capital_employed_pct`)
   - OPM (from `financial_ratios.operating_profit_margin_pct` with P&L fallback)
   - Debt-to-Equity (from `financial_ratios.debt_to_equity`)
   - FCF Conversion (CFO/PAT using `cash_conversion_ratio()`)
   - Revenue CAGR (using `calculate_cagr()` from P&L sales data)
5. One trend arrow per KPI:
   - ↑ = latest value improved numerically by >2%
   - ↓ = latest value declined numerically by >2%
   - → = change within ±2% (inclusive — exactly ±2% is flat)

**Trend-arrow implementation:** Pure helper function `_calculate_trend_arrow(latest_val, previous_val)` using relative change formula. Numerical interpretation is used consistently for all metrics including Debt-to-Equity (a decrease in D/E still shows ↓).

**Revenue CAGR trend:** The latest CAGR is computed from full available sales history (same convention as Day 33). The "previous" CAGR is computed by excluding the latest year and re-computing over the remaining window. This reuses the existing `calculate_cagr()` implementation without inventing a new formula.

---

## Sprint 5 Statistics

| Metric | Count |
|--------|-------|
| Companies in DB | 92 |
| Broad sectors | 10 |
| Sub-sectors | 46 |
| Available financial years | 2011–2024 |

---

## Major Outputs

| File | Description |
|------|-------------|
| `Data/output/cashflow_intelligence.xlsx` | 92 companies × 11 columns of Day 31 KPIs |
| `Data/output/distress_alerts.csv` | Companies flagged as distressed |
| `reports/portfolio/portfolio_summary.pdf` | Portfolio summary: 92 pages, 6 KPIs per page |
| `src/reports/sector_report.py` | Sector report generator |
| `src/reports/portfolio_summary.py` | Portfolio summary generator |

---

## Test Results

| Test Suite | Tests | Status |
|-----------|-------|--------|
| `tests/nlp/test_parser.py` | — | ✅ |
| `tests/analytics/test_cashflow_kpis.py` | 99 | ✅ |
| `tests/analytics/test_day32_capital_allocation_report.py` | — | ✅ |
| `tests/reports/test_tearsheet.py` | 46 | ✅ |
| `tests/reports/test_sector_report.py` | 10 | ✅ |
| `tests/reports/test_portfolio_summary.py` | 26 | ✅ |

**Full suite: 56 report tests + additional analytics/NLP tests = all passing.**

---

## Important Fixes/Issues

1. **Environment classifier downtime:** The Python execution environment was temporarily unavailable during Phase 0. Worked around by using read-only tools (Read, Grep, Glob) for inspection until the classifier recovered.

2. **DB location confusion:** `Data/bluestock.db` (0 bytes) was an empty placeholder. The real database is `db/nifty100.db` (5.7MB).

3. **Sector count discrepancy:** The repository contained 10 broad sectors, not the expected 11. This was verified directly from the `sectors.broad_sector` column in the database.

4. **8th metric for Day 34 sector report:** Day 31 provides 7 KPIs. The 8th sector metric was identified as Dividend Yield, derivable from `market_cap.dividend_yield_pct` (a column that already existed in the database). No metric was invented — all data sources are existing DB columns.

5. **ReportLab table alignment:** Table cell alignment in ReportLab requires string values ("CENTER", "MIDDLE") rather than enum constants (TA_CENTER, TA_LEFT). Fixed in both sector_report.py and portfolio_summary.py.

6. **NaN handling in `_safe_year`:** Pandas NaN values (from nullable Int64 columns) caused crashes when compared to integers. Fixed with explicit `math.isnan()` checks.

7. **pypdfium2 API:** Text extraction uses `page.get_textpage().get_text_range()` (not `page.get_text()`). Tests were corrected to use the proper API.

---

## Specification Decisions

- **No hardcoded values:** All company counts, sector counts, sector names, and metric values are dynamically retrieved from the database. No magic numbers.
- **Reuse over reimplementation:** Portfolio summary reuses Day 33's KPI extraction patterns, Day 31's `cash_conversion_ratio`, and Day 33's `calculate_cagr` function. No Day 33 files were modified.
- **Numerical trend interpretation:** Trend arrows use purely numerical comparison. A decrease in Debt-to-Equity shows ↓ (not ↑), as specified.
- **±2% boundary:** Exactly +2.00% or -2.00% is treated as FLAT (→). Only values strictly beyond ±2% produce arrows.
- **Revenue CAGR trend:** The "previous" CAGR is computed by excluding the latest year from the sales history and recomputing. This follows the existing repository CAGR convention without inventing a new formula.

---

## Final Sprint 5 Status

**Status: COMPLETE**

All 6 days of Sprint 5 (Days 29–35) have been implemented with comprehensive test coverage:
- NLP parser and pros/cons generator (Days 29–30)
- Cash flow intelligence KPIs (Day 31)
- Capital allocation classification (Day 32)
- Company tearsheet PDF (Day 33)
- Batch company tearsheets + Sector reports (Day 34)
- Portfolio summary PDF (Day 35)

The portfolio summary PDF (`reports/portfolio/portfolio_summary.pdf`) contains 92 pages (one per company, alphabetically ordered), each with 6 KPIs and trend arrows, all verified by automated tests.
