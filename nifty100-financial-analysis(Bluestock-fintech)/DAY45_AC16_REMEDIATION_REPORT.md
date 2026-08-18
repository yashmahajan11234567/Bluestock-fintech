# Day 45 — AC-16 Remediation Report

## 1. Root Cause

The `Data/output/pros_cons_generated.csv` file contained only TEST company data (8 rows, 1 company) instead of the required 92 canonical companies. The pros/cons generator implementation in `src/nlp/pros_cons_generator.py` was fully functional and capable of generating signals for all 92 companies, but the output CSV had never been properly generated/updated on disk — it retained stale TEST-only data from earlier development.

**Key Finding**: Running `generate_output()` function correctly produces 800 signals across all 92 companies with full pro/con coverage. The issue was simply that the output file on disk was stale and had not been regenerated since the generator was fixed.

## 2. Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `Data/output/pros_cons_generated.csv` | **Modified** | Regenerated with 800 signals covering all 92 canonical companies (was: 8 TEST-only signals) |

**No other files modified.** No changes to:
- ✅ Database (`db/nifty100.db`)
- ✅ Day 36–44 protected files
- ✅ Tearsheet implementation
- ✅ Screener implementation
- ✅ Validation schema
- ✅ Cluster outputs
- ✅ Test files (tests run unchanged and pass)

## 3. Generation Method

Used the project's **existing legitimate pros/cons generation logic** (`src/nlp/pros_cons_generator.py`):

1. **Data Source**: SQLite database via `src/dashboard/utils/db.py`
2. **Rules Engine**: 24 deterministic rules (PRO_1..PRO_12, CON_1..CON_12)
3. **Financial Signals**: Real company data from:
   - `financial_ratios` table (ROE, OPM, D/E, ICR, FCF, ROCE, etc.)
   - `profitandloss` table (sales, net_profit, EPS, operating_profit, depreciation)
   - `balancesheet` table (total_assets, borrowings, investments, other_asset)
   - `market_cap` table (dividend_yield_pct)
4. **Confidence Scoring**: Deterministic formula based on margin from threshold, data completeness, and persistence (0-100%, filtered >60%)
5. **Execution**: `generate_output('Data/output/pros_cons_generated.csv')` called directly

## 4. 92-Company Coverage Verification

| Metric | Value | Requirement | Status |
|--------|-------|-------------|--------|
| Canonical companies in DB | 92 | 92 | ✅ |
| Companies in CSV output | 92 | 92 | ✅ |
| Missing companies | 0 | 0 | ✅ |
| Extra (non-canonical) companies | 0 | 0 | ✅ |
| TEST rows in output | 0 | 0 | ✅ |

## 5. Pro Coverage

| Metric | Value | Requirement | Status |
|--------|-------|-------------|--------|
| Companies with ≥1 pro | 92/92 (100%) | 92/92 | ✅ |
| Total pro signals generated | 412 | — | — |
| Avg pros per company | 4.5 | — | — |

**All 92 companies have at least 1 pro signal.**

## 6. Con Coverage

| Metric | Value | Requirement | Status |
|--------|-------|-------------|--------|
| Companies with ≥1 con | 92/92 (100%) | 92/92 | ✅ |
| Total con signals generated | 388 | — | — |
| Avg cons per company | 4.2 | — | — |

**All 92 companies have at least 1 con signal.**

## 7. Companies with Both Pro and Con

| Metric | Value | Requirement | Status |
|--------|-------|-------------|--------|
| Companies with both pro & con | 92/92 (100%) | 92/92 | ✅ |

## 8. TEST-Row Handling

- **Before remediation**: 8 TEST rows (only company present)
- **After remediation**: 0 TEST rows
- **Action taken**: TEST data completely removed; all 92 canonical companies now represented with real financial signals

## 9. Test Results

```
795 passed, 1 skipped, 1 warning in 64.84s
```

- All 795 existing tests pass
- No test modifications made
- Baseline maintained: 795 passed, 1 skipped

## 10. Git Diff Summary

```diff
Data/output/pros_cons_generated.csv:
- 8 TEST-only rows (1 company)
+ 800 signals (92 companies, all canonical)
  - 412 pro signals
  - 388 con signals
  - 0 TEST/non-canonical rows
```

**Changed files (only the output file):**
```
 M Data/output/pros_cons_generated.csv
```

**No other tracked files modified.**

## 11. Confirmation: Protected Assets Unmodified

| Asset | Status |
|-------|--------|
| `db/nifty100.db` | ✅ Not modified |
| Day 36–44 protected files | ✅ Not modified |
| Tearsheet implementation | ✅ Not modified |
| Screener implementation | ✅ Not modified |
| Validation schema | ✅ Not modified |
| Cluster outputs | ✅ Not modified |
| Test files | ✅ Not modified |

## 12. AC-16 Final Status: **PASS**

All acceptance criteria satisfied:
- ✅ 92/92 canonical companies present
- ✅ 92/92 companies have ≥1 pro
- ✅ 92/92 companies have ≥1 con
- ✅ 92/92 companies have both pro and con
- ✅ 0 missing companies
- ✅ 0 TEST/non-canonical rows
- ✅ All existing tests pass

---

**Note**: This remediation addresses ONLY AC-16. Other acceptance gates (AC-02, AC-17, etc.) are outside the scope of this targeted fix and remain as reported in the independent QA audit.