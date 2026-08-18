import pandas as pd
from pathlib import Path

def check_raw_mm():
    raw_dir = Path(__file__).parent / "Data" / "raw"
    pl_path = raw_dir / "profitandloss.xlsx"
    # Read with header=1 (as we determined earlier)
    df = pd.read_excel(pl_path, header=1)
    # Filter for company_id = 'M&M'
    mm_df = df[df['company_id'] == 'M&M']
    print(f"Number of rows for M&M in profitandloss: {len(mm_df)}")
    if len(mm_df) > 0:
        print("First few rows:")
        print(mm_df[['id', 'company_id', 'year', 'sales']].head())
        print("\nUnique year values:")
        print(mm_df['year'].unique())
        # Now extract year part assuming format YYYY-MM-DD HH:MM:SS or similar
        # We'll try to get the first 4 characters if it's a string and starts with digits
        def extract_year(val):
            if isinstance(val, str):
                # If it matches YYYY-MM-DD HH:MM:SS
                if len(val) >= 4 and val[0:4].isdigit():
                    return val[0:4]
                # If it matches Mar-13 format
                elif len(val) >= 3 and val[-2:].isdigit() and val[0:3].isalpha():
                    # Assume 20xx for 00-29, 19xx for 30-99
                    year_suffix = int(val[-2:])
                    if year_suffix <= 29:
                        return f"20{year_suffix:02d}"
                    else:
                        return f"19{year_suffix:02d}"
                else:
                    return None
            return None
        mm_df['year_extracted'] = mm_df['year'].apply(extract_year)
        print("\nExtracted years:")
        print(mm_df['year_extracted'].unique())
        print(f"Distinct extracted years: {mm_df['year_extracted'].nunique()}")
    else:
        print("No rows found for company_id = 'M&M'")
        # Try case-insensitive or containing
        mm_df2 = df[df['company_id'].str.contains('M&M', case=False, na=False)]
        print(f"Rows with company_id containing 'M&M' (case-insensitive): {len(mm_df2)}")
        if len(mm_df2) > 0:
            print(mm_df2[['id', 'company_id', 'year']].head())

if __name__ == "__main__":
    check_raw_mm()