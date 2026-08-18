# DAY45_FINAL_QA_REPORT.md

A. FINAL VERDICT
STATUS: FAIL
Multiple acceptance gates failed (AC-06, AC-07, AC-10, AC-13, AC-16, AC-17, AC-19).

B. AC-01
STATUS: PASS
Evidence: SELECT COUNT(*) FROM companies returned exactly 92 companies.

C. AC-02
STATUS: PASS
Evidence: 84 out of 92 companies (91.30%) have >=10 years of P&L, Balance Sheet, and Cash Flow data.
Qualifying companies: ABB, ADANIENSOL, ADANIENT, ADANIPORTS, ADANIPOWER, AMBUJACEM, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO, etc.

D. AC-03
STATUS: PASS
Evidence: PRAGMA foreign_key_check returned 0 rows.

E. AC-04
STATUS: PASS
Evidence: 
- Financial ratios count: 3532 (>=1,100 requirement)
- Duplicate company/year combinations: 1065 rows (noted but not disqualifying per requirements)

F. AC-05
STATUS: PASS
Evidence: 
- TCS 10-year Revenue CAGR manual calculation: 10.94%
- TCS analysis table value: 11.0%
- Difference: 0.06% (within 0.1% requirement)

G. AC-06
STATUS: FAIL
Evidence:
- TCS: stored=52.0%, computed=50.94%, diff=1.06% (PASS)
- ABB: stored=34.9%, computed=32.47%, diff=2.43% (PASS)
- ADANIENT: stored=13.64%, computed=8.53%, diff=5.11% (FAIL - exceeds 5%)
- ASIANPAINT: stored=31.45%, computed=29.68%, diff=1.77% (PASS)
- AXISBANK: stored=18.4%, computed=15.83%, diff=2.57% (PASS)
- Result: 4/5 companies pass, but ADANIENT failure makes overall gate fail

H. AC-07
STATUS: FAIL
Evidence:
- Quality Compounder preset filters applied: ROE>=15, Debt to Equity<=1, Free Cash Flow>=0, Revenue CAGR>=10
- Results returned: 2 companies
- Requirement: 10-50 companies
- FAIL: Only 2 companies found (outside required range)

I. AC-08
STATUS: PASS
Evidence:
- TCS: 0.068 seconds
- RELIANCE: 0.009 seconds
- HDFCBANK: 0.009 seconds
- INFY: 0.009 seconds
- ICICIBANK: 0.029 seconds
- All company profiles load in under 3 seconds

J. AC-09
STATUS: PASS
Evidence:
- Screener CSV export generated successfully
- File created, parsed successfully, header exists
- Rows are valid, no malformed columns
- No unexpected empty/corrupt output
- Quality Compounder screener produced 2 companies with proper CSV format

K. AC-10
STATUS: FAIL
Evidence:
- Files checked: nifty100-financial-analysis(Bluestock-fintech)/Data/output/tearsheets_test/
- HDFCBANK_tearsheet.pdf: 6 KB (FAIL - <30 KB)
- RELIANCE_tearsheet.pdf: 6 KB (FAIL - <30 KB)
- SUNPHARMA_tearsheet.pdf: 6 KB (FAIL - <30 KB)
- TATASTEEL_tearsheet.pdf: 6 KB (FAIL - <30 KB)
- TCS_tearsheet.pdf: 6 KB (FAIL - <30 KB)
- All PDFs contain extractable text (104-108 words each) but are undersized

L. AC-11
STATUS: PASS
Evidence:
- GET /api/v1/health returned HTTP 200
- Response contains: status = "ok"
- db_row_counts containing all 12 required tables:
  companies, profitandloss, balancesheet, cashflow, analysis, documents, prosandcons, sectors, stock_prices, financial_ratios, market_cap, peer_groups

M. AC-12
STATUS: PASS
Evidence:
- GET /api/v1/companies/TCS/ratios returned 13 total entries
- Unique years: 13 years (range: 0 to 2024)
- Requirement: 10+ years of ratio data (PASS)

N. AC-13
STATUS: FAIL
Evidence:
- screener_output.xlsx not found at expected location: nifty100-financial-analysis(Bluestock-fintech)/Data/output/screener_output.xlsx
- File not found anywhere in the project after search
- Requirement: File must be present for comparison (FAIL if genuinely absent)

O. AC-14
STATUS: PASS
Evidence:
- Number of peer groups: 11
- All 11 peer groups contain usable data (each has at least one company)
- Peer group names: Automobiles, Consumer Finance, FMCG, IT Services, Life Insurance, Oil & Gas, Pharmaceuticals, Power & Utilities, Private Banks, Public Sector Banks, Steel
- API verification: TCS returns peer group "IT Services" with 15 peers

P. AC-15
STATUS: PASS
Evidence:
- File: nifty100-financial-analysis(Bluestock-fintech)/output/cluster_labels.csv
- Total rows: 92 (exactly 92 canonical companies)
- Unique company_id: 92 (no duplicates)
- No missing canonical company
- cluster IDs valid (all non-negative integers)

Q. AC-16
STATUS: FAIL
Evidence:
- File: nifty100-financial-analysis(Bluestock-fintech)/Data/output/pros_cons_generated.csv
- Total rows: 8
- After removing TEST company rows: 0 rows
- Requirement: all 92 canonical companies represented with >=1 pro and >=1 con
- FAIL: No non-TEST company data found

R. AC-17
STATUS: FAIL
Evidence:
- Directory: reports/tearsheets/ not found
- Requirement: EXACTLY 92 PDFs in reports/tearsheets/ directory
- FAIL: Directory does not exist

S. AC-18
STATUS: PASS
Evidence:
- From repository ROOT: python -m pytest tests/ -q
- Results: 795 passed, 1 skipped, 1 warning
- Requirement: >=60 tests collected, 0 failures (PASS)

T. AC-19
STATUS: FAIL
Evidence:
- File: nifty100-financial-analysis(Bluestock-fintech)/Data/output/validation_failures.csv
- Header: rule_id,severity,table,row_number,column,value,message
- Required columns: company_id, field, issue, severity
- Missing columns: company_id, field, issue
- FAIL: CSV does not contain required column structure

U. AC-20
STATUS: PASS
Evidence:
- File: docs/analyst_guide.pdf
- Page count: 15 pages (using PyPDF2)
- Requirement: >=10 pages
- PASS: 15 pages >= 10

V. 23-DELIVERABLE INVENTORY
STATUS: ARCHIVE BLOCKED — AUTHORITATIVE 23-DELIVERABLE LIST UNAVAILABLE
Evidence: Day 45 project specification not available in repository to verify the 23-item deliverable list.

W. DATABASE SAFETY
STATUS: PASS
Evidence: 
- Database file: nifty100-financial-analysis(Bluestock-fintech)/db/nifty100.db
- No modifications made during QA (read-only verification)
- Table counts recorded but not altered
- Database remained unchanged throughout verification process

X. PROTECTED DAYS 36–44
STATUS: PASS
Evidence:
- Day 36: src/analytics/clustering.py and output/cluster_labels.csv verified (no unauthorized modifications)
- Day 37: cluster profiling outputs verified
- Day 38: API health/scaffold verified
- Day 39: companies API verified
- Day 40: screener/sectors/peers verified
- Day 41: valuation verified
- Day 42: API tests/integration tests verified (795 passed, 1 skipped)
- Day 43: src/dashboard/utils/db.py and performance optimization/cache verified
- Day 44: README/documentation/docstrings/code-quality work verified
- Note: src/dashboard/utils/db.py contains approved Day 40 + Day 43 changes and was not incorrectly flagged

Y. WARNINGS
- AC-04: Financial ratios table contains 1065 duplicate company/year combinations (data quality issue but not disqualifying)
- AC-07: FutureWarning about DataFrameGroupBy.apply operation (non-fatal pandas warning)
- AC-10: Tearsheet PDFs are undersized (6KB vs 30KB minimum) but contain readable text
- AC-14: Peer group table has 168 total rows but only 11 distinct groups (multiple entries per company is expected design)

Z. GENUINE FAILURES
- AC-06: ADANIENT ROE difference exceeds 5% tolerance
- AC-07: Quality Compounder preset returns only 2 companies (requires 10-50)
- AC-10: All tearsheet PDFs are undersized (6KB < 30KB minimum)
- AC-13: screener_output.xlsx file not found
- AC-16: pros_cons_generated.csv contains only TEST company data, no real companies
- AC-17: reports/tearsheets/ directory missing entirely
- AC-19: validation_failures.csv missing required columns (company_id, field, issue)

AA. ENVIRONMENTAL/VERIFIER LIMITATIONS
- No limitations encountered; all verification performed from repository root as required
- Database access successful via sqlite3
- API endpoints accessible on localhost:8003
- All required tools available (Python, requests, PyPDF2, pdftotext, etc.)

AB. FINAL RECOMMENDATION
DO NOT PROMOTE TO PRODUCTION.
Multiple genuine failures in core functionality:
1. Financial data accuracy issues (AC-06 ROE discrepancies)
2. Screener engine not returning adequate results for preset strategies (AC-07)
3. Missing or incomplete generated deliverables (AC-10, AC-13, AC-16, AC-17)
4. Validation data format incorrect (AC-19)
Remediation required before re-submission for QA.