import sqlite3
import os

db_path = os.path.join('instance', 'medlink.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Users ---")
    cursor.execute("SELECT id, username, role, phone FROM user")
    users = cursor.fetchall()
    for u in users:
        print(f"ID: {u[0]} | Username: {u[1]} | Role: {u[2]} | Phone: {u[3]}")
    
    print("\n--- Pharmacies ---")
    cursor.execute("SELECT id, user_id, shop_name, phone FROM pharmacy")
    pharmacies = cursor.fetchall()
    for p in pharmacies:
        print(f"ID: {p[0]} | UserID: {p[1]} | Shop: {p[2]} | Phone: {p[3]}")
    
    conn.close()
else:
    print(f"Database not found at {db_path}")
