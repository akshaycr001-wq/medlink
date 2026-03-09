from sqlalchemy import text
from app import app, db

def drop_driver_name():
    with app.app_context():
        engine = db.engine
        queries = [
            "ALTER TABLE ambulance DROP COLUMN IF EXISTS driver_name;",
            "ALTER TABLE hospital DROP COLUMN IF EXISTS driver_name;"
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
    drop_driver_name()
    print("Database migration (DROP COLUMN) completed.")
