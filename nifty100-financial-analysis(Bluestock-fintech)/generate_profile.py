import pandas as pd
import os
import numpy as np

raw_dir = 'data/raw'
output_md = 'docs/dataset_profile.md'

def infer_primary_key(df):
    # Check if there's a column named 'id' that is unique and not null
    if 'id' in df.columns:
        if df['id'].notnull().all() and df['id'].nunique() == len(df):
            return 'id'
    # Check for company_id + year uniqueness (if both exist)
    if 'company_id' in df.columns and 'year' in df.columns:
        if df[['company_id', 'year']].dropna().duplicated().sum() == 0:
            return ['company_id', 'year']
    # Check for any single column that is unique and not null
    for col in df.columns:
        if df[col].notnull().all() and df[col].nunique() == len(df):
            return col
    return None

def infer_foreign_keys(df, all_sheets):
    fks = []
    # Simple heuristic: column ending with _id or named company_id that matches another table's primary key
    for col in df.columns:
        if col.endswith('_id') or col == 'company_id':
            # Look for other sheets where this column could be a primary key
            for sheet_name, other_df in all_sheets.items():
                if sheet_name == df_name:
                    continue
                # If other_df has column col and it is unique and not null (possible PK)
                if col in other_df.columns:
                    if other_df[col].notnull().all() and other_df[col].nunique() == len(other_df):
                        fks.append((col, sheet_name, col))
    return fks

def detect_title_row(df):
    # If first row contains a string that looks like a title (contains the file name or many spaces) and second row looks like header (contains typical column names)
    # Simple: if first row has any NaN or all values are strings and second row has less NaN?
    # We'll just rely on earlier detection: if first row is mostly NaN and second row has strings without NaN, then title.
    # For simplicity, we'll assume title row if first row has any NaN and second row has fewer NaNs.
    if df.shape[0] < 2:
        return False
    first_row_nulls = df.iloc[0].isnull().sum()
    second_row_nulls = df.iloc[1].isnull().sum()
    return first_row_nulls > second_row_nulls

with open(output_md, 'w', encoding='utf-8') as f:
    f.write('# Dataset Profile\n\n')
    files = [f for f in os.listdir(raw_dir) if f.endswith('.xlsx')]
    for file_name in files:
        file_path = os.path.join(raw_dir, file_name)
        f.write(f'## {file_name}\n\n')
        try:
            xl = pd.ExcelFile(file_path)
        except Exception as e:
            f.write(f'*Error reading file: {e}*\n\n')
            continue
        sheet_names = xl.sheet_names
        f.write(f'**Sheets:** {", ".join(sheet_names)}\n\n')
        # Store dataframes for FK inference
        sheets_data = {}
        for sheet in sheet_names:
            df_raw = xl.parse(sheet, header=None)  # no header
            # Determine header row: if first row looks like title, header is row 1 else 0
            header_row = 0
            if detect_title_row(df_raw):
                header_row = 1
            # Load with proper header
            df = xl.parse(sheet, header=header_row)
            # Clean column names: strip whitespace
            df.columns = [str(col).strip() for col in df.columns]
            sheets_data[sheet] = df
            f.write(f'### Sheet: {sheet}\n')
            f.write(f'- **Rows:** {df.shape[0]}\n')
            f.write(f'- **Columns:** {df.shape[1]}\n')
            f.write(f'- **Column Names:** {", ".join([str(c) for c in df.columns])}\n')
            # Primary key
            pk = infer_primary_key(df)
            f.write(f'- **Inferred Primary Key:** {pk if pk else "Not detected"}\n')
            # Missing values
            missing = df.isnull().sum()
            missing_cols = missing[missing > 0]
            if not missing_cols.empty:
                f.write(f'- **Missing Values:**\n')
                for col, cnt in missing_cols.items():
                    f.write(f'  - {col}: {cnt} missing ({cnt/len(df)*100:.1f}%)\n')
            else:
                f.write(f'- **Missing Values:** None\n')
            # Duplicate rows
            dup_count = df.duplicated().sum()
            f.write(f'- **Duplicate Rows:** {dup_count} ({dup_count/len(df)*100:.1f}%)\n')
            # Data types
            f.write(f'- **Column Data Types:**\n')
            for col, dtype in df.dtypes.items():
                f.write(f'  - {col}: {dtype}\n')
            # Title row
            title_row = detect_title_row(df_raw)
            f.write(f'- **First Row Appears as Title:** {title_row}\n')
            if title_row:
                f.write(f'  - Recommendation: Consider using second row as header; current first row may be descriptive text.\n')
            # Cleaning recommendations
            recs = []
            if not missing_cols.empty:
                recs.append('Handle missing values (imputation/removal).')
            if dup_count > 0:
                recs.append('Remove duplicate rows.')
            # Check for obvious data type issues: object columns that could be numeric/dates
            for col, dtype in df.dtypes.items():
                if dtype == 'object':
                    # Try to convert to numeric
                    try:
                        pd.to_numeric(df[col].dropna())
                        recs.append(f'Column "{col}" appears numeric but stored as object; consider converting.')
                    except:
                        pass
                    # Try to convert to datetime (if column name suggests date)
                    if 'date' in col.lower() or 'year' in col.lower():
                        try:
                            pd.to_datetime(df[col].dropna())
                            recs.append(f'Column "{col}" appears to be date but stored as object; consider converting to datetime.')
                        except:
                            pass
            if recs:
                f.write(f'- **Cleaning Recommendations:**\n')
                for r in recs:
                    f.write(f'  - {r}\n')
            else:
                f.write(f'- **Cleaning Recommendations:** None apparent.\n')
            f.write('\n')
        # Foreign keys across sheets
        f.write('#### Potential Foreign Key Relationships (across sheets)\n')
        found_fks = False
        for sheet_name, df in sheets_data.items():
            for col in df.columns:
                if col.endswith('_id') or col == 'company_id':
                    for other_sheet, other_df in sheets_data.items():
                        if other_sheet == sheet_name:
                            continue
                        if col in other_df.columns:
                            if other_df[col].notnull().all() and other_df[col].nunique() == len(other_df):
                                f.write(f'- Sheet **{sheet_name}**.{col} may reference Sheet **{other_sheet}**.{col}\n')
                                found_fks = True
        if not found_fks:
            f.write('No obvious foreign key relationships detected based on column name matching and uniqueness.\n')
        f.write('\n---\n\n')
print(f'Profile written to {output_md}')
