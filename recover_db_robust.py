
import sqlite3
import os

def recover_malformed_db(old_db_path, new_db_path):
    print(f"Starting recovery: {old_db_path} -> {new_db_path}")
    
    if os.path.exists(new_db_path):
        os.remove(new_db_path)
    
    try:
        # Try to use the dump/iterdump method via python
        src_conn = sqlite3.connect(old_db_path)
        dst_conn = sqlite3.connect(new_db_path)
        
        # Iterdump can sometimes get past corruption if it's not in the master table
        # If it fails, we fall back to manual table-by-table copy
        try:
            for line in src_conn.iterdump():
                dst_conn.execute(line)
            dst_conn.commit()
            print("Successfully recovered using iterdump!")
        except Exception as e:
            print(f"Iterdump failed: {e}. Falling back to manual table copy.")
            dst_conn.close()
            os.remove(new_db_path)
            dst_conn = sqlite3.connect(new_db_path)
            
            # Get table list
            cursor = src_conn.cursor()
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table_name, create_sql in tables:
                if table_name.startswith('sqlite_'): continue
                print(f"Copying table: {table_name}")
                try:
                    dst_conn.execute(create_sql)
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    if rows:
                        placeholders = ",".join(["?"] * len(rows[0]))
                        dst_conn.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
                    dst_conn.commit()
                except Exception as ex:
                    print(f"Failed to copy table {table_name}: {ex}")
            
        src_conn.close()
        dst_conn.close()
        print("Recovery attempt finished.")
        
    except Exception as e:
        print(f"Fatal error during recovery: {e}")

if __name__ == "__main__":
    old_db = os.path.join('instance', 'medlink.db')
    new_db = os.path.join('instance', 'medlink_fixed.db')
    recover_malformed_db(old_db, new_db)
