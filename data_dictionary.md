# Data Dictionary

## 01_fund_master.csv

| Column | Type | Description |
|---------|------|-------------|
| amfi_code | Integer | Unique AMFI Scheme Code |
| fund_house | Text | Mutual Fund Company |
| scheme_name | Text | Scheme Name |
| category | Text | Fund Category |
| sub_category | Text | Fund Sub Category |
| expense_ratio_pct | Float | Expense Ratio (%) |
| exit_load_pct | Float | Exit Load (%) |
| min_sip_amount | Integer | Minimum SIP Amount |
| min_lumpsum_amount | Integer | Minimum Lumpsum Amount |
| risk_category | Text | Risk Category |

---

## 02_nav_history.csv

| Column | Type | Description |
|---------|------|-------------|
| amfi_code | Integer | Scheme Code |
| date | Date | NAV Date |
| nav | Float | Net Asset Value |

---

## 07_scheme_performance.csv

| Column | Type | Description |
|---------|------|-------------|
| return_1yr_pct | Float | 1 Year Return |
| return_3yr_pct | Float | 3 Year Return |
| return_5yr_pct | Float | 5 Year Return |
| expense_ratio_pct | Float | Expense Ratio |
| aum_crore | Integer | Assets Under Management |
| risk_grade | Text | Risk Classification |

---

## 08_investor_transactions.csv

| Column | Type | Description |
|---------|------|-------------|
| investor_id | Text | Unique Investor ID |
| transaction_date | Date | Transaction Date |
| transaction_type | Text | SIP / Lumpsum / Redemption |
| amount_inr | Integer | Transaction Amount |
| state | Text | Investor State |
| city | Text | Investor City |
| payment_mode | Text | Payment Method |
| kyc_status | Text | KYC Verification Status |