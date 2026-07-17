import pytest
import sqlite3
import pandas as pd
from pathlib import Path

@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database with the schema from schema.sql."""
    conn = sqlite3.connect(':memory:')
    # Read the schema file
    schema_path = Path(__file__).parents[2] / 'db' / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema = f.read()
    # Execute the schema
    conn.executescript(schema)
    yield conn
    conn.close()

@pytest.fixture
def sample_dataframe():
    """Return a simple pandas DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [10.5, 20.0, 30.0]
    })