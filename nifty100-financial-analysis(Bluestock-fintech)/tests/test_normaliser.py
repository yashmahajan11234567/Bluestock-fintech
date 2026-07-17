"""
Tests for the normaliser module.
The normaliser re-exports normalize_dataframe from utils.
"""

import pandas as pd
from src.etl.normaliser import normalize_dataframe


def test_strip_whitespace():
    """Whitespace around string values is stripped."""
    df = pd.DataFrame({'A': ['  foo  ', ' bar ', 'baz']})
    result = normalize_dataframe(df)
    assert result['A'].tolist() == ['foo', 'bar', 'baz']


def test_whitespace_only_becomes_none():
    """Cells containing only whitespace become None (stripped to '' then replaced)."""
    df = pd.DataFrame({'A': ['   ', '\t', '  foo  ']})
    result = normalize_dataframe(df)
    assert pd.isna(result['A'][0])
    assert pd.isna(result['A'][1])
    assert result['A'][2] == 'foo'


def test_empty_string_to_none():
    """Empty strings are converted to None."""
    df = pd.DataFrame({'A': ['', 'foo', '']})
    result = normalize_dataframe(df)
    assert pd.isna(result['A'][0])
    assert result['A'][1] == 'foo'
    assert pd.isna(result['A'][2])


def test_string_none_variants_to_nan():
    """Case variants of 'None' are converted to None."""
    df = pd.DataFrame({'A': ['None', 'foo', 'none', 'NONE', 'bar']})
    result = normalize_dataframe(df)
    assert pd.isna(result['A'][0])
    assert result['A'][1] == 'foo'
    assert pd.isna(result['A'][2])
    assert pd.isna(result['A'][3])
    assert result['A'][4] == 'bar'


def test_string_null_variants_to_nan():
    """Case variants of 'null' are converted to None."""
    df = pd.DataFrame({'A': ['null', 'foo', 'NULL', 'bar']})
    result = normalize_dataframe(df)
    assert pd.isna(result['A'][0])
    assert result['A'][1] == 'foo'
    assert pd.isna(result['A'][2])
    assert result['A'][3] == 'bar'


def test_string_nan_variants_to_nan():
    """Case variants of 'nan' are converted to None."""
    df = pd.DataFrame({'A': ['nan', 'NaN', 'NAN', 'foo']})
    result = normalize_dataframe(df)
    assert pd.isna(result['A'][0])
    assert pd.isna(result['A'][1])
    assert pd.isna(result['A'][2])
    assert result['A'][3] == 'foo'


def test_non_string_columns_unchanged():
    """Numeric and boolean columns are not modified."""
    df = pd.DataFrame({
        'name': ['Alice', 'Bob'],
        'value': [1.5, 2.5],
        'flag': [True, False],
    })
    result = normalize_dataframe(df)
    assert result['value'].tolist() == [1.5, 2.5]
    assert result['flag'].tolist() == [True, False]


def test_empty_dataframe():
    """Empty DataFrame returns empty without error."""
    df = pd.DataFrame()
    result = normalize_dataframe(df)
    assert result.empty


def test_mixed_column_types_preserved():
    """Object columns remain object dtype after normalization."""
    df = pd.DataFrame({
        'A': ['1', '2', 'three'],
        'B': ['a', 'b', 'c'],
    })
    result = normalize_dataframe(df)
    assert result['A'].dtype == 'object'
    assert result['B'].dtype == 'object'


def test_does_not_mutate_original():
    """The original DataFrame is not modified in place."""
    original = pd.DataFrame({'A': ['  foo  ', ' bar ']})
    _ = normalize_dataframe(original)
    assert original['A'].tolist() == ['  foo  ', ' bar ']


def test_mixed_types_in_single_column():
    """A column with strings, numbers, and None values processes correctly."""
    df = pd.DataFrame({
        'A': ['foo', 42, None, 'bar'],
    })
    result = normalize_dataframe(df)
    assert result['A'][0] == 'foo'
    assert result['A'][1] == 42
    assert pd.isna(result['A'][2])
    assert result['A'][3] == 'bar'


def test_normalize_dataframe_reexported():
    """normalize_dataframe is the same function as utils.normalize_dataframe."""
    from src.etl.utils import normalize_dataframe as utils_normalize
    assert normalize_dataframe is utils_normalize