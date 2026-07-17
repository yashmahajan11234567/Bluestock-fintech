import pandas as pd
import pytest
from src.etl.utils import detect_header_row, normalize_dataframe

def test_detect_header_row_with_header_in_second_row():
    # Create a DataFrame with a title row and then a header row
    data = [
        ['Report Title', 'Company Data', '2023'],
        ['id', 'name', 'value'],
        [1, 'Alice', 100],
        [2, 'Bob', 200]
    ]
    df = pd.DataFrame(data)
    # The header row is at index 1
    assert detect_header_row(df) == 1

def test_detect_header_row_with_header_in_first_row():
    # No title row, header in first row
    data = [
        ['id', 'name', 'value'],
        [1, 'Alice', 100],
        [2, 'Bob', 200]
    ]
    df = pd.DataFrame(data)
    # The function should return 0 because it finds header indicators in row 0
    assert detect_header_row(df) == 0

def test_detect_header_row_no_header():
    # No header-like row, should default to 0
    data = [
        ['Some random text', 'More text'],
        [1, 2],
        [3, 4]
    ]
    df = pd.DataFrame(data)
    # Expect 0 because no clear header found
    assert detect_header_row(df) == 0

def test_detect_header_row_empty_dataframe():
    df = pd.DataFrame()
    assert detect_header_row(df) == 0

def test_normalize_dataframe_strips_whitespace():
    df = pd.DataFrame({
        'name': ['  Alice  ', 'Bob', '  Charlie  '],
        'value': [1, 2, 3]
    })
    normalized = normalize_dataframe(df)
    assert normalized['name'].tolist() == ['Alice', 'Bob', 'Charlie']

def test_normalize_dataframe_converts_empty_strings_to_none():
    df = pd.DataFrame({
        'name': ['Alice', '', 'Bob'],
        'value': [1, 2, 3]
    })
    normalized = normalize_dataframe(df)
    assert pd.isna(normalized.loc[1, 'name'])
    assert normalized.loc[0, 'name'] == 'Alice'
    assert normalized.loc[2, 'name'] == 'Bob'

def test_normalize_dataframe_converts_string_none_to_none():
    df = pd.DataFrame({
        'name': ['Alice', 'None', 'Bob'],
        'value': [1, 2, 3]
    })
    normalized = normalize_dataframe(df)
    assert pd.isna(normalized.loc[1, 'name'])
    assert normalized.loc[0, 'name'] == 'Alice'
    assert normalized.loc[2, 'name'] == 'Bob'

def test_normalize_dataframe_converts_string_nan_to_none():
    df = pd.DataFrame({
        'name': ['Alice', 'nan', 'Bob'],
        'value': [1, 2, 3]
    })
    normalized = normalize_dataframe(df)
    assert pd.isna(normalized.loc[1, 'name'])
    assert normalized.loc[0, 'name'] == 'Alice'
    assert normalized.loc[2, 'name'] == 'Bob'

def test_normalize_dataframe_preserves_non_string_columns():
    df = pd.DataFrame({
        'name': ['Alice', 'Bob'],
        'value': [1.5, 2.5],
        'flag': [True, False]
    })
    normalized = normalize_dataframe(df)
    # Check that non-object columns are unchanged
    assert normalized['value'].tolist() == [1.5, 2.5]
    assert normalized['flag'].tolist() == [True, False]

def test_normalize_dataframe_empty_dataframe():
    df = pd.DataFrame()
    normalized = normalize_dataframe(df)
    assert normalized.empty

def test_normalize_dataframe_all_nan_column():
    df = pd.DataFrame({
        'name': ['Alice', 'Bob'],
        'empty': [None, None]
    })
    normalized = normalize_dataframe(df)
    assert pd.isna(normalized['empty']).all()


def test_detect_header_row_with_exact_matches():
    """Exact matches get a bonus, making that row win."""
    data = [
        ['Title', 'Info', 'Data'],
        ['id', 'company_name', 'sales'],
        [1, 'ACME', 100],
    ]
    df = pd.DataFrame(data)
    # Row 1 has exact header matches, should be chosen over row 0
    assert detect_header_row(df) == 1


def test_detect_header_row_fallback_long_sentences():
    """Fallback path: rows with long sentences are skipped."""
    data = [
        ['This is a very long sentence that describes the report in detail and goes on forever'],
        ['id', 'name', 'value'],
        [1, 'Alice', 100],
    ]
    df = pd.DataFrame(data)
    assert detect_header_row(df) == 1


def test_detect_header_row_fallback_all_short():
    """Fallback: when all rows look like headers, pick the first."""
    data = [
        ['a', 'b', 'c'],
        ['d', 'e', 'f'],
        [1, 2, 3],
    ]
    df = pd.DataFrame(data)
    # Very few header indicator matches, falls into fallback path.
    # Row 0 has 100% strings with avg len < 50, row 1 same.
    result = detect_header_row(df)
    assert result == 0


def test_normalize_dataframe_string_none_variants():
    """All case variants of 'None' and 'null' are converted."""
    df = pd.DataFrame({
        'A': ['None', 'none', 'NONE', 'null', 'NULL', 'valid']
    })
    result = normalize_dataframe(df)
    assert pd.isna(result['A'][0])
    assert pd.isna(result['A'][1])
    assert pd.isna(result['A'][2])
    assert pd.isna(result['A'][3])
    assert pd.isna(result['A'][4])
    assert result['A'][5] == 'valid'


def test_normalize_dataframe_string_nan_variants():
    """All case variants of 'nan' are converted."""
    df = pd.DataFrame({
        'A': ['nan', 'NaN', 'NAN', 'valid']
    })
    result = normalize_dataframe(df)
    assert pd.isna(result['A'][0])
    assert pd.isna(result['A'][1])
    assert pd.isna(result['A'][2])
    assert result['A'][3] == 'valid'


def test_normalize_dataframe_integer_in_object_column():
    """Integer values in a column remain unchanged by normalize_dataframe."""
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': ['x', 'y', 'z'],
    })
    df['A'] = df['A'].astype(object)
    result = normalize_dataframe(df)
    # Integer values must be preserved — stripping or replacement should not affect them
    assert result['A'].tolist() == [1, 2, 3]
    # String column should have been stripped
    assert result['B'].tolist() == ['x', 'y', 'z']


def test_normalize_dataframe_preserves_original():
    """Verify the original DataFrame is not mutated."""
    df = pd.DataFrame({
        'name': ['  Alice  ', 'Bob', 'None']
    })
    original_copy = df.copy()
    _ = normalize_dataframe(df)
    pd.testing.assert_frame_equal(df, original_copy)