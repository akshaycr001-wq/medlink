import sqlite3

db_path = 'instance/medlink.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]

for table in tables:
    print(f"\nTable: {table}")
    cursor.execute(f"PRAGMA table_info({table})")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")

conn.close()
