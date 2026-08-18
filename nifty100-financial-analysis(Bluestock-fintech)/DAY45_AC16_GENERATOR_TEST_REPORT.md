# DAY 45 — AC-16 CONTROLLED GENERATOR TEST REPORT

## 1. Database Confirmation

**Read-only database queries:**
```
SELECT COUNT(*) FROM companies;
```
Result: **92 companies**

```
SELECT COUNT(DISTINCT company_id) FROM financial_ratios;
```
Result: **94 companies** (some companies may have financial ratios but not be in the main companies list, or vice versa)

**First 10 companies in financial_ratios:**
- ABB: 59 ratios
- ADANIENSOL: 34 ratios
- ADANIENT: 37 ratios
- ADANIGREEN: 25 ratios
- ADANIPORTS: 61 ratios
- ADANIPOWER: 37 ratios
- AMBUJACEM: 35 ratios
- APOLLOHOSP: 37 ratios
- ASIANPAINT: 61 ratios
- ATGL: 8 ratios

**Conclusion:** The database contains 92 canonical companies (excluding TEST) with sufficient financial data for pros/cons generation.

## 2. Controlled Generator Test

**Exact generator command executed:**
```python
python -c "from src.nlp.pros_cons_generator import generate_output; generate_output('Data/output/pros_cons_generated_INVESTIGATION.csv')"
```

**Generator output:** `Generated 800 signals for 92 companies`

## 3. Generated Investigation File Inspection

**File:** `Data/output/pros_cons_generated_INVESTIGATION.csv`
- **Absolute path:** `C:\Users\hitoy\Downloads\Bluestock_fintech\nifty100-financial-analysis(Bluestock-fintech)\Data\output\pros_cons_generated_INVESTIGATION.csv`
- **File size:** 91,062 bytes
- **Total rows:** 801 (1 header + 800 data rows)
- **Unique company IDs:** 92
- **Canonical company count:** 92 (0 TEST companies)
- **TEST count:** 0
- **Pro count:** 344
- **Con count:** 456
- **Companies with >=1 pro:** 92 (100%)
- **Companies with >=1 con:** 92 (100%)
- **Companies with both pro and con:** 92 (100%)

**Comparison with existing acceptance CSV (`Data/output/pros_cons_generated.csv`):**
| Metric | Current Acceptance File | Generated Investigation File |
|--------|-------------------------|------------------------------|
| File size | 914 bytes | 91,062 bytes |
| Total rows | 9 | 801 |
| Data rows | 8 | 800 |
| Unique company IDs | 1 (TEST only) | 92 |
| Canonical company count | 0 | 92 |
| TEST count | 8 | 0 |
| Pro count | 8 | 344 |
| Con count | 0 | 456 |
| Companies with >=1 pro | 1 (TEST only) | 92 |
| Companies with >=1 con | 0 | 92 |
| Companies with both pro and con | 0 | 92 |

## 4. Root Cause Determination

**RESULT: GENERATOR BEHAVIOR IS CORRECT (Possibility A)**

The controlled test demonstrates that:
- The `pros_cons_generator.py` script functions correctly when executed
- It reads from the database and generates pros/cons signals for all 92 canonical companies
- Each company receives both pro and con signals (100% coverage)
- Output matches exactly what the previous AC-16 remediation claimed: 800 rows for 92 companies

**Therefore, the discrepancy is explained by:**
The `Data/output/pros_cons_generated.csv` file in the repository is **stale** - it contains outdated TEST-only data from a previous execution or test scenario, while the generator itself is working correctly and capable of producing the full 800-row output.

The file is not modified from HEAD (per git status), indicating it was deliberately committed in this state, likely as part of earlier testing or development work.

## 5. Recommended Next Step

**Perform controlled production-output regeneration:**
Since the generator works correctly and the database contains the expected data, the acceptance file should be regenerated using the proper process.

**However, per investigation constraints:**
DO NOT modify `Data/output/pros_cons_generated.csv` in this round.

**For future AC-16 remediation:**
1. Verify that the generation process is part of the approved ETL/pipeline
2. Ensure the generation script is executed with the correct parameters
3. Confirm the output is written to the correct location: `Data/output/pros_cons_generated.csv`
4. Validate that the regenerated file contains 800 rows for 92 companies with both pro and con signals

**Important:** Do NOT claim AC-16 PASS yet. The acceptance file still contains the stale TEST-only data. The root cause has been identified as a stale file issue, not a generator or database problem.