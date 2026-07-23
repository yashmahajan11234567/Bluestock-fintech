import pandas as pd
import os

def inspect_excel(filepath):
    print(f"Inspecting {filepath}")
    xl = pd.ExcelFile(filepath)
    print(f"Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        print(f"  Sheet: {sheet}")
        print(f"    Columns: {df.columns.tolist()}")
        print(f"    Shape: {df.shape}")
        if df.shape[0] > 0:
            print(f"    First row: {df.iloc[0].to_dict()}")
        print()

inspect_excel('Data/raw/analysis.xlsx')
inspect_excel('Data/raw/profitandloss.xlsx')
