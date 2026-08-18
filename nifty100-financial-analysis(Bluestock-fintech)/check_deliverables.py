import os
import pandas as pd

# Check screener_output.xlsx
path = 'Data/output/screener_output.xlsx'
if os.path.exists(path):
    print(f'{path} EXISTS, size: {os.path.getsize(path)} bytes')
else:
    print(f'{path} NOT FOUND')

# Check pros_cons_generated.csv
path = 'Data/output/pros_cons_generated.csv'
if os.path.exists(path):
    df = pd.read_csv(path)
    print(f'{path} EXISTS, rows: {len(df)}, companies: {df["company_id"].nunique() if "company_id" in df.columns else "N/A"}')
    print(df['company_id'].unique()[:20] if 'company_id' in df.columns else 'N/A')
else:
    print(f'{path} NOT FOUND')

# Check validation_failures.csv
path = 'Data/output/validation_failures.csv'
if os.path.exists(path):
    df = pd.read_csv(path)
    print(f'{path} EXISTS, rows: {len(df)}, cols: {df.columns.tolist()}')
else:
    print(f'{path} NOT FOUND')

# Check tearsheets
path = 'reports/tearsheets/'
if os.path.exists(path):
    files = os.listdir(path)
    print(f'{path} EXISTS, {len(files)} files')
else:
    print(f'{path} NOT FOUND')

# Check cluster_labels
path = 'output/cluster_labels.csv'
if os.path.exists(path):
    df = pd.read_csv(path)
    print(f'{path} EXISTS, rows: {len(df)}, companies: {df["company_id"].nunique() if "company_id" in df.columns else "N/A"}')
else:
    print(f'{path} NOT FOUND')