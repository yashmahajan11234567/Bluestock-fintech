import pandas as pd
import os

raw_dir = 'data/raw'
files = [f for f in os.listdir(raw_dir) if f.endswith('.xlsx')]
for fname in files:
    path = os.path.join(raw_dir, fname)
    try:
        xls = pd.ExcelFile(path)
    except Exception as e:
        print(f"{fname}: failed to open - {e}")
        continue
    for sheet in xls.sheet_names:
        df_raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        # Look at first 10 rows
        print(f"\n{fname} - {sheet}")
        print(f"Shape: {df_raw.shape}")
        for i in range(min(10, df_raw.shape[0])):
            row_vals = list(df_raw.iloc[i])
            print(f"Row {i}: {row_vals}")
        # Determine header row: first row that does NOT contain the long title pattern in first column
        header_row = None
        for i in range(min(10, df_raw.shape[0])):
            first_cell = str(df_raw.iloc[i,0]) if not pd.isna(df_raw.iloc[i,0]) else ''
            if 'Bluestock Fintech' not in first_cell and 'Mkt Fintech' not in first_cell:
                # also check if row contains mostly non-null strings that look like headers
                non_null = [v for v in row_vals if pd.notna(v)]
                if len(non_null) > 0:
                    header_row = i
                    break
        if header_row is None:
            header_row = 0  # fallback
        print(f"Suggested header row: {header_row}")
        # Read with that header
        df = pd.read_excel(xls, sheet_name=sheet, header=header_row)
        print(f"Corrected columns ({len(df.columns)}): {list(df.columns)}")
        # Show first few rows of corrected df
        print("First 2 rows of corrected data:")
        print(df.head(2))
        print('-'*50)
