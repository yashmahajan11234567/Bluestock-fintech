# Dataset Profile

## analysis.xlsx

**Sheets:** Analysis

### Sheet: Analysis
- **Rows:** 20
- **Columns:** 6
- **Column Names:** id, company_id, compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe
- **Inferred Primary Key:** id
- **Missing Values:** None
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - compounded_sales_growth: object
  - compounded_profit_growth: object
  - stock_price_cagr: object
  - roe: object
- **First Row Appears as Title:** True
  - Recommendation: Consider using second row as header; current first row may be descriptive text.
- **Cleaning Recommendations:** None apparent.

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## balancesheet.xlsx

**Sheets:** Balance Sheet

### Sheet: Balance Sheet
- **Rows:** 1312
- **Columns:** 13
- **Column Names:** id, company_id, year, equity_capital, reserves, borrowings, other_liabilities, total_liabilities, fixed_assets, cwip, investments, other_asset, total_assets
- **Inferred Primary Key:** id
- **Missing Values:** None
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - year: object
  - equity_capital: float64
  - reserves: int64
  - borrowings: int64
  - other_liabilities: int64
  - total_liabilities: int64
  - fixed_assets: int64
  - cwip: int64
  - investments: int64
  - other_asset: int64
  - total_assets: int64
- **First Row Appears as Title:** True
  - Recommendation: Consider using second row as header; current first row may be descriptive text.
- **Cleaning Recommendations:**
  - Column "year" appears to be date but stored as object; consider converting to datetime.

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## cashflow.xlsx

**Sheets:** Cash Flow

### Sheet: Cash Flow
- **Rows:** 1187
- **Columns:** 7
- **Column Names:** id, company_id, year, operating_activity, investing_activity, financing_activity, net_cash_flow
- **Inferred Primary Key:** id
- **Missing Values:**
  - operating_activity: 2 missing (0.2%)
  - investing_activity: 2 missing (0.2%)
  - financing_activity: 2 missing (0.2%)
  - net_cash_flow: 2 missing (0.2%)
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - year: object
  - operating_activity: float64
  - investing_activity: float64
  - financing_activity: float64
  - net_cash_flow: float64
- **First Row Appears as Title:** True
  - Recommendation: Consider using second row as header; current first row may be descriptive text.
- **Cleaning Recommendations:**
  - Handle missing values (imputation/removal).

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## companies.xlsx

**Sheets:** Companies

### Sheet: Companies
- **Rows:** 92
- **Columns:** 12
- **Column Names:** id, company_logo, company_name, chart_link, about_company, website, nse_profile, bse_profile, face_value, book_value, roce_percentage, roe_percentage
- **Inferred Primary Key:** id
- **Missing Values:**
  - company_logo: 1 missing (1.1%)
  - website: 1 missing (1.1%)
  - nse_profile: 1 missing (1.1%)
  - bse_profile: 1 missing (1.1%)
  - face_value: 1 missing (1.1%)
  - book_value: 1 missing (1.1%)
  - roce_percentage: 1 missing (1.1%)
  - roe_percentage: 2 missing (2.2%)
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: object
  - company_logo: object
  - company_name: object
  - chart_link: object
  - about_company: object
  - website: object
  - nse_profile: object
  - bse_profile: object
  - face_value: float64
  - book_value: float64
  - roce_percentage: float64
  - roe_percentage: float64
- **First Row Appears as Title:** True
  - Recommendation: Consider using second row as header; current first row may be descriptive text.
- **Cleaning Recommendations:**
  - Handle missing values (imputation/removal).

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## documents.xlsx

**Sheets:** Documents

### Sheet: Documents
- **Rows:** 1585
- **Columns:** 4
- **Column Names:** id, company_id, Year, Annual_Report
- **Inferred Primary Key:** id
- **Missing Values:**
  - Annual_Report: 52 missing (3.3%)
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - Year: int64
  - Annual_Report: object
- **First Row Appears as Title:** True
  - Recommendation: Consider using second row as header; current first row may be descriptive text.
- **Cleaning Recommendations:**
  - Handle missing values (imputation/removal).

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## financial_ratios.xlsx

**Sheets:** Sheet1

### Sheet: Sheet1
- **Rows:** 1184
- **Columns:** 16
- **Column Names:** id, company_id, year, net_profit_margin_pct, operating_profit_margin_pct, return_on_equity_pct, debt_to_equity, interest_coverage, asset_turnover, free_cash_flow_cr, capex_cr, earnings_per_share, book_value_per_share, dividend_payout_ratio_pct, total_debt_cr, cash_from_operations_cr
- **Inferred Primary Key:** id
- **Missing Values:**
  - net_profit_margin_pct: 1 missing (0.1%)
  - operating_profit_margin_pct: 61 missing (5.2%)
  - interest_coverage: 93 missing (7.9%)
  - asset_turnover: 1 missing (0.1%)
  - free_cash_flow_cr: 2 missing (0.2%)
  - capex_cr: 2 missing (0.2%)
  - earnings_per_share: 4 missing (0.3%)
  - dividend_payout_ratio_pct: 4 missing (0.3%)
  - cash_from_operations_cr: 2 missing (0.2%)
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - year: object
  - net_profit_margin_pct: float64
  - operating_profit_margin_pct: float64
  - return_on_equity_pct: float64
  - debt_to_equity: float64
  - interest_coverage: float64
  - asset_turnover: float64
  - free_cash_flow_cr: float64
  - capex_cr: float64
  - earnings_per_share: float64
  - book_value_per_share: float64
  - dividend_payout_ratio_pct: float64
  - total_debt_cr: int64
  - cash_from_operations_cr: float64
- **First Row Appears as Title:** False
- **Cleaning Recommendations:**
  - Handle missing values (imputation/removal).
  - Column "year" appears to be date but stored as object; consider converting to datetime.

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## market_cap.xlsx

**Sheets:** Sheet1

### Sheet: Sheet1
- **Rows:** 552
- **Columns:** 9
- **Column Names:** id, company_id, year, market_cap_crore, enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
- **Inferred Primary Key:** id
- **Missing Values:** None
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - year: int64
  - market_cap_crore: float64
  - enterprise_value_crore: float64
  - pe_ratio: float64
  - pb_ratio: float64
  - ev_ebitda: float64
  - dividend_yield_pct: float64
- **First Row Appears as Title:** False
- **Cleaning Recommendations:** None apparent.

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## peer_groups.xlsx

**Sheets:** Sheet1

### Sheet: Sheet1
- **Rows:** 56
- **Columns:** 4
- **Column Names:** id, peer_group_name, company_id, is_benchmark
- **Inferred Primary Key:** id
- **Missing Values:** None
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - peer_group_name: object
  - company_id: object
  - is_benchmark: bool
- **First Row Appears as Title:** False
- **Cleaning Recommendations:** None apparent.

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## profitandloss.xlsx

**Sheets:** Profit & Loss

### Sheet: Profit & Loss
- **Rows:** 1276
- **Columns:** 15
- **Column Names:** id, company_id, year, sales, expenses, operating_profit, opm_percentage, other_income, interest, depreciation, profit_before_tax, tax_percentage, net_profit, eps, dividend_payout
- **Inferred Primary Key:** id
- **Missing Values:**
  - operating_profit: 13 missing (1.0%)
  - opm_percentage: 15 missing (1.2%)
  - tax_percentage: 95 missing (7.4%)
  - eps: 5 missing (0.4%)
  - dividend_payout: 103 missing (8.1%)
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - year: object
  - sales: int64
  - expenses: int64
  - operating_profit: float64
  - opm_percentage: float64
  - other_income: int64
  - interest: int64
  - depreciation: int64
  - profit_before_tax: int64
  - tax_percentage: float64
  - net_profit: int64
  - eps: float64
  - dividend_payout: float64
- **First Row Appears as Title:** True
  - Recommendation: Consider using second row as header; current first row may be descriptive text.
- **Cleaning Recommendations:**
  - Handle missing values (imputation/removal).

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## prosandcons.xlsx

**Sheets:** Pros & Cons

### Sheet: Pros & Cons
- **Rows:** 16
- **Columns:** 4
- **Column Names:** id, company_id, pros, cons
- **Inferred Primary Key:** id
- **Missing Values:**
  - pros: 5 missing (31.2%)
  - cons: 1 missing (6.2%)
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - pros: object
  - cons: object
- **First Row Appears as Title:** True
  - Recommendation: Consider using second row as header; current first row may be descriptive text.
- **Cleaning Recommendations:**
  - Handle missing values (imputation/removal).

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## sectors.xlsx

**Sheets:** Sheet1

### Sheet: Sheet1
- **Rows:** 92
- **Columns:** 6
- **Column Names:** id, company_id, broad_sector, sub_sector, index_weight_pct, market_cap_category
- **Inferred Primary Key:** id
- **Missing Values:** None
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - broad_sector: object
  - sub_sector: object
  - index_weight_pct: float64
  - market_cap_category: object
- **First Row Appears as Title:** False
- **Cleaning Recommendations:** None apparent.

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

## stock_prices.xlsx

**Sheets:** Sheet1

### Sheet: Sheet1
- **Rows:** 5520
- **Columns:** 9
- **Column Names:** id, company_id, date, open_price, high_price, low_price, close_price, volume, adjusted_close
- **Inferred Primary Key:** id
- **Missing Values:** None
- **Duplicate Rows:** 0 (0.0%)
- **Column Data Types:**
  - id: int64
  - company_id: object
  - date: object
  - open_price: float64
  - high_price: float64
  - low_price: float64
  - close_price: float64
  - volume: int64
  - adjusted_close: float64
- **First Row Appears as Title:** False
- **Cleaning Recommendations:**
  - Column "date" appears to be date but stored as object; consider converting to datetime.

#### Potential Foreign Key Relationships (across sheets)
No obvious foreign key relationships detected based on column name matching and uniqueness.

---

