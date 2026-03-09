from app import app, db
import sqlalchemy as sa
from sqlalchemy import text

with app.app_context():
    inspector = sa.inspect(db.engine)
    
    # Check User table
    user_cols = [c['name'] for c in inspector.get_columns('user')]
    if 'is_suspended' not in user_cols:
        db.session.execute(text('ALTER TABLE "user" ADD COLUMN is_suspended BOOLEAN DEFAULT FALSE'))
        print('Added is_suspended to User table')
    else:
        print('is_suspended already exists in User table')
        
    # Check Pharmacy table
    pharma_cols = [c['name'] for c in inspector.get_columns('pharmacy')]
    if 'is_suspended' not in pharma_cols:
        db.session.execute(text('ALTER TABLE pharmacy ADD COLUMN is_suspended BOOLEAN DEFAULT FALSE'))
        print('Added is_suspended to Pharmacy table')
    else:
        print('is_suspended already exists in Pharmacy table')
        
    db.session.commit()
    print("Migration complete!")
