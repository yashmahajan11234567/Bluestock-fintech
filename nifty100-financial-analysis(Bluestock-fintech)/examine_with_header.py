import pandas as pd
from pathlib import Path

def examine_file_with_header(file_path, header_row=1):
    print(f"\n=== Examining {file_path} with header row {header_row} ===")
    try:
        df = pd.read_excel(file_path, header=header_row)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")

        # Look for year column
        year_cols = [col for col in df.columns if 'year' in col.lower() or 'Year' in col]
        if year_cols:
            print(f"Year columns: {year_cols}")
            for col in year_cols:
                # Show sample values
                sample = df[col].dropna().unique()[:10]
                print(f"  Sample values in {col}: {sample}")
                # Count distinct years (assuming format might be YYYY-MM-DD or just YYYY)
                if df[col].dtype == 'object':
                    # Try to extract first 4 characters if it's a string
                    years = df[col].astype(str).str[:4].unique()
                    years = [y for y in years if y.isdigit() and len(y)==4]
                    print(f"  Distinct years (first 4 chars): {sorted(years)}")
                    print(f"  Count distinct years: {len(years)}")
                else:
                    # Assume numeric or datetime
                    print(f"  Distinct values: {df[col].unique()[:20]}")
        else:
            print("No year column found")

        # Show first few rows
        print("\nFirst 3 rows:")
        print(df.head(3))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    base = Path(__file__).parent
    raw_dir = base / "Data" / "raw"

    files = [
        "profitandloss.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx"
    ]

    for f in files:
        examine_file_with_header(raw_dir / f, header_row=1)