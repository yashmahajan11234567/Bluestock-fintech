"""
Tests for loader.py — ETL loading functions.
"""

import pytest
import pandas as pd
import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parents[2] / 'src'))

from etl.loader import _get_table_file_mapping, _get_table_columns, _load_table, LOAD_ORDER


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database with the schema from schema.sql."""
    conn = sqlite3.connect(':memory:')
    conn.execute("PRAGMA foreign_keys = ON;")
    schema_path = Path(__file__).parents[2] / 'db' / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    for statement in schema_sql.split(';'):
        statement = statement.strip()
        if statement:
            try:
                conn.execute(statement)
            except sqlite3.Error:
                pass
    conn.commit()
    yield conn
    conn.close()


# --- _get_table_file_mapping ---

def test_get_table_file_mapping():
    """Mapping covers all load-order tables and uses correct filenames."""
    mapping = _get_table_file_mapping()
    assert isinstance(mapping, dict)
    assert set(mapping.keys()) == set(LOAD_ORDER)
    for table, filename in mapping.items():
        assert filename == f"{table}.xlsx"


# --- _get_table_columns ---

def test_get_table_columns_returns_columns_for_known_table(in_memory_db):
    """Known table returns its column list."""
    cols = _get_table_columns(in_memory_db, 'companies')
    assert 'id' in cols
    assert 'company_name' in cols
    assert 'website' in cols


def test_get_table_columns_returns_empty_for_unknown_table(in_memory_db):
    """Unknown table returns empty list without crashing."""
    cols = _get_table_columns(in_memory_db, 'nonexistent_table')
    assert cols == []


# --- _load_table — without FK validation ---

def test_load_table_basic_insert_no_fk(in_memory_db):
    """Insert into companies table without FK validation."""
    df = pd.DataFrame({
        'id': ['AAPL', 'MSFT'],
        'company_name': ['Apple Inc', 'Microsoft Corp'],
        'extra_col': ['x', 'y'],  # should be dropped
    })
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='companies',
        df=df, valid_company_ids=None, output_dir=Path('.')
    )
    assert rows == 2
    assert status == 'SUCCESS'

    cursor = in_memory_db.cursor()
    cursor.execute("SELECT id, company_name FROM companies WHERE id IN ('AAPL', 'MSFT')")
    assert len(cursor.fetchall()) == 2


def test_load_table_extra_columns_are_dropped(in_memory_db):
    """Extra columns in DataFrame not present in the table are dropped."""
    df = pd.DataFrame({
        'id': ['DROP'],
        'company_name': ['Drop Test'],
        'ghost_col': ['should vanish'],
    })
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='companies',
        df=df, valid_company_ids=None, output_dir=Path('.')
    )
    assert rows == 1
    assert status == 'SUCCESS'

    cursor = in_memory_db.cursor()
    cursor.execute("PRAGMA table_info(companies)")
    db_cols = {row[1] for row in cursor.fetchall()}
    assert 'ghost_col' not in db_cols


def test_load_table_missing_nullable_columns_default_to_null(in_memory_db):
    """Columns omitted from DataFrame that exist in table become NULL."""
    df = pd.DataFrame({
        'id': ['NULL1'],
        'company_name': ['Null Co'],
    })
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='companies',
        df=df, valid_company_ids=None, output_dir=Path('.')
    )
    assert rows == 1
    assert status == 'SUCCESS'

    cursor = in_memory_db.cursor()
    cursor.execute("SELECT id, company_name, company_logo, website FROM companies WHERE id='NULL1'")
    row = cursor.fetchone()
    assert row[2] is None
    assert row[3] is None


def test_load_table_empty_dataframe(in_memory_db):
    """Empty DataFrame results in EMPTY_AFTER_FILTER status."""
    df = pd.DataFrame({'id': pd.Series(dtype='object'), 'company_name': pd.Series(dtype='object')})
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='companies',
        df=df, valid_company_ids=None, output_dir=Path('.')
    )
    assert rows == 0
    assert status == 'EMPTY_AFTER_FILTER'


def test_load_table_insert_error_handled(in_memory_db):
    """Duplicate PK insert is caught and reported as INSERT_ERROR."""
    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO companies (id, company_name) VALUES ('DUP', 'Original')")
    in_memory_db.commit()

    df = pd.DataFrame({'id': ['DUP'], 'company_name': ['Duplicate']})
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='companies',
        df=df, valid_company_ids=None, output_dir=Path('.')
    )
    assert rows == 0
    assert 'INSERT_ERROR' in status


# --- _load_table — with FK validation ---

def test_load_table_fk_all_valid(in_memory_db):
    """All rows pass FK validation — all inserted."""
    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO companies (id, company_name) VALUES ('ABC', 'ABC Corp')")
    in_memory_db.commit()

    df = pd.DataFrame({
        'company_id': ['ABC', 'ABC'],
        'broad_sector': ['Technology', 'Finance'],
    })
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='sectors',
        df=df, valid_company_ids={'ABC'}, output_dir=Path('.')
    )
    assert rows == 2
    assert status == 'SUCCESS'


def test_load_table_fk_some_invalid(in_memory_db):
    """Rows with invalid company_id are rejected; valid ones are inserted."""
    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO companies (id, company_name) VALUES ('VAL1', 'Valid Co')")
    in_memory_db.commit()

    df = pd.DataFrame({
        'company_id': ['VAL1', 'MISSING'],
        'broad_sector': ['Tech', 'Finance'],
    })
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='sectors',
        df=df, valid_company_ids={'VAL1'}, output_dir=Path('.')
    )
    assert rows == 1
    assert status == 'PARTIAL_REJECT'

    cursor.execute("SELECT company_id FROM sectors")
    assert cursor.fetchall() == [('VAL1',)]


def test_load_table_fk_all_invalid(in_memory_db):
    """All rows have invalid company_id — none are inserted."""
    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO companies (id, company_name) VALUES ('OK', 'OK Co')")
    in_memory_db.commit()

    df = pd.DataFrame({
        'company_id': ['BAD1', 'BAD2'],
        'broad_sector': ['Tech', 'Finance'],
    })
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='sectors',
        df=df, valid_company_ids={'OK'}, output_dir=Path('.')
    )
    assert rows == 0
    assert status == 'PARTIAL_REJECT'


def test_load_table_fk_no_company_id_column(in_memory_db):
    """When FK validation is enabled but table lacks company_id, all rows pass through."""
    cursor = in_memory_db.cursor()
    cursor.execute("INSERT INTO companies (id, company_name) VALUES ('X', 'X Corp')")
    in_memory_db.commit()

    df = pd.DataFrame({
        'id': ['NEWCO'],
        'company_name': ['New Company'],
    })
    rows, elapsed, status = _load_table(
        conn=in_memory_db, table_name='companies',
        df=df, valid_company_ids={'X'},
        output_dir=Path('.')
    )
    assert rows == 1
    assert status == 'SUCCESS'