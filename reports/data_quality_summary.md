# Data Quality Summary

## Project
Bluestock Fintech - Mutual Fund Analytics

## Dataset Summary

- Total original datasets analysed: **10**
- Additional live NAV datasets fetched: **6**
- All datasets loaded successfully.

## Data Quality Checks

### Missing Values

- All datasets contain complete data except:
  - `04_monthly_sip_inflows.csv`
    - `yoy_growth_pct` has **12 missing values**, which is expected because Year-over-Year growth cannot be calculated for the first year.

### Duplicate Records

- No duplicate records were found in any dataset.

### Data Types

- Numeric columns are correctly detected.
- Date columns are currently stored as string (`object`) and will be converted to `datetime` during the data cleaning phase.

## Fund Master Analysis

- Fund Houses: **10**
- Categories: **2**
  - Equity
  - Debt
- Sub Categories: **12**
- Risk Categories:
  - Low
  - Moderate
  - Moderately High
  - High
  - Very High

## AMFI Validation

- Total AMFI Codes in fund_master.csv: **40**
- Total AMFI Codes in nav_history.csv: **40**
- All AMFI codes exist in nav_history.csv.

## Overall Assessment

The datasets are clean, consistent and ready for preprocessing in Day 2.