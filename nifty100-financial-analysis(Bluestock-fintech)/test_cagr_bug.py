#!/usr/bin/env python3
"""
Test script to demonstrate the CAGR bug and verify the fix
"""

import sys
import os
sys.path.append('src')

def test_current_implementation():
    """Test the current (buggy) implementation"""
    print("=== Testing Current Implementation ===")

    # Simulate what the current code does
    import pandas as pd

    # Load data
    base_path = os.path.join('src', 'screener', '..', '..', 'Data', 'raw')
    profitandloss = pd.read_excel(os.path.join(base_path, 'profitandloss.xlsx'), header=1)
    if 'id' in profitandloss.columns:
        profitandloss = profitandloss.drop(columns=['id'])

    print(f"Original profitandloss shape: {profitandloss.shape}")
    print(f"Original unique companies: {profitandloss['company_id'].nunique()}")

    # Show TCS data as example
    tcs_original = profitandloss[profitandloss['company_id'] == 'TCS']
    print(f"TCS original rows: {len(tcs_original)}")
    if len(tcs_original) > 0:
        print(f"TCS original years: {sorted(tcs_original['year'].unique())}")

    # Current implementation: modify profitandloss first (lines 41-47)
    if 'year' in profitandloss.columns:
        def _parse_year_to_int(y):
            if isinstance(y, str):
                import re
                m = re.search(r'\b(\d{4})\b', y)
                return int(m.group(1)) if m else 0
            elif isinstance(y, (int, float,)):
                return int(y)
            return 0
        profitandloss['_year_int'] = profitandloss['year'].apply(_parse_year_to_int)
        profitandloss = profitandloss.sort_values(['company_id', '_year_int'], ascending=[True, False])
        profitandloss = profitandloss.drop_duplicates(subset=['company_id'], keep='first')  # BUG: This keeps earliest year!
        profitandloss = profitandloss.drop(columns=['_year_int'])

    print(f"\nAfter modification for latest year tracking:")
    print(f"Modified profitandloss shape: {profitandloss.shape}")
    print(f"Modified unique companies: {profitandloss['company_id'].nunique()}")

    # Current implementation: make pl_full copy AFTER modification (line 50) - THIS IS THE BUG
    pl_full = profitandloss.copy()
    print(f"\npl_full shape (copied AFTER modification): {pl_full.shape}")
    print(f"pl_full unique companies: {pl_full['company_id'].nunique()}")

    # Show TCS in pl_full
    tcs_plfull = pl_full[pl_full['company_id'] == 'TCS']
    print(f"TCS rows in pl_full: {len(tcs_plfull)}")
    if len(tcs_plfull) > 0:
        print(f"TCS year in pl_full: {tcs_plfull['year'].iloc[0] if 'year' in tcs_plfull.columns else 'NO YEAR COLUMN'}")

    # This means we can't calculate CAGR - only 1 year per company!
    print(f"\n=== RESULT: Cannot calculate CAGR (only {pl_full['company_id'].nunique()} years available per company) ===")

    return pl_full

def test_corrected_implementation():
    """Test what the corrected implementation should be"""
    print("\\n=== Testing Corrected Implementation ===")

    # Simulate what the corrected code should do
    import pandas as pd

    # Load data
    base_path = os.path.join('src', 'screener', '..', '..', 'Data', 'raw')
    profitandloss = pd.read_excel(os.path.join(base_path, 'profitandloss.xlsx'), header=1)
    if 'id' in profitandloss.columns:
        profitandloss = profitandloss.drop(columns=['id'])

    print(f"Original profitandloss shape: {profitandloss.shape}")
    print(f"Original unique companies: {profitandloss['company_id'].nunique()}")

    # CORRECTED: Make pl_full copy FIRST (before modifying profitandloss)
    pl_full = profitandloss.copy()
    print(f"\\npl_full shape (copied BEFORE modification): {pl_full.shape}")
    print(f"pl_full unique companies: {pl_full['company_id'].nunique()}")

    # Show TCS data in pl_full
    tcs_plfull = pl_full[pl_full['company_id'] == 'TCS']
    print(f"TCS rows in pl_full: {len(tcs_plfull)}")
    if len(tcs_plfull) > 0:
        print(f"TCS years in pl_full: {sorted(tcs_plfull['year'].unique())}")

    # NOW modify profitandloss for latest year tracking
    if 'year' in profitandloss.columns:
        def _parse_year_to_int(y):
            if isinstance(y, str):
                import re
                m = re.search(r'\b(\d{4})\b', y)
                return int(m.group(1)) if m else 0
            elif isinstance(y, (int, float,)):
                return int(y)
            return 0
        profitandloss['_year_int'] = profitandloss['year'].apply(_parse_year_to_int)
        profitandloss = profitandloss.sort_values(['company_id', '_year_int'], ascending=[True, False])
        profitandloss = profitandloss.drop_duplicates(subset=['company_id'], keep='first')  # Keep earliest after sorting ascending
        profitandloss = profitandloss.drop(columns=['_year_int'])

    print(f"\\nAfter modification for latest year tracking:")
    print(f"Modified profitandloss shape: {profitandloss.shape}")
    print(f"Modified unique companies: {profitandloss['company_id'].nunique()}")

    # Show TCS in modified profitandloss (latest year only)
    tcs_modified = profitandloss[profitandloss['company_id'] == 'TCS']
    print(f"TCS rows in modified profitandloss: {len(tcs_modified)}")
    if len(tcs_modified) > 0:
        print(f"TCS year in modified profitandloss: {tcs_modified['year'].iloc[0] if 'year' in tcs_modified.columns else 'NO YEAR COLUMN'}")

    # Now we CAN calculate CAGR because pl_full has all years
    print(f"\\n=== RESULT: Can calculate CAGR (have {pl_full['company_id'].nunique()} years available per company) ===")

    return pl_full

if __name__ == "__main__":
    current_result = test_current_implementation()
    corrected_result = test_corrected_implementation()

    print("\\n" + "="*60)
    print("SUMMARY:")
    print(f"Current implementation years per company: {current_result['company_id'].nunique() if len(current_result) > 0 else 0}")
    print(f"Corrected implementation years per company: {corrected_result['company_id'].nunique() if len(corrected_result) > 0 else 0}")
    print("="*60)