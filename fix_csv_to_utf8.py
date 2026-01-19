from pathlib import Path
import pandas as pd

src = Path("data/gita/raw/main.csv")
dst = Path("data/gita/raw/main_utf8.csv")

# Try these in order. We'll pick the first that loads AND appears to contain Devanagari.
candidates = ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin1"]

def has_devanagari(s: str) -> bool:
    # Devanagari Unicode block: 0900–097F
    return any("\u0900" <= ch <= "\u097F" for ch in s)

best = None
best_enc = None

for enc in candidates:
    try:
        df = pd.read_csv(src, encoding=enc, dtype=str, keep_default_na=False)
    except Exception:
        continue

    # Scan a few cells for Devanagari
    sample = " ".join(df.head(20).astype(str).fillna("").values.flatten().tolist())
    if has_devanagari(sample):
        best = df
        best_enc = enc
        break

if best is None:
    raise SystemExit(
        "Could not find an encoding that yields Devanagari characters. "
        "This CSV may have been saved in an ANSI encoding, destroying Sanskrit text. "
        "Re-download the dataset or find a source file that preserves Devanagari."
    )

# Write out a clean UTF-8 CSV
best.to_csv(dst, index=False, encoding="utf-8")
print(f"Loaded with encoding={best_enc}. Wrote cleaned UTF-8 CSV to: {dst}")
