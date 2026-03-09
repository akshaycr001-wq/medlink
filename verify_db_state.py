import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("DATABASE_URL not found in .env")
else:
    print(f"Checking connection to: {db_url}")
    try:
        # Handle the postgres:// vs postgresql:// issue just in case
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nConnected successfully!")
        print(f"Database Name: {engine.url.database}")
        print(f"Tables found in public schema: {len(tables)}")
        for table in tables:
            print(f" - {table}")
            
        if not tables:
            print("\nWARNING: No tables found. You might be connected to an empty database.")
            
    except Exception as e:
        print(f"\nError: {e}")
