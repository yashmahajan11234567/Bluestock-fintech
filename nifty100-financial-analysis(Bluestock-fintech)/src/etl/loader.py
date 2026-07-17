"""
Main ETL loader script.
"""

import csv
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd

from . import utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define load order (dependencies first)
LOAD_ORDER = [
    'companies',
    'sectors',
    'peer_groups',
    'documents',
    'prosandcons',
    'analysis',
    'financial_ratios',
    'market_cap',
    'profitandloss',
    'balancesheet',
    'cashflow',
    'stock_prices'
]

def _get_table_file_mapping() -> Dict[str, str]:
    """
    Map table names to their corresponding Excel file names.
    Assumes file name matches table name (lowercase) with .xlsx extension.
    """

    return {table: f"{table}.xlsx" for table in LOAD_ORDER}

def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> list:
    """
    Get the list of column names for a table in the database.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]  # column name is in index 1
        return columns
    except Exception:
        # If we can't get the table info, return empty list to avoid filtering
        return []
def _load_table(
    conn: sqlite3.Connection,
    table_name: str,
    df: pd.DataFrame,
    valid_company_ids: set | None,
    output_dir: Path,
) -> tuple[int, int, str]:
    """
    Insert a DataFrame into a SQLite table.
    Returns (rows_loaded, rows_rejected, status_message).

    If valid_company_ids is provided (i.e., this is a fact/dimension table with a FK),
    rows with company_id not in the set are rejected and logged to validation_failures.csv.
    """
    start_time = time.time()
    rows_total = len(df)
    rows_loaded = 0
    rows_rejected = 0
    status = "SUCCESS"

    # Ensure target table exists (should have been created by schema.sql)
    # We'll just try to insert; if table missing, SQL error will be caught.

    # Validate foreign key if applicable
    if valid_company_ids is not None and 'company_id' in df.columns:
        # Identify invalid rows
        # Ensure company_id is string for comparison
        df['company_id'] = df['company_id'].astype(str).str.strip()
        invalid_mask = ~df['company_id'].isin(valid_company_ids)
        invalid_df = df[invalid_mask].copy()
        valid_df = df[~invalid_mask].copy()

        if not invalid_df.empty:
            # Write to validation_failures.csv
            invalid_df = invalid_df.copy()
            invalid_df['table_name'] = table_name
            invalid_df['rejection_reason'] = 'FK_VIOLATION'
            fail_path = output_dir / "validation_failures.csv"
            file_exists = fail_path.is_file()
            invalid_df.to_csv(fail_path, mode='a', header=not file_exists, index=False)
            rows_rejected = len(invalid_df)
            rows_loaded = len(valid_df)
            df_to_insert = valid_df
            status = "PARTIAL_REJECT"
        else:
            rows_loaded = rows_total
            df_to_insert = df
    else:
        # No FK validation needed (e.g., companies table)
        df_to_insert = df
        rows_loaded = rows_total


    # Filter DataFrame to only include columns that exist in the database table
    db_columns = _get_table_columns(conn, table_name)
    if db_columns:  # Only filter if we successfully got the column list
        # Keep only columns that exist in the database
        cols_to_keep = [col for col in df_to_insert.columns if col in db_columns]
        if len(cols_to_keep) < len(df_to_insert.columns):
            dropped_cols = [col for col in df_to_insert.columns if col not in db_columns]
            logger.info(f"Dropping columns not in database table {table_name}: {dropped_cols}")
        df_to_insert = df_to_insert[cols_to_keep]
    else:
        # If we couldn't get database columns, proceed with all columns (original behavior)
        pass
    # Insert into SQLite with chunking to avoid SQLite variable limit
    if not df_to_insert.empty:
        try:
            # Use pandas to_sql with method='multi' and chunksize
            df_to_insert.to_sql(
                name=table_name,
                con=conn,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=500
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            # Log detailed exception info for debugging
            logger.exception(f"Exception during insert for table {table_name}: {type(e).__name__}: {e}")
            status = f"INSERT_ERROR: {e}"
            # All rows considered failed for audit? We'll treat as zero loaded.
            rows_loaded = 0
            rows_rejected = rows_total
    else:
        # Nothing to insert (all rows rejected)
        if status == "SUCCESS":
            status = "EMPTY_AFTER_FILTER"

    elapsed = time.time() - start_time
    return rows_loaded, round(elapsed, 3), status

def run_etl():
    """
    Execute the full ETL pipeline.
    """
    base_path = Path(__file__).resolve().parents[2]  # project root
    raw_dir = base_path / "data" / "raw"
    output_dir = base_path / "data" / "output"
    db_path = base_path / "db" / "commerce.db"  # but we need to match schema location? Actually db/schema.sql creates tables; we will create db file here.

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Database file (SQLite)
    sqlite_db_path = base_path / "db" / "nifty100.db"
    sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)

    # Load schema to create tables
    schema_path = base_path / "db" / "schema.sql"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Connect to SQLite
    conn = sqlite3.connect(str(sqlite_db_path))
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    # Apply schema
    with open(schema_path, 'r', encoding='utf-8', errors='ignore') as f:
        sql_script = f.read()
    # Execute each statement (split by ;)
    for statement in sql_script.split(';'):
        stmt = statement.strip()
        if stmt:
            try:
                conn.execute(stmt)
            except Exception as e:
                # Some statements may fail (e.g., CREATE IF NOT EXISTS already exists) – ignore
                logger.debug("Schema statement skip %s: %s", stmt[:50], e)
    conn.commit()
    logger.info("Database initialized with schema from %s", schema_path)

    # Get mapping of table to file
    table_file_map = _get_table_file_mapping()

    # We'll need company IDs after loading companies
    company_ids_set: set | None = None

    # Prepare audit rows
    audit_rows: list[dict] = []
    audit_path = output_dir / "load_audit.csv"
    # Write header
    with open(audit_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'table_name', 'rows_loaded', 'rows_rejected', 'execution_time', 'status'
        ])
        writer.writeheader()

    # Process tables in load order
    for table_name in LOAD_ORDER:
        file_name = table_file_map[table_name]
        excel_path = raw_dir / file_name
        if not excel_path.is_file():
            logger.warning("File not found for table %s: %s", table_name, excel_path)
            audit_rows.append({
                'table_name': table_name,
                'rows_loaded': 0,
                'rows_rejected': 0,
                'execution_time': 0.0,
                'status': f'MISSING_FILE: {file_name}'
            })
            continue

        logger.info("Processing %s (%s)", table_name, file_name)
        try:
            # Detect header row
            raw_df = pd.read_excel(excel_path, header=None)
            header_row = utils.detect_header_row(raw_df)
            df = pd.read_excel(excel_path, header=header_row)
            # Normalize column names
            df.columns = [str(c).strip() for c in df.columns]
            # Normalize data
            df = utils.normalize_dataframe(df)

            # Determine if we need FK validation
            needs_fk = table_name != 'companies' and 'company_id' in df.columns
            valid_ids = company_ids_set if needs_fk else None

            rows_loaded, elapsed, status = _load_table(
                conn=conn,
                table_name=table_name,
                df=df,
                valid_company_ids=valid_ids,
                output_dir=output_dir
            )

            # If this is the companies table, refresh the set of valid IDs
            if table_name == 'companies' and status == 'SUCCESS':
                # Reload companies to get latest IDs (including any that might have been inserted)
                # But we haven't inserted any yet; we just loaded df.
                # Extract IDs from df (should be the same as what we just loaded)
                if 'id' in df.columns:
                    company_ids_set = set(df['id'].dropna().astype(str).str.strip())
                else:
                    company_ids_set = set()
                logger.info("Loaded %d company IDs for FK validation", len(company_ids_set))

            audit_rows.append({
                'table_name': table_name,
                'rows_loaded': rows_loaded,
                'rows_rejected': 0 if status == 'SUCCESS' else (len(df) - rows_loaded),
                'execution_time': elapsed,
                'status': status
            })
            logger.info(
                "Loaded %s: %d rows loaded, %d rejected, %.3fs, status=%s",
                table_name, rows_loaded, (len(df) - rows_loaded) if status != 'SUCCESS' else 0, elapsed, status
            )
        except Exception as exc:
            logger.exception("Failed processing %s", table_name)
            audit_rows.append({
                'table_name': table_name,
                'rows_loaded': 0,
                'rows_rejected': 0,
                'execution_time': 0.0,
                'status': f'ERROR: {exc}'
            })

    # Write audit CSV (append mode)
    with open(audit_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'table_name', 'rows_loaded', 'rows_rejected', 'execution_time', 'status'
        ])
        for row in audit_rows:
            writer.writerow(row)

    # Close connection
    conn.close()
    logger.info("ETL completed. Audit written to %s", audit_path)

if __name__ == "__main__":
    run_etl()