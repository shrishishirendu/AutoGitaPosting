import pandas as pd
from pathlib import Path

path = Path(__file__).parent / "data" / "gita" / "raw" / "main_utf8.csv"

try:
    df = pd.read_csv(path, encoding="utf-8-sig")
except UnicodeDecodeError:
    df = pd.read_csv(path, encoding="cp1252")

print("Columns:")
print(df.columns.tolist())

print("\nFirst Sanskrit verse (first 120 chars):")
print(str(df.iloc[0]["Sanskrit Anuvad"])[:120])

print("\nFirst English translation (first 120 chars):")
print(str(df.iloc[0]["Enlgish Translation"])[:120])

print("\nTotal rows:", len(df))
