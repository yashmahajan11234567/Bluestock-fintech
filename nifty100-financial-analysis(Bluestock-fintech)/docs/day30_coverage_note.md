# Day 30 Specification Coverage Note

## Sprint 5 - Day 30: Auto Pros/Cons Generator

## 1. Specification Summary

The Sprint 5 Day 30 specification defines exactly **24 rules**:

- **12 Pro rules** (PRO_1 through PRO_12)
- **12 Con rules** (CON_1 through CON_12)

### Pro Rules

| Rule | Condition |
|------|-----------|
| PRO_1 | ROE > 20% sustained for 3+ years |
| PRO_2 | FCF positive for 5+ consecutive years |
| PRO_3 | D/E = 0 (debt-free balance sheet) |
| PRO_4 | Revenue CAGR > 15% over 5 years |
| PRO_5 | OPM > 25% latest year |
| PRO_6 | PAT CAGR > 20% over 5 years |
| PRO_7 | ICR > 10 OR debt-free |
| PRO_8 | Dividend yield > 2% AND FCF positive |
| PRO_9 | EPS CAGR > 15% over 5 years |
| PRO_10 | ROE improving for 3 consecutive years |
| PRO_11 | Revenue CAGR > PAT CAGR |
| PRO_12 | Balance sheet assets growing with declining debt |

### Con Rules

| Rule | Condition |
|------|-----------|
| CON_1 | D/E > 2.0 for non-financial companies |
| CON_2 | FCF negative for 3 consecutive years |
| CON_3 | OPM declining for 3 consecutive years |
| CON_4 | Net profit negative latest year |
| CON_5 | Revenue declining for 2+ years |
| CON_6 | ICR < 1.5 |
| CON_7 | Dividend payout > 100% |
| CON_8 | D/E rising for 3 consecutive years |
| CON_9 | EPS declining for 3 consecutive years |
| CON_10 | ROCE < 10% |
| CON_11 | Net Debt > 3x EBITDA |
| CON_12 | Revenue CAGR < 5% over 5 years |

## 2. Implementation Status

All 24 rules are implemented in `src/nlp/pros_cons_generator.py` and tested in `tests/nlp/test_pros_cons_generator.py`.

- 12 Pro rules: implemented
- 12 Con rules: implemented
- RO_RULES = 12
- CON_RULES = 12
- Total rules = 24

## 3. Extension Testing (NOT in specification)

During development, PRO_13 and CON_13 were implemented as extensions to test
whether strict coverage (every company having both a Pro and a Con) could be
achieved with the supplied data:

- PRO_13: Sustained net profit margin > 10% (for financial institutions)
- CON_13: High PE ratio > 50x

These extensions were tested but are **NOT part of the final Sprint 5
implementation**. Tests explicitly confirm that:

- PRO_13 is not in PRO_RULES
- CON_13 is not in CON_RULES
- No output signal contains rule_id PRO_13 or CON_13

## 4. SBIN (0 Pros) - Factual Result

SBIN has **0 Pros** under the specified 24 rules. This is a factual result
of applying the rules to the supplied data:

| Rule | Reason for Not Qualifying |
|------|--------------------------|
| PRO_1 | ROE in financial_ratios is NULL for all years; companies table ROE (17.3%) is below 20% threshold |
| PRO_2 | FCF not positive for 5 consecutive years |
| PRO_3 | No balance sheet data available in database |
| PRO_4 | Revenue CAGR = 9.13% (below 15% threshold) |
| PRO_5 | OPM = -14% (banks do not have traditional operating margins) |
| PRO_6 | PAT CAGR = 12.76% (below 20% threshold) |
| PRO_7 | ICR = 0.37 (below 10, and not debt-free) |
| PRO_8 | Dividend yield = 0.42% (below 2% threshold) |
| PRO_9 | EPS CAGR = 10.11% (below 15% threshold) |
| PRO_10 | ROE is NULL, cannot determine improvement trend |
| PRO_11 | Revenue CAGR (9.13%) < PAT CAGR (12.76%) |
| PRO_12 | No balance sheet data available |

SBIN qualifies for 5 Con signals (CON_3, CON_5, CON_6, CON_9, CON_10),
reflecting legitimate financial concerns for a bank evaluated through
non-financial-institution metrics.

## 5. BRITANNIA (0 Cons) - Factual Result

BRITANNIA has **0 Cons** under the specified 24 rules. This is a factual result
of applying the rules to the supplied data:

| Rule | BRITANNIA Value | Threshold | Result |
|------|-----------------|-----------|--------|
| CON_1 | D/E = 0.68 | > 2.0 | Does not trigger |
| CON_2 | FCF positive all years | Negative 3y | Does not trigger |
| CON_3 | OPM improving | Declining 3y | Does not trigger |
| CON_4 | Net profit positive | Negative | Does not trigger |
| CON_5 | Revenue growing | Declining 2y | Does not trigger |
| CON_6 | ICR = 20.6 | < 1.5 | Does not trigger |
| CON_7 | Payout = 83% | > 100% | Does not trigger |
| CON_8 | D/E stable | Rising 3y | Does not trigger |
| CON_9 | EPS growing | Declining 3y | Does not trigger |
| CON_10 | ROCE = 48.9 | < 10% | Does not trigger |
| CON_11 | Net debt/EBITDA = 0.11 | > 3x | Does not trigger |
| CON_12 | Revenue CAGR = 9.49% | < 5% | Does not trigger |

BRITANNIA qualifies for 6 Pro signals (PRO_1, PRO_6, PRO_7, PRO_9, PRO_10, PRO_12),
reflecting genuinely strong financial health.

## 6. ROE Backfill Decision

The companies table contains `roe_percentage` values that could be used to
backfill NULL values in `financial_ratios.return_on_equity_pct`.

**Decision**: ROE backfill from the companies table was **not retained** in
the final implementation because:

1. The companies table ROE appears to be stale/summary data, not yearly values.
2. For SBIN, the companies table ROE (17.3%) would not trigger any PRO rule
   (PRO_1 requires > 20%, PRO_10 requires trend data).
3. Using static summary data would be inappropriate for trend-based rules
   (PRO_1, PRO_10) which require yearly values.
4. The backfill would be a data-quality workaround rather than a specification
   requirement.

## 7. Coverage Report

Generated from `Data/output/pros_cons_generated.csv`:

| Metric | Value |
|--------|-------|
| Total companies | 92 |
| Total signals | 745 |
| Pro signals | 473 |
| Con signals | 272 |
| Companies with 0 Pros | 1 (SBIN) |
| Companies with 0 Cons | 1 (BRITANNIA) |

## 8. Conclusion

The Day 30 Auto Pros/Cons Generator is **specification-compliant**:

- Exactly 24 rules implemented (PRO_1-12, CON_1-12)
- No artificial signals generated
- No thresholds loosened
- No out-of-specification rules added
- SBIN and BRITANNIA coverage gaps are factual results of applying the
  specified rules to the supplied data, not generator defects

This is a **data/specification constraint**, not a code failure. The
requirement "every company must have Pro + Con" cannot be simultaneously
satisfied with the 24-rule specification and the supplied database.
