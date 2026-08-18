import pandas as pd
from pathlib import Path

def check_raw_data_for_company(company_id):
    raw_dir = Path(__file__).parent / "Data" / "raw"
    files = [
        ('profitandloss.xlsx', 'profitandloss'),
        ('balancesheet.xlsx', 'balancesheet'),
        ('cashflow.xlsx', 'cashflow')
    ]

    for file_name, table_name in files:
        print(f"\n{table_name.upper()} for {company_id}:")
        df = pd.read_excel(raw_dir / file_name, header=1)
        # Filter for the company
        company_df = df[df['company_id'] == company_id]
        if len(company_df) == 0:
            print("  NOT FOUND")
            continue
        print(f"  Number of rows: {len(company_df)}")
        # Show unique year values
        years = company_df['year'].unique()
        print(f"  Unique year values ({len(years)}): {sorted(years)[:20]}")  # Show first 20
        # Extract year part (first 4 digits if possible)
        def extract_year(val):
            if isinstance(val, str):
                if len(val) >= 4 and val[0:4].isdigit():
                    return val[0:4]
                # Handle Mar-13 format
                elif len(val) >= 3 and val[-2:].isdigit() and val[0:3].isalpha():
                    year_suffix = int(val[-2:])
                    if year_suffix <= 29:
                        return f"20{year_suffix:02d}"
                    else:
                        return f"19{year_suffix:02d}"
                else:
                    import re
                    match = re.search(r'(\d{4})', val)
                    if match:
                        return match.group(1)
            return None
        company_df['year_extracted'] = company_df['year'].apply(extract_year)
        extracted_years = company_df['year_extracted'].dropna().unique()
        print(f"  Distinct extracted years ({len(extracted_years)}): {sorted(extracted_years)}")

if __name__ == "__main__":
    # Check the companies from the dispute report that we have in DB
    companies_to_check = ['NAUKRI', 'NESTLEIND', 'M&M']  # M&M is in DB as 'M&M'
    for cid in companies_to_check:
        print(f"===== {cid} =====")
        check_raw_data_for_company(cid)