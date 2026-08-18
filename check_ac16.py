import pandas as pd

def check_ac16():
    df = pd.read_csv('nifty100-financial-analysis(Bluestock-fintech)/Data/output/pros_cons_generated.csv')
    print(f"Total rows: {len(df)}")
    # Check for TEST company
    if 'TEST' in df['company_id'].values:
        print("FAIL: TEST company found")
        return False
    # Check for duplicates
    if df['company_id'].duplicated().any():
        print("FAIL: Duplicate company IDs found")
        return False
    # Check that each company has at least one pro and one con
    # Assuming columns: company_id, pros, cons (or similar)
    # Let's see the columns
    print(f"Columns: {list(df.columns)}")
    # We need to adjust based on actual column names
    # From previous runs, the file might have columns: company_id, pros, cons
    # But let's check the file first by reading a few rows
    print("\nFirst few rows:")
    print(df.head())
    # Now, let's check the pros and cons columns
    # We'll assume the pros and cons are stored as strings, maybe separated by newlines or semicolons?
    # Looking at the file from earlier, it seems each row has a pros and cons string.
    # We'll check if the pros and cons fields are non-empty.
    # We'll count non-empty strings in pros and cons columns.
    # But we need to know the column names.
    # Let's print the column names and first row values to infer.
    if len(df) > 0:
        print("\nFirst row:")
        for col in df.columns:
            print(f"  {col}: {repr(df.iloc[0][col])}")
    # Now, let's assume the pros column is named 'pros' and cons column is named 'cons'
    # If not, we'll adjust.
    pros_col = None
    cons_col = None
    for col in df.columns:
        if col.lower() == 'pros':
            pros_col = col
        if col.lower() == 'cons':
            cons_col = col
    if pros_col is None or cons_col is None:
        # Try to find columns that contain pros and cons
        for col in df.columns:
            if 'pro' in col.lower():
                pros_col = col
            if 'con' in col.lower():
                cons_col = col
    if pros_col is None or cons_col is None:
        print("FAIL: Could not find pros and cons columns")
        return False
    print(f"\nUsing pros column: {pros_col}")
    print(f"Using cons column: {cons_col}")
    # Check for empty pros or cons
    empty_pros = df[pros_col].isna() | (df[pros_col].astype(str).str.strip() == '')
    empty_cons = df[cons_col].isna() | (df[cons_col].astype(str).str.strip() == '')
    if empty_pros.any():
        print(f"FAIL: {empty_pros.sum()} companies have empty pros")
        return False
    if empty_cons.any():
        print(f"FAIL: {empty_cons.sum()} companies have empty cons")
        return False
    # If we got here, all checks passed
    print(f"AC-16: PASS - {len(df)} companies, each with at least one pro and one con")
    return True

if __name__ == "__main__":
    check_ac16()