import pandas as pd
from pathlib import Path
from src.etl import utils

def debug_header_detection(file_path):
    print(f"\n=== Debugging header detection for {file_path} ===")
    try:
        # Read with no header to see raw data
        raw_df = pd.read_excel(file_path, header=None)
        print(f"Raw DataFrame shape: {raw_df.shape}")
        print("First 5 rows:")
        print(raw_df.head())

        # Detect header row
        header_row = utils.detect_header_row(raw_df)
        print(f"Detected header row: {header_row}")

        # Show what the detected header row looks like
        if header_row < len(raw_df):
            header_values = []
            for val in raw_df.iloc[header_row]:
                if isinstance(val, str):
                    header_values.append(val.strip())
                else:
                    header_values.append(str(val).strip() if pd.notna(val) else "")
            print(f"Header row values: {header_values}")

        # Now read with the detected header
        df = pd.read_excel(file_path, header=header_row)
        print(f"\nDataFrame with header={header_row}:")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("First 3 rows:")
        print(df.head(3))

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    base = Path(__file__).parent
    raw_dir = base / "Data" / "raw"

    files = [
        "profitandloss.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx"
    ]

    for f in files:
        debug_header_detection(raw_dir / f)