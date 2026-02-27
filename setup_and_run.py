
from app import app, db, User
from werkzeug.security import generate_password_hash
import os

with app.app_context():
    # Ensure database tables exist
    db.create_all()
    
    # Check if admin already exists
    admin = User.query.filter_by(username='admin@medlink.com').first()
    if not admin:
        admin = User(
            username='admin@medlink.com',
            password=generate_password_hash('admin123', method='scrypt'),
            role='admin',
            name='System Administrator'
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: admin@medlink.com / admin123")
    else:
        print("Admin user already exists.")

    print("Database initialization complete.")
