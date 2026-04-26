import sys
try:
    from app import app, db
    with app.app_context():
        db.create_all()
        print("SUCCESS: Database tables created/verified in PostgreSQL.")
except Exception as e:
    print(f"ERROR: Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
