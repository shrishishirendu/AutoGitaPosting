from pathlib import Path

p = Path("data/gita/raw/main.csv")

raw = p.read_bytes()
print("File size:", len(raw))
print("First 200 bytes:", raw[:200])
print("Contains UTF-8 Devanagari bytes pattern (E0 A4):", b"\xE0\xA4" in raw)
print("Contains UTF-8 Devanagari bytes pattern (E0 A5):", b"\xE0\xA5" in raw)
