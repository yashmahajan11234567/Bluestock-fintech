import os
import pandas as pd
from sqlalchemy import create_engine

PROCESSED_PATH = "data/processed"

engine = create_engine("sqlite:///bluestock_mf.db")

files = [
    "02_nav_history_clean.csv",
    "07_scheme_performance_clean.csv",
    "08_investor_transactions_clean.csv"
]

print("=" * 80)
print("Loading cleaned datasets into SQLite")
print("=" * 80)

for file in files:

    table_name = file.replace("_clean.csv", "")

    df = pd.read_csv(os.path.join(PROCESSED_PATH, file))

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False
    )

    print(f"{table_name}")
    print(f"Rows Loaded : {len(df)}")
    print("-" * 50)

print("\nDatabase created successfully!")