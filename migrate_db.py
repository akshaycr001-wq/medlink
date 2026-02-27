import sqlite3
import os

db_path = os.path.join('instance', 'medlink.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Add phone column to user table
        cursor.execute("ALTER TABLE user ADD COLUMN phone VARCHAR(20)")
        print("Successfully added 'phone' column to 'user' table.")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("'phone' column already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
