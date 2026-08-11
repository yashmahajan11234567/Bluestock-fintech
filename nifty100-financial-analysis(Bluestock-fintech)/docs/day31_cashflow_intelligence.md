# Day 31: Cash Flow Intelligence

## Sprint 5 - Day 31: Cash Flow Intelligence

### Overview

The Day 31 Cash Flow Intelligence module provides 7 key performance indicators
that assess a company's cash generation quality, capital efficiency, financial
distress risk, and capital allocation quality.

### KIPs Computed

| # | KPI | Formula | Labels |
|---|-----|---------|--------|
| 1 | CFO Quality | Mean(CFO/PAT) over 5 years | High Quality (>1), Moderate (0.5-1), Accrual Risk (<=0.5) |
| 2 | CapEx Intensity | abs(investing_activity) / sales * 100 | Asset Light (<20%), Moderate (20-50%), Capital Intensive (>50%) |
| 3 | FCF CAGR 5yr | CAGR of free cash flow over 5 years | Numeric percentage |
| 4 | FCF Conversion | FCF_latest / PAT_latest * 100 | Numeric percentage |
| 5 | Distress Flag | CFO < 0 AND CFF > 0 | Boolean |
| 6 | Deleveraging Flag | CFF < 0 AND borrowings declining YoY | Boolean |
| 7 | Capital Allocation | capital_allocation_category(ROE, ROCE, CCR) | Excellent/Good/Average/Weak/Poor |

### Data Sources

- **Cash Flow**: `get_cashflow_data()` — operating_activity (CFO), investing_activity, financing_activity (CFF)
- **P&L**: `get_pl()` — net_profit (PAT), sales
- **Balance Sheet**: `get_bs()` — borrowings
- **Financial Ratios**: `get_financial_ratios()` — ROE, ROCE, capex_cr

### Reuse of Existing Functions

- `cash_conversion_ratio()` from `src/analytics/cashflow.py`
- `free_cash_flow()` from `src/analytics/cashflow.py`
- `calculate_cagr()` from `src/analytics/cagr.py`
- `capital_allocation_category()` from `src/analytics/capital_allocation.py`

### Output Files

1. `Data/output/cashflow_intelligence.xlsx` — 92 rows × 11 columns
2. `Data/output/distress_alerts.csv` — only companies flagged as distressed

### CFO Quality CAGR Handling

The FCF CAGR calculation follows the same pattern as the Pros/Cons generator's
`_compute_cagr_from_series`: only positive FCF values are considered, because
`calculate_cagr()` rejects non-positive start values. This ensures the CAGR
is computed from the first to last positive FCF year.

### Test Coverage

99 tests in `tests/analytics/test_cashflow_kpis.py`:
- 50+ pure function tests with edge cases (None, NaN, boundaries, empty)
- 8 integration tests using real DB data (BHARTIARTL, BRITANNIA, SBIN)
- 8 DataFrame-level tests (row count, columns, data types)
- 3 distress alert tests
