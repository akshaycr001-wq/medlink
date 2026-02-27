
from app import app, db, User, Pharmacy
from werkzeug.security import generate_password_hash

def test_register_patient():
    with app.app_context():
        print("Testing Patient Registration...")
        try:
            username = "testpatient_debug"
            email = "test@debug.com"
            password = "password123"
            role = "patient"
            name = "Debug Patient"
            phone = "1234567890"
            
            # Check if exists
            existing = User.query.filter_by(username=username).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
                print(f"Deleted existing test user {username}")

            hashed_password = generate_password_hash(password, method='scrypt')
            new_user = User(
                username=username, 
                phone=phone, 
                email=email, 
                password=hashed_password, 
                role=role, 
                name=name, 
                email_verified=False
            )
            db.session.add(new_user)
            db.session.commit()
            print("Successfully registered patient in DB!")
            
        except Exception as e:
            print(f"Error registering patient: {str(e)}")
            db.session.rollback()

def test_register_pharmacy():
    with app.app_context():
        print("\nTesting Pharmacy Registration...")
        try:
            username = "testpharmacy_debug"
            email = "pharmacy@debug.com"
            password = "password123"
            role = "pharmacy"
            name = "Debug Pharmacy Shop"
            phone = "1234567890"
            
            # Check if exists
            existing = User.query.filter_by(username=username).first()
            if existing:
                db.session.delete(existing)
                # Also delete pharmacy
                pharm = Pharmacy.query.filter_by(shop_name=name).first()
                if pharm:
                    db.session.delete(pharm)
                db.session.commit()
                print(f"Deleted existing test pharmacy {username}")

            hashed_password = generate_password_hash(password, method='scrypt')
            new_user = User(
                username=username, 
                phone=phone, 
                email=email, 
                password=hashed_password, 
                role=role, 
                name=name, 
                email_verified=False
            )
            db.session.add(new_user)
            db.session.flush() # Get user ID
            
            new_pharmacy = Pharmacy(
                user_id=new_user.id, 
                shop_name=name, 
                phone=phone,
                location_address="Test Address",
                verified=False
            )
            db.session.add(new_pharmacy)
            db.session.commit()
            print("Successfully registered pharmacy in DB!")
            
        except Exception as e:
            print(f"Error registering pharmacy: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    test_register_patient()
    test_register_pharmacy()
