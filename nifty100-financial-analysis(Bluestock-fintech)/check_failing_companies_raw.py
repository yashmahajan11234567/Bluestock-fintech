import pandas as pd
from pathlib import Path

def check_failing_companies_raw():
    raw_dir = Path(__file__).parent / "Data" / "raw"
    files = [
        ('profitandloss.xlsx', 'profitandloss'),
        ('balancesheet.xlsx', 'balancesheet'),
        ('cashflow.xlsx', 'cashflow')
    ]

    # Companies that failed the intersection test (<10 common years)
    failing_companies = ['ADANIGREEN', 'ATGL', 'HAL', 'IRFC', 'JIOFIN', 'LICI', 'LODHA', 'SBIN']

    for company_id in failing_companies:
        print(f"\n{'='*50}")
        print(f"Checking {company_id}")
        print('='*50)

        for file_name, table_name in files:
            print(f"\n{table_name.upper()}:")
            df = pd.read_excel(raw_dir / file_name, header=1)
            # Filter for the company
            company_df = df[df['company_id'] == company_id]
            if len(company_df) == 0:
                print("  NOT FOUND in raw data")
                continue
            print(f"  Number of rows: {len(company_df)}")

            # Show unique year values
            years = company_df['year'].unique()
            print(f"  Unique year values ({len(years)}): {sorted(years)}")

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
    check_failing_companies_raw()