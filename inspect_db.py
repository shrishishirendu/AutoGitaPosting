import sqlite3

db_path = r"data\app.db"
conn = sqlite3.connect(db_path)

rows = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables in DB:")
for r in rows:
    print(" -", r[0])
