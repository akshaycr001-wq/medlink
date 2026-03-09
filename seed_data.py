import os
from app import app, db
from models import User, Pharmacy, Medicine, Hospital, SOS, Ambulance, MedicineAlternative
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

def seed_data():
    with app.app_context():
        print("Cleaning up old sample data (if any)...")
        # We don't delete everything, just sample data if needed, 
        # but since it's a new DB, we can just add.
        
        # 1. Create a Patient User
        if not User.query.filter_by(username='patient').first():
            print("Creating sample patient...")
            patient = User(
                username='patient',
                password=generate_password_hash('patient123', method='scrypt'),
                role='patient',
                name='John Doe',
                phone='9876543210'
            )
            db.session.add(patient)
            db.session.flush() # Get ID
            
            # Create an SOS request for this patient
            sos = SOS(
                patient_id=patient.id,
                medicine_name='Insulin',
                latitude=12.9716,
                longitude=77.5946,
                status='open'
            )
            db.session.add(sos)

        # 2. Create a Verified Pharmacy
        if not User.query.filter_by(username='pharma1').first():
            print("Creating MedPlus Pharmacy...")
            pharma_user = User(
                username='pharma1',
                password=generate_password_hash('pharma123', method='scrypt'),
                role='pharmacy',
                name='MedPlus Admin'
            )
            db.session.add(pharma_user)
            db.session.flush()
            
            medplus = Pharmacy(
                user_id=pharma_user.id,
                shop_name='MedPlus Ernakulam',
                phone='0484-123456',
                dl_no='KL-ERS-12345',
                prc_no='P-999',
                verified=True,
                latitude=9.9816,
                longitude=76.2999,
                location_address='M.G. Road, Ernakulam'
            )
            db.session.add(medplus)
            db.session.flush()
            
            # Add some medicines to MedPlus
            m1 = Medicine(
                pharmacy_id=medplus.id,
                name='Dolo 650',
                generic_name='Paracetamol',
                manufacturer='Micro Labs',
                description='Anagesic and Antipyretic',
                qty=100,
                expiry=date.today() + timedelta(days=365),
                price=30.0
            )
            m2 = Medicine(
                pharmacy_id=medplus.id,
                name='Amoxicillin',
                generic_name='Amoxicillin',
                manufacturer='Abbott',
                qty=50,
                expiry=date.today() + timedelta(days=180),
                price=120.0
            )
            db.session.add_all([m1, m2])

        # 3. Create a Pending Pharmacy (for Admin to verify)
        if not User.query.filter_by(username='pharma2').first():
            print("Creating Apollo Pharmacy (Pending)...")
            pharma_user2 = User(
                username='pharma2',
                password=generate_password_hash('pharma123', method='scrypt'),
                role='pharmacy',
                name='Apollo Admin'
            )
            db.session.add(pharma_user2)
            db.session.flush()
            
            apollo = Pharmacy(
                user_id=pharma_user2.id,
                shop_name='Apollo Pharmacy',
                phone='0484-999888',
                dl_no='KL-ERS-99999',
                verified=False,
                location_address='Palarivattom, Kochi'
            )
            db.session.add(apollo)

        # 4. Create a Hospital and Ambulance
        if not Hospital.query.filter_by(name='City Hospital').first():
            print("Creating City Hospital...")
            hosp = Hospital(
                name='City Hospital',
                address='North Kochi',
                phone='0484-222333',
                ambulance_no='KL-07-AS-1234',
                driver_name='Suresh Gopi',
                driver_no='9988776655',
                latitude=10.0159,
                longitude=76.3419
            )
            db.session.add(hosp)
            db.session.flush()
            
            # Create a standalone ambulance linked to this hospital
            amb = Ambulance(
                vehicle_number='KL-07-AS-1234',
                driver_name='Suresh Gopi',
                driver_phone='9988776655',
                hospital_id=hosp.id,
                address='North Kochi'
            )
            db.session.add(amb)

        # 5. Seed Alternatives
        if not MedicineAlternative.query.first():
            print("Seeding alternatives...")
            alt1 = MedicineAlternative(medicine_name='Dolo 650', alternative_name='Paracetamol')
            alt2 = MedicineAlternative(medicine_name='Calpol 500', alternative_name='Paracetamol')
            db.session.add_all([alt1, alt2])

        # 6. Create a Sub-Admin
        if not User.query.filter_by(username='subadmin@medlink.com').first():
            print("Creating sample sub-admin...")
            sub_admin = User(
                username='subadmin@medlink.com',
                password=generate_password_hash('subadmin123', method='scrypt'),
                role='sub_admin',
                name='Jane Smith'
            )
            db.session.add(sub_admin)

        db.session.commit()
        print("Success! Sample data seeded successfully.")

if __name__ == "__main__":
    seed_data()
