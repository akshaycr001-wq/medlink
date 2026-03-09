from app import app, db
from models import User

with app.app_context():
    users = User.query.all()
    print(f"Total users found: {len(users)}")
    for u in users:
        print(f"ID: {u.id} | Username: {u.username} | Role: {u.role} | Name: {u.name}")
