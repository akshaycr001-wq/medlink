from app import app
from models import db, Pharmacy
with app.app_context():
    p = Pharmacy.query.filter_by(user_id=2).first()
    if p:
        print(p.to_dict())
    else:
        print("Pharmacy record for user_id 2 not found")
