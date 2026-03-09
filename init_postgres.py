from app import app, db
from models import *

with app.app_context():
    print(f"DEBUG: Using URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    try:
        print("Creating tables in PostgreSQL...")
        db.create_all()
        print("Success! Tables created:")
        # Print the tables for verification
        for table in db.metadata.tables.keys():
            print(f" - {table}")
    except Exception as e:
        print(f"Error creating tables: {e}")
        print("\nMake sure your DATABASE_URL in .env is correct and PostgreSQL is running.")
