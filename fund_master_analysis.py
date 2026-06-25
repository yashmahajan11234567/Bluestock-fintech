import pandas as pd

df = pd.read_csv("data/raw/01_fund_master.csv")

print("=" * 80)
print("UNIQUE FUND HOUSES")
print("=" * 80)
print(df["fund_house"].unique())
print("Count:", df["fund_house"].nunique())

print("\n" + "=" * 80)
print("CATEGORIES")
print("=" * 80)
print(df["category"].unique())

print("\n" + "=" * 80)
print("SUB-CATEGORIES")
print("=" * 80)
print(df["sub_category"].unique())

print("\n" + "=" * 80)
print("RISK CATEGORIES")
print("=" * 80)
print(df["risk_category"].unique())