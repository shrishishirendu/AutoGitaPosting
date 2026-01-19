from pathlib import Path

p = Path("data/gita/raw/main_utf8.csv")
raw = p.read_bytes()

print("File exists:", p.exists())
print("File size:", len(raw))
print("Has UTF-8 Devanagari bytes E0 A4:", b"\xE0\xA4" in raw)
print("Has UTF-8 Devanagari bytes E0 A5:", b"\xE0\xA5" in raw)
