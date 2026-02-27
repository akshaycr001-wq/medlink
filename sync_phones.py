import sqlite3
import os

db_path = os.path.join('instance', 'medlink.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Migrate numbers from pharmacy table to user table
    cursor.execute("""
        UPDATE user 
        SET phone = (SELECT phone FROM pharmacy WHERE pharmacy.user_id = user.id)
        WHERE role = 'pharmacy' AND phone IS NULL
    """)
    print("Migrated phone numbers for existing pharmacies.")
    
    # 2. For patients who have None, set a placeholder so links don't break
    # Note: User can update these later
    cursor.execute("UPDATE user SET phone = '9876543210' WHERE phone IS NULL")
    print("Set placeholder '9876543210' for remaining users.")
    
    conn.commit()
    conn.close()
    print("Database updated successfully.")
else:
    print(f"Database not found at {db_path}")
