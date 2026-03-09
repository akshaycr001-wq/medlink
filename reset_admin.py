import os
from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def reset_admin():
    username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
    
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"Updating password for user '{username}'...")
            user.password = generate_password_hash(password, method='scrypt')
            db.session.commit()
            print("Password updated successfully.")
        else:
            print(f"User '{username}' not found. Creating new...")
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
            print("New admin account created.")

if __name__ == "__main__":
    reset_admin()
