import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def setup_db():
    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='postgres:akshay2005'.split(':')[-1],
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if medlink exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'medlink'")
        exists = cur.fetchone()
        if not exists:
            cur.execute('CREATE DATABASE medlink')
            print("DONE: Database 'medlink' created.")
        else:
            print("INFO: Database 'medlink' already exists.")
            
        cur.close()
        conn.close()
        print("SUCCESS: PostgreSQL connection test passed.")
    except Exception as e:
        print(f"ERROR: PostgreSQL Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_db()
