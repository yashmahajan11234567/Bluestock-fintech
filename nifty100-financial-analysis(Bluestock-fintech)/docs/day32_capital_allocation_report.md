# Day 32: Capital Allocation Report

## Sprint 5 - Day 32: Capital Allocation Report

### Overview

Day 32 produces three output files analyzing capital allocation patterns
across all Nifty 100 companies:

1. `Data/output/capital_allocation.csv` — Yearly capital allocation for every company
2. `Data/output/capital_allocation_distribution.csv` — Latest-year distribution across 5 categories
3. `Data/output/pattern_changes.csv` — Year-over-year pattern transitions

### Key Discrepancy: 5 Categories vs 8 Patterns

The Sprint specification mentions **8 capital allocation patterns**, but the
actual repository implementation in `src/analytics/capital_allocation.py`
defines only **5 categories**:

1. **Excellent** — ROE >= 20, ROCE >= 20, CCR >= 1.2
2. **Good** — ROE >= 15, ROCE >= 15, CCR >= 1.0
3. **Average** — ROE >= 10, ROCE >= 10, CCR >= 0.8
4. **Weak** — ROE >= 5, ROCE >= 5
5. **Poor** — Otherwise (ROE < 5 or ROCE < 5)

**Decision**: This implementation preserves the existing 5-category logic.
No artificial "8 patterns" were created. The discrepancy is documented here
as a specification vs. implementation gap.

### KPI Inputs

- **ROE**: `financial_ratios.return_on_equity_pct`
- **ROCE**: `financial_ratios.return_on_capital_employed_pct`
- **CFO**: `cashflow.operating_activity`
- **PAT**: `profitandloss.net_profit`
- **CCR**: CFO / PAT (computed via `cash_conversion_ratio()`)

### Output Files

#### 1. capital_allocation.csv

| Column | Description |
|--------|-------------|
| company_id | Company ticker |
| year | Fiscal year (INT) |
| capital_allocation | Category: Excellent/Good/Average/Weak/Poor |

- One row per company/year where ROE, ROCE, and CCR are all available
- No duplicate (company_id, year) pairs
- Missing data produces no row (not an invented category)

#### 2. capital_allocation_distribution.csv

| Column | Description |
|--------|-------------|
| capital_allocation | Category name |
| company_count | Number of companies in latest valid year |

- All 5 categories included, even if count is 0
- Based on latest valid year per company

#### 3. pattern_changes.csv

| Column | Description |
|--------|-------------|
| company_id | Company ticker |
| previous_year | Year of previous pattern |
| previous_pattern | Previous category |
| latest_year | Year of current pattern |
| latest_pattern | Current category |

- Only includes genuinely consecutive year changes (latest_year = previous_year + 1)
- Only includes actual pattern changes (previous != latest)
- All labels from the 5 valid categories

### Cash Flow Intelligence XLSX

The `Data/output/cashflow_intelligence.xlsx` from Day 31 already contains
the `capital_allocation` column with correct values. Day 32 does NOT add
a duplicate column (`capital_allocation_2` or `capital_allocation_label`).

### Test Coverage

37 tests in `tests/analytics/test_day32_capital_allocation_report.py`:

- 10 boundary tests for `capital_allocation_category()`
- 4 None-handling tests
- 7 schema validation tests for capital_allocation.csv
- 5 distribution validation tests
- 7 pattern_changes validation tests
- 4 cashflow_intelligence.xlsx validation tests
