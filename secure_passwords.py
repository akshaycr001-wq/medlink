import sys
import os
sys.path.insert(0, os.path.abspath(os.getcwd()))

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def secure_all_passwords():
    with app.app_context():
        print("--- Initiating Security Hardening: Password Privacy Audit ---")
        users = User.query.all()
        updated_count = 0
        already_hashed = 0
        
        for u in users:
            # Check if password already looks like a hash
            is_hashed = (u.password.startswith('scrypt:') or 
                         u.password.startswith('pbkdf2:sha256:') or 
                         u.password.startswith('argon2:'))
            
            if not is_hashed:
                print(f"Securing password for user: {u.username}")
                u.password = generate_password_hash(u.password, method='scrypt')
                updated_count += 1
            else:
                already_hashed += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"Success: {updated_count} passwords were newly secured (hashed).")
        else:
            print("Audit complete: All existing passwords were already securely hashed.")
        
        print(f"Total verified users: {len(users)}")
        print(f"Already secure: {already_hashed}")

if __name__ == "__main__":
    secure_all_passwords()
