import sqlite3
import os

db_path = 'instance/medlink.db'

def repair_database():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Repair medicine table
    cursor.execute("PRAGMA table_info(medicine)")
    columns = [col[1] for col in cursor.fetchall()]
    
    medicine_updates = [
        ('generic_name', 'VARCHAR(100)'),
        ('manufacturer', 'VARCHAR(100)'),
        ('description', 'VARCHAR(500)')
    ]

    for col_name, col_type in medicine_updates:
        if col_name not in columns:
            print(f"Adding column {col_name} to medicine table...")
            cursor.execute(f"ALTER TABLE medicine ADD COLUMN {col_name} {col_type}")
        else:
            print(f"Column {col_name} already exists in medicine table.")

    # Repair sos table
    cursor.execute("PRAGMA table_info(sos)")
    sos_columns = [col[1] for col in cursor.fetchall()]
    if 'status' not in sos_columns:
        print("Adding column status to sos table...")
        cursor.execute("ALTER TABLE sos ADD COLUMN status VARCHAR(20) DEFAULT 'open'")
    else:
        print("Column status already exists in sos table.")

    # Ensure other tables exist (Ambulance, SystemAlert, etc.)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Existing tables: {tables}")

    conn.commit()
    conn.close()
    print("Database repair complete.")

if __name__ == '__main__':
    repair_database()
