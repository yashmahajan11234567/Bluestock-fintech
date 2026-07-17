import os
import pandas as pd

RAW_DATA_PATH = "data/raw"

csv_files = sorted(
    [file for file in os.listdir(RAW_DATA_PATH) if file.endswith(".csv")]
)

print("=" * 100)
print(f"Total CSV files found: {len(csv_files)}")
print("=" * 100)

for file in csv_files:

    print("\n" + "=" * 100)
    print(f"Dataset: {file}")
    print("=" * 100)

    file_path = os.path.join(RAW_DATA_PATH, file)

    try:
        df = pd.read_csv(file_path)

        print("\nShape:")
        print(df.shape)

        print("\nData Types:")
        print(df.dtypes)

        print("\nFirst 5 Rows:")
        print(df.head())

        print("\nMissing Values:")
        print(df.isnull().sum())

        print("\nDuplicate Rows:", df.duplicated().sum())

    except Exception as e:
        print(f"Error reading {file}: {e}")

print("\nFinished loading all datasets.")