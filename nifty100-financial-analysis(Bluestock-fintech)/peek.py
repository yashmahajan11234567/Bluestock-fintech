import pandas as pd
import os

raw_dir = 'data/raw'
for file in os.listdir(raw_dir):
    if file.endswith('.xlsx'):
        print(f'\n=== {file} ===')
        try:
            xls = pd.ExcelFile(os.path.join(raw_dir, file))
            for sheet in xls.sheet_names:
                print(f'  Sheet: {sheet}')
                df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
                print('    Columns:', list(df.columns))
                print('    First 5 rows:')
                print(df.head())
                print()
        except Exception as e:
            print(f'    Error: {e}')
