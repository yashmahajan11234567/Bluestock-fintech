import os
import pandas as pd

RAW_PATH = "data/raw"
PROCESSED_PATH = "data/processed"

os.makedirs(PROCESSED_PATH, exist_ok=True)

print("=" * 80)
print("Cleaning nav_history.csv")
print("=" * 80)

nav = pd.read_csv(f"{RAW_PATH}/02_nav_history.csv")

# Convert date to datetime
nav["date"] = pd.to_datetime(nav["date"])

# Sort by fund and date
nav = nav.sort_values(["amfi_code", "date"])

# Forward fill missing NAV within each fund
nav["nav"] = nav.groupby("amfi_code")["nav"].ffill()

# Remove duplicate rows
nav = nav.drop_duplicates()

# Keep only positive NAV values
nav = nav[nav["nav"] > 0]

nav.to_csv(
    f"{PROCESSED_PATH}/02_nav_history_clean.csv",
    index=False
)

print("Rows:", len(nav))
print("Saved 02_nav_history_clean.csv")

print("\n" + "=" * 80)
print("Cleaning investor_transactions.csv")
print("=" * 80)

transactions = pd.read_csv(f"{RAW_PATH}/08_investor_transactions.csv")

transactions["transaction_date"] = pd.to_datetime(
    transactions["transaction_date"]
)

transactions["transaction_type"] = (
    transactions["transaction_type"]
    .str.strip()
    .str.title()
)

transactions = transactions[
    transactions["transaction_type"].isin(
        ["Sip", "Lumpsum", "Redemption"]
    )
]

transactions = transactions[
    transactions["amount_inr"] > 0
]

transactions["kyc_status"] = (
    transactions["kyc_status"]
    .str.strip()
    .str.title()
)

transactions.to_csv(
    f"{PROCESSED_PATH}/08_investor_transactions_clean.csv",
    index=False
)

print("Rows:", len(transactions))
print("Saved 08_investor_transactions_clean.csv")

print("\n" + "=" * 80)
print("Cleaning scheme_performance.csv")
print("=" * 80)

performance = pd.read_csv(f"{RAW_PATH}/07_scheme_performance.csv")

return_columns = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct",
    "benchmark_3yr_pct"
]

for col in return_columns:
    performance[col] = pd.to_numeric(
        performance[col],
        errors="coerce"
    )

performance = performance[
    performance["expense_ratio_pct"].between(0.1, 2.5)
]

performance.to_csv(
    f"{PROCESSED_PATH}/07_scheme_performance_clean.csv",
    index=False
)

print("Rows:", len(performance))
print("Saved 07_scheme_performance_clean.csv")

print("\nCleaning Completed Successfully!")