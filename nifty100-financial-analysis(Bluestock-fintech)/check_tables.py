import sqlite3
from pathlib import Path

def check_tables():
    db_path = Path(__file__).parent / "db" / "nifty100.db"
    conn = sqlite3.connect(db_path)

    # Get list of tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables in database:")
    for table in tables:
        print(f"  {table[0]}")

    # Check row counts for each table
    print("\nRow counts:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} rows")

    conn.close()

if __name__ == "__main__":
    check_tables()