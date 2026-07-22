# Sprint 2 — Implementation Roadmap
## Bluestock Financial Analytics — Nifty 100

**Author:** Technical Architect  
**Date:** 2026-07-22  
**Status:** Planning  

---

## Phase 1 — Repository Gap Analysis

### Findings

| Check | Status | Details |
|---|---|---|
| `src/analytics/` directory | **MISSING** | Must be created |
| `src/analytics/ratios.py` | **MISSING** | Must be created |
| `src/analytics/cagr.py` | **MISSING** | Must be created |
| `src/analytics/cashflow_kpis.py` | **MISSING** | Must be created |
| `financial_ratios` table | **EXISTS** | 15 columns, already populated with 1160 rows (FK-filtered from Excel) |
| `analysis` table | **EXISTS** | Contains CAGR data from Excel, but not programmatically generated |
| Existing tests | **EXISTS in `tests/`** | Covers normaliser, loader, validator only — no analytics tests |
| DB `nifty100.db` | **EXISTS** | Fully populated by Sprint 1 ETL pipeline |
| `analysis.xlsx` source | **EXISTS** | Pre-computed CAGR values from Excel source |
| Edge case data | **PRESENT** | Nulls exist in `interest_coverage` (93), `operating_profit_margin_pct` (61), `free_cash_flow_cr` (2), `capex_cr` (2), etc. |
| Company coverage gap | **KNOWN** | FK violations exist — 24 rows rejected from `financial_ratios`, up to 128 from `documents` |

### Edge Cases Identified in Source Data

1. **Year stored as timestamp string** (`"2012-12-01 00:00:00"`) — not pure year. CAGR engine must normalize.
2. **Duplicate (company_id, year) in financial_ratios** — some companies have multiple rows per year (e.g., ABB with two `2014-03-01` entries).
3. **Zero values** in `free_cash_flow_cr`, `capex_cr`, `cash_from_operations_cr` — division-by-zero risk.
4. **Nulls in critical ratio columns** — `interest_coverage` has 93 nulls, `operating_profit_margin_pct` has 61.
5. **Negative sales** — DQ-06 already flags these, ratio engine must handle.
6. **Missing company_id FK references** — `WIPRO`, `UNIONBANK`, `ZOMATO` appear in fact tables but not in `companies`.
7. **Year range:** ~2011–2024 across tables, but not all companies have data for all years.
8. **`other_income`, `interest`, `depreciation` in PL are zero for many rows** — impacts computed ratios.
9. **Dividend payout ratio varies 0–100%**, some null — must handle gracefully.
10. **Book value per share values are very small** (e.g., ABB @ 3.08) — precision matters.

---

## Phase 2 — `src/analytics/ratios.py`

**Objective:** Build a pure computation module that reads from `profitandloss`, `balancesheet`, and `cashflow` tables and computes financial ratios programmatically. This replaces dependence on the pre-computed `financial_ratios.xlsx`.

### Ratio Groups

#### A. Profitability Ratios (source: profitandloss table)
| Ratio | Formula | Edge Cases |
|---|---|---|
| Net Profit Margin | `net_profit / sales * 100` | sales=0 → None; negative net profit → valid negative margin |
| Operating Profit Margin | `operating_profit / sales * 100` | sales=0 → None; operating_profit=0 → 0% |
| Return on Equity (ROE) | `net_profit / (equity_capital + reserves)` | equity = 0 → None from balancesheet |
| Earnings Per Share (EPS) | Already in PL table; verify `net_profit / shares_outstanding` | shares=0, net_profit=0 |

#### B. Leverage Ratios (source: balancesheet + profitandloss)
| Ratio | Formula | Edge Cases |
|---|---|---|
| Debt to Equity | `borrowings / (equity_capital + reserves)` | equity=0 → None; zero debt → 0.0 |
| Interest Coverage | `operating_profit / interest` | interest=0 → None (div by zero); negative interest |

#### C. Efficiency Ratios (source: profitandloss + balancesheet)
| Ratio | Formula | Edge Cases |
|---|---|---|
| Asset Turnover | `sales / total_assets` | total_assets=0 → None |
| Operating Profit Margin | (same as profitability, cross-listed) | — |

### Output
- Dictionary of computed ratios per `(company_id, year)`
- All None/NaN handled explicitly — never raise uncaught exceptions

### Dependencies
- Requires: `profitandloss`, `balancesheet`, `cashflow` tables populated (Sprint 1 ✓)
- No external math libraries beyond `sqlite3` + `decimal`

### Files to Create
- `src/analytics/__init__.py`
- `src/analytics/ratios.py`

### Risks
- Division by zero on any financial metric
- Year format mismatch between tables
- Missing company_id in joins

---

## Phase 3 — `src/analytics/cagr.py`

**Objective:** Build a CAGR (Compound Annual Growth Rate) engine that computes growth rates for `sales`, `net_profit`, and `stock_price` over configurable time windows.

### Core Logic
```
CAGR = ((Ending Value / Beginning Value) ^ (1 / N)) - 1
```
Where N = number of fiscal years between start and end.

### Six Sprint-Defined Edge Cases

1. **Positive → Positive** — Both beginning and ending values are positive. Standard CAGR computation with no sign adjustments. Example: sales growing from 100→150 over 3 years.

2. **Positive → Negative (DECLINE_TO_LOSS)** — Beginning value is positive, ending value is negative. CAGR formula produces no real result. Return CAGR = `None`, set `flag = "DECLINE_TO_LOSS"`, and log to `ratio_edge_cases.log`.

3. **Negative → Positive (TURNAROUND)** — Beginning value is negative, ending value is positive. CAGR formula produces no real result when beginning value is negative. Return CAGR = `None`, set `flag = "TURNAROUND"`, and log to `ratio_edge_cases.log`.

4. **Negative → Negative (BOTH_NEGATIVE)** — Both beginning and ending values are negative. Compute CAGR using absolute values for the ratio, then apply sign logic. Return signed CAGR with `flag = "BOTH_NEGATIVE"`, and log to `ratio_edge_cases.log`.

5. **ZERO_BASE** — Beginning value is zero. Division by zero is mathematically impossible. Return CAGR = `None`, set `flag = "ZERO_BASE"`, and log to `ratio_edge_cases.log`.

6. **INSUFFICIENT** — Fewer than 2 data points available for the requested period. Cannot compute any growth rate. Return CAGR = `None`, set `flag = "INSUFFICIENT"`, and log to `ratio_edge_cases.log`.

### Output
- Dictionary of CAGR results per `(company_id, metric, period)`
- Side-effect: log entries to `ratio_edge_cases.log`

### Dependencies
- Requires: `profitandloss.sales`, `profitandloss.net_profit`, `stock_prices.close_price`
- `ratios.py` should be read (for understanding patterns) but CAGR has no hard dependency on it

### Files to Create
- `src/analytics/cagr.py`

### Risks
- Year column is timestamp string, must extract fiscal year before sorting
- Companies with only 1 year of data (newer listings) will produce all-None CAGR — should not crash
- Stock price CAGR requires aligning dates to fiscal year-end

---

## Phase 4 — `src/analytics/cashflow_kpis.py`

**Objective:** Build cash flow analytics module computing working capital efficiency, FCF quality, and capital allocation classification.

### KPI Definitions

| KPI | Formula | Source Columns | Edge Cases |
|---|---|---|---|
| Free Cash Flow (FCF) | `operating_activity - capex_cr` | cashflow, financial_ratios | Either is null → None; negative FCF is valid |
| CFO Quality Ratio | `operating_activity / net_profit` | cashflow, profitandloss | net_profit=0 or null → None |
| CapEx Intensity | `capex_cr / operating_activity` | financial_ratios, cashflow | operating_activity=0 → None; capex_cr=0 → 0.0 |
| FCF Conversion | `FCF / operating_activity` | Computed from above | operating_activity=0 → None |
| Capital Allocation | See classifier logic below | Computed from above | — |

### Capital Allocation Classifier

Classify each company-year into exactly one of 8 categories based on combined cash flow and financial signals:

| Category | Classification Rule |
|---|---|
| `GROWTH` | FCF conversion > 50% AND CapEx > 20% of operating cash flow |
| `DIVIDEND` | Dividend payout ratio > 30% AND CFO Quality > 80% |
| `DEBT_REDUCTION` | FCF positive AND debt_to_equity > 1.0 AND not GROWTH |
| `REINVEST` | CapEx Intensity > 40% AND positive operating cash flow |
| `ACQUISITIVE` | Free cash flow negative for 2+ consecutive years WITH sustained CapEx spending |
| `BUYBACK` | Dividend payout < 10% AND positive FCF AND low debt |
| `LIQUIDATING` | Operating cash flow negative for 3+ consecutive years |
| `NEUTRAL` | None of the above conditions met |

### Multi-Year Classification Rules

- **ACQUISITIVE** and **LIQUIDATING** require rolling multi-year analysis, not single-year classification
- **BUYBACK** requires both low leverage and high FCF — not just zero dividends

### Output
- Dictionary of KPI results per `(company_id, year)`
- Capital allocation category string
- Side-effect: writes to `ratio_edge_cases.log` for division-by-zero events

### Dependencies
- Requires: `cashflow`, `profitandloss`, `financial_ratios` tables populated
- Requires `ratios.py` concept (division handling patterns) but no direct import dependency

### Files to Create
- `src/analytics/cashflow_kpis.py`

### Risks
- Capital allocation classifier boundary conditions — many companies may be "NEUTRAL"
- CFO Quality with negative net_profit produces negative ratio — need to handle
- FCF Conversion when operating_activity is negative → meaningless ratio

---

## Phase 5 — Database Population Pipeline

**Objective:** Build the script that executes all analytics computations and writes results to:
1. `financial_ratios` table — UPDATE existing records with newly computed values
2. `capital_allocation.csv` — new output file with capital allocation per company/year
3. `ratio_edge_cases.log` — log file capturing all edge cases encountered

### Pipeline Logic

```
for each (company_id, year) in profitandloss:
    ratios = compute_ratios(company_id, year)        # from ratios.py
    cagr_values = compute_cagr(company_id)            # from cagr.py
    kpis = compute_cashflow_kpis(company_id, year)    # from cashflow_kpis.py
    
    upsert into financial_ratios
    append to capital_allocation.csv
    if any edge case: append to ratio_edge_cases.log
```

### Table Operation Strategy

**Option A (Recommended):** Create a separate `analytics` table or use the existing `analysis` table for CAGR-specific computed values. For `financial_ratios`, compute and verify against existing values but store in a separate analytics-specific table to avoid overwriting source data.

**Recommended schema addition:**
```sql
CREATE TABLE analytics_computed (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT,
    source_type TEXT,  -- 'RATIO', 'CAGR', 'CASHFLOW_KPI'
    metric_name TEXT,
    metric_value REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
```

Alternatively, UPDATE the existing `financial_ratios` table in-place.

### Output File Formats

**capital_allocation.csv:**
```
company_id,year,fcf,operating_cash_flow,capex,capital_allocation_category
ABB,2012-12-01,42.0,101.0,59.0,GROWTH
...
```

**ratio_edge_cases.log:**
```
[2026-07-22 15:30:00] EDGE001: CAGR base value zero/negative — company=WIPRO, metric=sales, period=2020-2023
[2026-07-22 15:30:01] EDGE002: Division by zero (interest=0) — company=ABB, year=2012-12-01
...
```

### Files to Create
- `src/analytics/populate.py` (runner script)
- `data/output/capital_allocation.csv` (generated)
- `data/output/ratio_edge_cases.log` (generated)

### Dependencies
- Depends on Phases 2, 3, 4 being complete
- Requires `db/nifty100.db` to be populated (Sprint 1 ✓)

### Risks
- Writing to the same `financial_ratios` table that was ETL-loaded may cause confusion — recommend a separate analytics table
- Upsert logic in SQLite requires `INSERT OR REPLACE` or explicit DELETE + INSERT
- Must not modify the source `nifty100.db` schema without a migration plan

---

## Phase 6 — Unit Tests

**Objective:** Ensure every analytics function is tested with known inputs and expected outputs, including all edge cases.

### Test Files to Create

| File | Module Under Test | Test Count Estimate |
|---|---|---|
| `tests/analytics/test_ratios.py` | `src/analytics/ratios.py` | ~15 tests |
| `tests/analytics/test_cagr.py` | `src/analytics/cagr.py` | ~12 tests |
| `tests/analytics/test_cashflow_kpis.py` | `src/analytics/cashflow_kpis.py` | ~12 tests |

### Test Patterns to Follow

- Use existing `tests/conftest.py` pattern: in-memory SQLite with schema applied
- Insert known data, run computation, assert results
- Cover all 6 CAGR edge cases explicitly
- Cover all 5 capital allocation categories with known inputs
- Test division-by-zero paths

### Edge Case Test Matrix

| # | Scenario | Module | Expected Behavior |
|---|---|---|---|
| 1 | sales=0, net_profit positive | ratios | Profit margin → None |
| 2 | equity=0, net_profit positive | ratios | ROE → None |
| 3 | interest=0, operating_profit positive | ratios | Interest coverage → None |
| 4 | Positive→Positive CAGR | cagr | Standard CAGR computed |
| 5 | Positive→Negative (DECLINE_TO_LOSS) | cagr | CAGR=None, flag=DECLINE_TO_LOSS |
| 6 | Negative→Positive (TURNAROUND) | cagr | CAGR=None, flag=TURNAROUND |
| 7 | Negative→Negative (BOTH_NEGATIVE) | cagr | Signed CAGR with flag=BOTH_NEGATIVE |
| 8 | ZERO_BASE (beginning = 0) | cagr | CAGR=None, flag=ZERO_BASE |
| 9 | INSUFFICIENT data (< 2 points) | cagr | CAGR=None, flag=INSUFFICIENT |
| 10 | Negative operating_activity | cashflow_kpis | FCF Conversion → None |
| 11 | All cash flow fields null | cashflow_kpis | All KPIs → None |
| 12 | Very large/small values | all | No overflow |
| 13 | Missing company in FK | all | Skip silently |

### Dependencies
- Requires `src/analytics/*.py` modules to exist (Phases 2–4)
- Requires `tests/conftest.py` for fixtures — may need additional fixtures

---

## Phase 7 — Integration

**Objective:** Execute the full analytics pipeline against the populated database and validate outputs.

### Steps

1. **Run the population script** against `nifty100.db`
2. **Verify row counts:**
   - Rows in `financial_ratios` before vs. after run
   - Rows in `capital_allocation.csv`
   - Rows in `ratio_edge_cases.log`
3. **Spot-check known values:**
   - Manually verify 3–5 companies' known ratios against source Excel
   - Verify CAGR for a company with 5+ years of data
   - Verify capital allocation classification for a GROWTH and NEUTRAL company
4. **Edge case verification:**
   - Confirm companies with zero-interest years appear in `ratio_edge_cases.log`
   - Confirm missing companies are skipped, not crashed
5. **Run existing Sprint 1 test suite** to verify no regressions
6. **Document findings** in Sprint Review

### Integration Test Scenarios

| Test | What to Check |
|---|---|
| Full pipeline run | No exceptions, all 90 companies processed |
| capital_allocation.csv | Meets expected column format, 1 row per (company,year) |
| ratio_edge_cases.log | Contains entries, not empty (unless zero edge cases) |
| Database integrity | No FK violations created by analytics pipeline |
| Performance | Full pipeline completes in < 30 seconds |

### Dependencies
- All prior phases complete
- `nifty100.db` populated (Sprint 1)

---

## Complete Dependency Graph

```
Phase 1 (Gap Analysis)
  │
  ├──► Phase 2 (ratios.py) ──────────┐
  │                                   │
  ├──► Phase 3 (cagr.py) ────────────┤
  │                                   │
  └──► Phase 4 (cashflow_kpis.py) ───┤
                                      │
                        Phase 5 (Populate Pipeline) ◄──── All three
                                      │
                        Phase 6 (Unit Tests) ──────────── Phases 2–4
                                      │
                        Phase 7 (Integration) ──────────── Phase 5, Phase 6 pass
```

**Execution order is strict:** Phase 1 → 2 → 3 → 4 → 5 → 6 → 7

---

## Reusable Code Analysis

| Existing Asset | How to Reuse in Sprint 2 |
|---|---|
| `src/etl/utils.py` — `normalize_dataframe()` | Data cleaning before computation |
| `src/etl/utils.py` — `detect_header_row()` | Not directly reusable (CSV, not Excel) |
| `tests/conftest.py` — `in_memory_db` fixture | Extend for analytics tests with pre-loaded test data |
| Schema SQL in `db/schema.sql` | Reference for column names and types |
| `loader.py` — chunked insert pattern | Reuse for `populate.py` SQLite writes |
| Validator DQ checks | Reference: DQ-05 (OPM), DQ-06 (sales), DQ-08 (cashflow) show which validation patterns exist |
| `analysis_id_investigation.md` | Understand existing CAGR data structure |

---

## Sprint 2 Execution Checklist

- [ ] Phase 1: All gap checks documented and acknowledged
- [ ] Phase 2: `src/analytics/__init__.py` created
- [ ] Phase 2: `src/analytics/ratios.py` implements profitability/leverage/efficiency computations
- [ ] Phase 3: `src/analytics/cagr.py` implements CAGR engine with all 6 edge case handlers
- [ ] Phase 4: `src/analytics/cashflow_kpis.py` implements FCF/CFO/CapEx/FCF Conversion + Capital Allocation
- [ ] Phase 5: Populate pipeline writes to DB, `capital_allocation.csv`, `ratio_edge_cases.log`
- [ ] Phase 6: All analytics modules have unit tests covering edge cases
- [ ] Phase 7: Integration run produces valid outputs with no regressions