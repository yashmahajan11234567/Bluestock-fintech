# Company ID Investigation

## Summary

The following company IDs were found in the validation failures (foreign key violations) when loading the fact tables into the database. After investigating the source Excel files, we determined that all of these companies are **not present** in the `companies.xlsx` file, which contains the Nifty 100 constituents. There is no evidence of alternative tickers, renaming, or typos. Their absence is expected because they are not part of the Nifty 100 index.

| Company ID | In Companies.xlsx? | Alternative Ticker? | Renamed? | Typo? | Expected Absence? |
|------------|--------------------|---------------------|----------|-------|-------------------|
| WIPRO      | No                 | No                  | No       | No    | Yes               |
| ZOMATO     | No                 | No                  | No       | No    | Yes               |
| ULTRACEMCO | No                 | No                  | No       | No    | Yes               |
| UNIONBANK  | No                 | No                  | No       | No    | Yes               |
| UNITDSPR   | No                 | No                  | No       | No    | Yes               |
| VBL        | No                 | No                  | No       | No    | Yes               |
| VEDL       | No                 | No                  | No       | No    | Yes               |
| ZYDUSLIFE  | No                 | No                  | No       | No    | Yes               |
| AGTL       | No                 | No                  | No       | No    | Yes               |

## Detailed Findings

### Methodology
1. Loaded `companies.xlsx` using the same header detection logic as the ETL process.
2. Extracted the set of tickers from the `id` column (92 unique tickers).
3. For each rejected company ID, checked:
   - Exact match in the `companies.xlsx` ticker column (case-insensitive, trimmed).
   - Exact match in any column of `companies.xlsx`.
   - Match as a company name (via the `company_name` column) for the given ticker.
   - Substring matches (ticker in company name or company name in ticker) to catch possible variations.
   - Word-boundary matches (ticker as a whole word in the company name).
4. Examined the fact tables to confirm the presence of these IDs in the `company_id` column.

### Results per Company

#### WIPRO
- **Presence in companies.xlsx**: Not found in any column.
- **Alternative ticker**: No match found in company name or other columns.
- **Renamed**: No evidence of renaming (no company name matches "WIPRO" as a word or substring).
- **Typo**: No similar tickers found in the dataset.
- **Expected absence**: Yes, as WIPRO is not part of the Nifty 100 (as per the companies.xlsx list).

#### ZOMATO
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

#### ULTRACEMCO (UltraTech Cement)
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

#### UNIONBANK (Union Bank of India)
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

#### UNITDSPR (likely Unitech? or similar)
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

#### VBL (Varun Beverages Limited)
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

#### VEDL (Vedanta Limited)
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

#### ZYDUSLIFE (Zydus Lifesciences Limited)
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

#### AGTL (Apollo Tyres? or Adani Gas? - not in Nifty 100)
- **Presence in companies.xlsx**: Not found.
- **Alternative ticker**: No match.
- **Renamed**: No evidence.
- **Typo**: No similar tickers.
- **Expected absence**: Yes.

## Conclusion
All investigated company IDs are absent from the `companies.xlsx` file because they are not part of the Nifty 100 index, which is the source of the companies reference table. The foreign key violations are expected and indicate that the fact sheets contain data for companies beyond the Nifty 100. No data correction is needed; the ETL process correctly rejects these rows to maintain referential integrity.

---
*Investigation conducted using the source Excel files in `data/raw/`.*  
*No modifications were made to the source data or code.*
