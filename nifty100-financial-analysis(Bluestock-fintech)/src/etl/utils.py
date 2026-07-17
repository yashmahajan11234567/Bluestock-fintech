"""
Utility functions for the ETL pipeline.
Provides helper functions for detecting headers in Excel files and normalizing dataframes.
"""

import pandas as pd
import numpy as np
from typing import Union


def detect_header_row(df: pd.DataFrame) -> int:
    """
    Detect the row number that contains column headers in an Excel sheet.

    Looks for the row that contains common identifier columns like 'id'
    or follows a title row pattern commonly found in financial reports.

    Args:
        df: DataFrame read from Excel with header=None (all data as strings/objects)

    Returns:
        int: The row index that should be used as headers

    Example:
        For Excel files with format:
        Row 0: "Report Title | Company Data | 2023"
        Row 1: "id", "company_name", "sales", "profit", ...
        Row 2+: actual data rows

        Returns: 1
    """
    if df.empty:
        return 0

    # Common indicators that a row contains headers
    header_indicators = [
        'id', 'ID', 'Id',  # Primary key column
        'company_id', 'company_id',  # Foreign key
        'year', 'Year', 'YEAR',  # Time period
        'date', 'Date', 'DATE',  # Date column
        'name', 'Name', 'NAME',  # Name column
        'value', 'Value', 'VALUE',  # Value column
        'amount', 'Amount', 'AMOUNT',  # Amount column
        'sales', 'Sales', 'SALES',  # Common financial columns
        'profit', 'Profit', 'PROFIT',
        'revenue', 'Revenue', 'REVENUE',
        'expenses', 'Expenses', 'EXPENSES',
        'assets', 'Assets', 'ASSETS',
        'liabilities', 'Liabilities', 'LIABILITIES',
        'equity', 'Equity', 'EQUITY'
    ]

    # Check each row to see how many header indicators it contains
    best_row = 0
    max_matches = 0

    # Don't check too many rows - usually header is in first few rows
    max_rows_to_check = min(10, len(df))

    for row_idx in range(max_rows_to_check):
        row_values = []
        for val in df.iloc[row_idx]:
            if isinstance(val, str):
                row_values.append(val.strip())
            else:
                # Convert non-strings to string for checking
                row_values.append(str(val).strip() if pd.notna(val) else "")

        # Count how many header indicators are in this row (case-insensitive)
        matches = 0
        for indicator in header_indicators:
            # Check if any cell in the row contains this indicator (case-insensitive)
            if any(indicator.lower() in str(val).lower() for val in row_values if val):
                matches += 1

        # Also check for exact matches (stronger signal)
        exact_matches = sum(1 for val in row_values if val in header_indicators)
        matches += exact_matches  # Bonus for exact matches

        if matches > max_matches:
            max_matches = matches
            best_row = row_idx

    # If we found very few matches, default to row 0 (no header row detected)
    # But if we found multiple matches, we likely found the header
    if max_matches < 2:
        # Fallback: look for a row that looks like headers (more strings than numbers, reasonable length)
        for row_idx in range(min(5, len(df))):
            row = df.iloc[row_idx]
            str_count = sum(1 for val in row if isinstance(val, str) and str(val).strip())
            total_count = len([val for val in row if pd.notna(val)])
            if total_count > 0 and str_count / total_count > 0.5:  # Mostly strings
                # Also check that it looks like column names (no long sentences)
                avg_len = sum(len(str(val).strip()) for val in row if isinstance(val, str) and str(val).strip()) / max(str_count, 1)
                if avg_len < 50:  # Reasonable column name length
                    return row_idx
        return 0

    return best_row


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a DataFrame by cleaning string values and handling missing data.

    Operations performed:
    1. Strip whitespace from string values
    2. Convert empty strings to None (for NULL in SQLite)
    3. Convert string 'None'/'nan'/'NaN' to actual None/NaN
    4. Ensure consistent handling of missing data

    Args:
        df: DataFrame to normalize

    Returns:
        pd.DataFrame: Normalized DataFrame
    """
    if df.empty:
        return df

    # Create a copy to avoid modifying the original
    df_norm = df.copy()

    # Process each column
    for col in df_norm.columns:
        if df_norm[col].dtype == 'object':
            # Strip whitespace from string values
            df_norm[col] = df_norm[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )

            # Convert various forms of empty/missing values to None
            # Empty strings
            df_norm[col] = df_norm[col].replace('', None)
            # String versions of null/nan
            df_norm[col] = df_norm[col].replace(['None', 'none', 'NONE', 'null', 'NULL'], None)
            df_norm[col] = df_norm[col].replace(['nan', 'NaN', 'NAN'], None)

    return df_norm