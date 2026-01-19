from pathlib import Path

p = Path("data/gita/raw")
print("RAW DIR EXISTS:", p.exists())
print("RAW DIR:", p.resolve())

if p.exists():
    files = sorted(p.glob("*"))
    print("FILES:")
    for f in files:
        print(" -", f.name, "|", f.stat().st_size, "bytes")
