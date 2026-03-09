from sqlalchemy import text
from app import app, db

def fix_nullable_driver():
    with app.app_context():
        engine = db.engine
        queries = [
            "ALTER TABLE ambulance ALTER COLUMN driver_name DROP NOT NULL;",
            "ALTER TABLE hospital ALTER COLUMN driver_name DROP NOT NULL;"
        ]
        
        with engine.connect() as conn:
            for query in queries:
                try:
                    conn.execute(text(query))
                    conn.commit()
                    print(f"Executed: {query}")
                except Exception as e:
                    print(f"Error executing {query}: {e}")
                    conn.rollback()

if __name__ == "__main__":
    fix_nullable_driver()
    print("Database schema updated.")
