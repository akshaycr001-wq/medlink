import os
from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def seed_admin():
    username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
    print(f"Connecting to: {os.environ.get('DATABASE_URL')}")
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            return

        print(f"Creating default admin: {username}")
        hashed_password = generate_password_hash(password, method='scrypt')
        
        new_admin = User(
            username=username,
            password=hashed_password,
            role='admin',
            name='System Administrator',
            email_verified=True
        )
        
        db.session.add(new_admin)
        db.session.commit()
        print("Success! Default admin account created.")

if __name__ == "__main__":
    seed_admin()
