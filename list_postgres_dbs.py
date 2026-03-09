import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("DATABASE_URL not found in .env")
else:
    # Connect to 'postgres' database to list other databases
    base_url = db_url.rsplit('/', 1)[0] + '/postgres'
    print(f"Connecting to: {base_url} to list databases...")
    
    try:
        engine = create_engine(base_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false;"))
            databases = [row[0] for row in result]
            print("\nDatabases found on server:")
            for db in databases:
                print(f" - {db}")
                
        print(f"\nYour .env is targeting: {db_url.rsplit('/', 1)[1]}")
        
    except Exception as e:
        print(f"\nError: {e}")
