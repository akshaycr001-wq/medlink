from app import app, db, User, Pharmacy, Hospital, Medicine, SOS, Ambulance, Review, SystemAlert, MedicineAlternative
import json
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

def restore_data():
    # Only run this if DATABASE_URL is set in environment (i.e. Render PostgreSQL)
    if not os.environ.get('DATABASE_URL'):
        print("Please set your Render External Database URL in the .env file as DATABASE_URL.")
        return

    with app.app_context():
        try:
            with open('data_dump.json', 'r') as f:
                data = json.load(f)
            
            # Clear existing data just in case
            db.drop_all()
            db.create_all()

            # Insert Users
            for u in data.get('users', []):
                user = User(id=u['id'], username=u['username'], email=u.get('email', f"{u['username']}@example.com"), name=u['name'], role=u['role'])
                if 'password' in u:
                    user.password = u['password']
                # For safety, if password is lost, reset it to username
                if not user.password:
                    user.password = "pbkdf2:sha256:260000$missing$missing"
                db.session.add(user)
            
            # Insert Pharmacies
            for p in data.get('pharmacies', []):
                pharma = Pharmacy(id=p['id'], shop_name=p['shop_name'], location_address=p['location_address'], prc_no=p['prc_no'], dl_no=p['dl_no'], verified=p.get('verified', True), latitude=p.get('latitude'), longitude=p.get('longitude'), phone=p.get('phone', '0000000000'))
                db.session.add(pharma)
            
            # Insert Medicines
            for m in data.get('medicines', []):
                med = Medicine(id=m['id'], name=m['name'], manufacturer=m.get('manufacturer'), description=m.get('description'), quantity=m.get('quantity', 0), price=m.get('price'), expiry_date=m.get('expiry_date'), pharmacy_id=m['pharmacy_id'])
                db.session.add(med)
            
            # Insert Ambulances
            for a in data.get('ambulances', []):
                amb = Ambulance(id=a['id'], vehicle_number=a['vehicle_number'], driver_name=a.get('driver_name', 'Unknown'), phone=a.get('phone', '0000000000'), latitude=a.get('latitude'), longitude=a.get('longitude'), status=a.get('status', 'available'), hospital_id=a.get('hospital_id'))
                db.session.add(amb)

            db.session.commit()
            print("Successfully migrated local data to the PostgreSQL database!")
        except Exception as e:
            db.session.rollback()
            print(f"Error during migration: {e}")

if __name__ == "__main__":
    restore_data()
