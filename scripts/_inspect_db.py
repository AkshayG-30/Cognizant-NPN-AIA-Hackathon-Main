import sqlite3
conn = sqlite3.connect(r'd:\CTS\carepath_dev.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)
for t in tables:
    cols = [(r[1], r[2]) for r in cur.execute(f"PRAGMA table_info({t})").fetchall()]
    cnt = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"\n  {t} ({cnt} rows):")
    for c, tp in cols:
        print(f"    {c} ({tp})")
conn.close()
