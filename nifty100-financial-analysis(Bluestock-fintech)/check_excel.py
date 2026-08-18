import pandas as pd
from pathlib import Path

def check_excel_file(file_path):
    print(f"Checking {file_path}")
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst few rows:")
        print(df.head())
        print("\nData types:")
        print(df.dtypes)

        # Check for year column
        year_cols = [col for col in df.columns if 'year' in col.lower()]
        if year_cols:
            print(f"\nYear columns found: {year_cols}")
            for col in year_cols:
                print(f"Unique values in {col}: {df[col].unique()[:10]}")  # Show first 10 unique values
        else:
            print("\nNo year columns found")

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    base_path = Path(__file__).parent
    files_to_check = [
        "Data/raw/profitandloss.xlsx",
        "Data/raw/balancesheet.xlsx",
        "Data/raw/cashflow.xlsx"
    ]

    for file_path in files_to_check:
        full_path = base_path / file_path
        if full_path.exists():
            check_excel_file(full_path)
            print("="*50)
        else:
            print(f"File not found: {full_path}")