import sqlite3
import os

db_path = r'c:\Users\eldho\Downloads\Templatefolder\instance\medlink.db'

if os.path.exists(db_path):
    print(f"Checking {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(pharmacy)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns in 'pharmacy' table: {columns}")
    
    needed_columns = {
        'dl_no': 'VARCHAR(50)',
        'prc_no': 'VARCHAR(50)',
        'license_doc': 'VARCHAR(255)',
        'verified': 'BOOLEAN DEFAULT 0',
        'latitude': 'FLOAT',
        'longitude': 'FLOAT',
        'location_address': 'VARCHAR(255)'
    }
    
    added = []
    for col, data_type in needed_columns.items():
        if col not in columns:
            print(f"Adding '{col}' column...")
            try:
                cursor.execute(f"ALTER TABLE pharmacy ADD COLUMN {col} {data_type}")
                added.append(col)
            except Exception as e:
                print(f"Failed to add {col}: {e}")
    
    if added:
        conn.commit()
        print(f"Successfully added: {added}")
    else:
        print("All columns already exist.")
    conn.close()
else:
    print(f"Database not found at {db_path}")
