from app import app
from models import db, Medicine, Pharmacy, User, MedicineAlternative
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def add_test_data():
    """Add test data to verify alternative medicine functionality"""
    with app.app_context():
        print("Adding test data for alternative medicine feature...")
        
        # Check if test pharmacy exists
        test_pharmacy_user = User.query.filter_by(username='testpharmacy').first()
        
        if not test_pharmacy_user:
            # Create test pharmacy user
            test_pharmacy_user = User(
                username='testpharmacy',
                email='test@pharmacy.com',
                password=generate_password_hash('test123', method='scrypt'),
                role='pharmacy',
                name='Test Pharmacy'
            )
            db.session.add(test_pharmacy_user)
            db.session.commit()
            
            # Create pharmacy profile
            test_pharmacy = Pharmacy(
                user_id=test_pharmacy_user.id,
                shop_name='Test Pharmacy',
                phone='9876543210',
                dl_no='DL123',
                prc_no='PRC123',
                location_address='Test Location',
                latitude=12.9716,
                longitude=77.5946,
                verified=True
            )
            db.session.add(test_pharmacy)
            db.session.commit()
            print(f"Created test pharmacy: {test_pharmacy.shop_name}")
        else:
            test_pharmacy = Pharmacy.query.filter_by(user_id=test_pharmacy_user.id).first()
            print(f"Using existing test pharmacy: {test_pharmacy.shop_name}")
        
        # Add test medicines (alternatives but NOT the brand names)
        test_medicines = [
            ('Paracetamol', 50, 10.00),  # Alternative for Dolo, Crocin, Calpol
            ('Aspirin', 30, 15.00),      # Alternative for Disprin, Ecosprin
            ('Ibuprofen', 40, 20.00),    # Alternative for Brufen, Combiflam
            ('Diclofenac', 25, 25.00),   # Alternative for Voveran, Volini
        ]
        
        for med_name, qty, price in test_medicines:
            # Check if medicine already exists
            existing = Medicine.query.filter_by(
                pharmacy_id=test_pharmacy.id,
                name=med_name
            ).first()
            
            if not existing:
                medicine = Medicine(
                    pharmacy_id=test_pharmacy.id,
                    name=med_name,
                    qty=qty,
                    price=price,
                    expiry=(datetime.now() + timedelta(days=365)).date()
                )
                db.session.add(medicine)
                print(f"  Added: {med_name} (Qty: {qty}, Price: Rs.{price})")
        
        db.session.commit()
        
        print("\n[SUCCESS] Test data added successfully!")
        print("\nTest scenario:")
        print("1. Login as patient")
        print("2. Search for 'Dolo' (brand name)")
        print("3. System should show 'Paracetamol' as alternative")
        print("4. Alternative banner should appear with amber styling")
        
        # Verify alternatives exist
        alt_count = MedicineAlternative.query.count()
        print(f"\nAlternative mappings in database: {alt_count}")

if __name__ == '__main__':
    add_test_data()
