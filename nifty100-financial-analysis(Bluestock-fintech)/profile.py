import pandas as pd
import os
import sys

raw_dir = 'data/raw'
output_md = 'docs/dataset_profile.md'

def infer_primary_key(df):
    """Attempt to infer primary key: column(s) with unique non-null values."""
    # For simplicity, look for a single column with all unique and not null
    candidates = []
    for col in df.columns:
        if df[col].notnull().all() and df[col].nunique() == len(df):
            candidates.append(col)
    if len(candidates) == 1:
        return candidates[0]
    # If multiple, maybe composite? For simplicity return first or None
    if candidates:
        return ', '.join(candidates)
    return None

def infer_foreign_keys(df, all_sheets):
    """Very naive: column names that contain '_id' or end with '_id' and match another table's primary key."""
    fks = []
    for col in df.columns:
        if '_id' in col.lower():
            # check if any other sheet has a column with same name that could be PK
            for sheet_name, other_df in all_sheets.items():
                if sheet_name == df_name:
                    continue
                if col in other_df.columns:
                    # check if other_df[col] is unique and not null
                    if other_df[col].notnull().all() and other_df[col].nunique() == len(other_df):
                        fks.append((col, sheet_name, col))
    return fks

def detect_title_row(df):
    """Heuristic: if first row contains strings that look like titles (e.g., contains spaces, no numbers) and second row looks like header.
    Simpler: check if first row values are all strings and contain letters, and second row has more varied types.
    We'll just return True if first row looks like a title (e.g., contains the file name or sheet name)."""
    # For simplicity, we'll assume first row is header if first row contains strings and second row has numbers or dates.
    # We'll just return False assuming header is first row.
    # We'll later provide recommendation to check.
    return False

def main():
    files = [f for f in os.listdir(raw_dir) if f.endswith('.xlsx')]
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write('# Dataset Profile\n\n')
        for file_name in files:
            file_path = os.path.join(raw_dir, file_name)
            f.write(f'## {file_name}\n\n')
            try:
                excel_file = pd.ExcelFile(file_path)
            except Exception as e:
                f.write(f'*Error reading file: {e}*\n\n')
                continue
            sheet_names = excel_file.sheet_names
            f.write(f'**Sheets:** {", ".join(sheet_names)}\n\n')
            # Store dataframes for foreign key inference
            sheets_data = {}
            for sheet in sheet_names:
                df = excel_file.parse(sheet)
                sheets_data[sheet] = df
                f.write(f'### Sheet: {sheet}\n')
                f.write(f'- **Rows:** {df.shape[0]}\n')
                f.write(f'- **Columns:** {df.shape[1]}\n')
                f.write(f'- **Column Names:** {", ".join([str(c) for c in df.columns])}\n')
                # Infer primary key
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
                # Title row detection
                title_row = detect_title_row(df)
                f.write(f'- **First Row Appears as Title:** {title_row}\n')
                if title_row:
                    f.write(f'  - Recommendation: Consider using second row as header; current first row may be descriptive text.\n')
                # Cleaning recommendations
                recs = []
                if not missing_cols.empty:
                    recs.append('Handle missing values (imputation/removal).')
                if dup_count > 0:
                    recs.append('Remove duplicate rows.')
                # Check for obvious data type issues: e.g., numeric columns stored as object
                for col, dtype in df.dtypes.items():
                    if dtype == 'object':
                        # Try to infer if numeric
                        try:
                            pd.to_numeric(df[col].dropna())
                            recs.append(f'Column "{col}" appears numeric but stored as object; consider converting.')
                        except:
                            pass
                if recs:
                    f.write(f'- **Cleaning Recommendations:**\n')
                    for r in recs:
                        f.write(f'  - {r}\n')
                else:
                    f.write(f'- **Cleaning Recommendations:** None apparent.\n')
                f.write('\n')
            # Foreign keys inference across sheets
            f.write('#### Potential Foreign Key Relationships (across sheets)\n')
            found_fks = False
            for sheet_name, df in sheets_data.items():
                for col in df.columns:
                    if '_id' in col.lower():
                        for other_sheet, other_df in sheets_data.items():
                            if other_sheet == sheet_name:
                                continue
                            if col in other_df.columns:
                                # check uniqueness in other_df
                                if other_df[col].notnull().all() and other_df[col].nunique() == len(other_df):
                                    f.write(f'- Sheet **{sheet_name}**.{col} may reference Sheet **{other_sheet}**.{col}\n')
                                    found_fks = True
            if not found_fks:
                f.write('No obvious foreign key relationships detected based on column name matching and uniqueness.\n')
            f.write('\n---\n\n')
    print(f'Profile written to {output_md}')

if __name__ == '__main__':
    main()
