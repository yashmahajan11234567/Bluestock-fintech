import sys
import os
import csv
import tempfile
sys.path.insert(0, 'nifty100-financial-analysis(Bluestock-fintech)/src')

from screener.engine import run_screener, get_quality_compounder_filters

def check_ac09():
    print("Running screener for Quality Compounder preset...")
    filters = get_quality_compounder_filters()
    results = run_screener(filters=filters)

    if results is None or results.empty:
        print("FAIL: No results from screener")
        return False

    # Create a temporary CSV file
    temp_dir = tempfile.gettempdir()
    csv_path = os.path.join(temp_dir, 'screener_output.csv')
    print(f"Writing CSV to {csv_path}")

    # Write to CSV
    results.to_csv(csv_path, index=False)

    # Check file exists
    if not os.path.exists(csv_path):
        print("FAIL: CSV file was not created")
        return False

    # Check file size
    size = os.path.getsize(csv_path)
    print(f"CSV file size: {size} bytes")
    if size == 0:
        print("FAIL: CSV file is empty")
        return False

    # Try to read as CSV and check header and rows
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
    except Exception as e:
        print(f"FAIL: Could not parse CSV: {e}")
        return False

    if len(rows) < 1:
        print("FAIL: CSV has no rows")
        return False

    header = rows[0]
    print(f"Header: {header}")
    if len(header) == 0:
        print("FAIL: Header is empty")
        return False

    data_rows = rows[1:]
    print(f"Number of data rows: {len(data_rows)}")

    # Check for empty rows or malformed columns
    for i, row in enumerate(data_rows):
        if len(row) != len(header):
            print(f"FAIL: Row {i+2} has {len(row)} columns, expected {len(header)}")
            return False
        # Check for completely empty row
        if all(field.strip() == '' for field in row):
            print(f"FAIL: Row {i+2} is completely empty")
            return False

    # If we got here, all checks passed
    print("AC-09: PASS")
    return True

if __name__ == "__main__":
    try:
        success = check_ac09()
        # Clean up the temp file
        temp_dir = tempfile.gettempdir()
        csv_path = os.path.join(temp_dir, 'screener_output.csv')
        if os.path.exists(csv_path):
            os.remove(csv_path)
            print(f"Removed temporary file: {csv_path}")
    except Exception as e:
        print(f"Error during AC-09 check: {e}")
        success = False

    sys.exit(0 if success else 1)