import pandas as pd
from pathlib import Path

def check_raw_years():
    raw_dir = Path(__file__).parent / "Data" / "raw"
    files = ['profitandloss.xlsx', 'balancesheet.xlsx', 'cashflow.xlsx']
    table_names = ['profitandloss', 'balancesheet', 'cashflow']

    for file_name, table_name in zip(files, table_names):
        print(f"\n=== {table_name.upper()} ===")
        df = pd.read_excel(raw_dir / file_name, header=1)
        # We expect columns: id, company_id, year, ...
        # Let's check the company_id and year columns
        if 'company_id' not in df.columns or 'year' not in df.columns:
            print(f"ERROR: Expected columns company_id and year not found in {file_name}")
            print(f"Columns: {list(df.columns)}")
            continue

        # Group by company_id and count distinct years (after extracting first 4 digits if they are digits)
        def extract_year(val):
            if isinstance(val, str):
                # If it's in format YYYY-MM-DD HH:MM:SS
                if len(val) >= 4 and val[0:4].isdigit():
                    return val[0:4]
                # If it's in format Mar-13
                elif len(val) >= 3 and val[-2:].isdigit() and val[0:3].isalpha():
                    year_suffix = int(val[-2:])
                    if year_suffix <= 29:
                        return f"20{year_suffix:02d}"
                    else:
                        return f"19{year_suffix:02d}"
                else:
                    # Try to find any four consecutive digits
                    import re
                    match = re.search(r'(\d{4})', val)
                    if match:
                        return match.group(1)
            return None

        df['year_extracted'] = df['year'].apply(extract_year)
        # Now group by company_id and count distinct non-null years
        grouped = df.groupby('company_id')['year_extracted'].nunique()
        # Sort by the count
        grouped_sorted = grouped.sort_values()

        print(f"Number of companies: {len(grouped)}")
        print(f"Companies with <10 years: {(grouped < 10).sum()}")
        print(f"Companies with >=10 years: {(grouped >= 10).sum()}")
        print("\nFirst 10 companies with least years:")
        for company_id, count in grouped_sorted.head(10).items():
            print(f"  {company_id}: {count} years")

        print("\nLast 10 companies with most years:")
        for company_id, count in grouped_sorted.tail(10).items():
            print(f"  {company_id}: {count} years")

if __name__ == "__main__":
    check_raw_years()