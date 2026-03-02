from app import app
from models import db, User
with app.app_context():
    pharmacies = User.query.filter_by(role='pharmacy').all()
    print(f"Found {len(pharmacies)} pharmacies:")
    for p in pharmacies:
        print(f"ID: {p.id}, Username: {p.username}, Name: {p.name}")
