import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from models import db
from app import app

load_dotenv()

def update_db():
    with app.app_context():
        engine = db.engine
        
        print("Starting database migration...")
        
        # SQL for adding columns to the review table
        # We use IF NOT EXISTS if possible, but standard SQL ALTER TABLE is safer with try-except
        alter_queries = [
            "ALTER TABLE review ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES \"user\"(id)",
            "ALTER TABLE review ADD COLUMN IF NOT EXISTS pharmacy_reply TEXT",
            "ALTER TABLE review ADD COLUMN IF NOT EXISTS reply_at TIMESTAMP WITHOUT TIME ZONE"
        ]
        
        with engine.connect() as conn:
            for query in alter_queries:
                try:
                    conn.execute(text(query))
                    conn.commit()
                    print(f"Executed: {query}")
                except Exception as e:
                    print(f"Failed or already exists: {query} Error: {e}")
                    conn.rollback()
        
        print("Database migration completed.")

if __name__ == "__main__":
    update_db()
