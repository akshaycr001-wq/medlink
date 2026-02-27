from app import app, db
from models import Pharmacy, SystemAlert, Review, User, Medicine
import datetime

with app.app_context():
    # Find the first pharmacy (you can change this if you know the specific one)
    pharmacy = Pharmacy.query.first()
    
    if not pharmacy:
        print("No pharmacy found! Please create one first.")
        exit(1)

    print(f"Adding data for Pharmacy: {pharmacy.shop_name} (ID: {pharmacy.id})")

    # Add a sample System Alert
    alert = SystemAlert(
        message="Please ensure your stock of Paracetamol is updated.",
        type="info",
        pharmacy_id=pharmacy.id,
        created_at=datetime.datetime.now()
    )
    db.session.add(alert)
    print("Added: Info Alert")

    alert2 = SystemAlert(
        message="New government regulation regarding antibiotic sales.",
        type="warning",
        pharmacy_id=pharmacy.id,
        created_at=datetime.datetime.now() - datetime.timedelta(hours=2)
    )
    db.session.add(alert2)
    print("Added: Warning Alert")

    # Add a sample Review
    # We need a user to create a review, let's find one or create a dummy user
    reviewer = User.query.filter_by(role='patient').first()
    if not reviewer:
        # Create a dummy patient if none exists
        reviewer = User(username='patient_test', email='patient@test.com', role='patient', name='Test Patient')
        reviewer.set_password('password')
        db.session.add(reviewer)
        db.session.commit()
        print("Created dummy patient for review.")

    review = Review(
        user_id=reviewer.id,
        pharmacy_id=pharmacy.id,
        rating=5,
        comment="Excellent service and quick delivery!",
        user_name=reviewer.name,
        created_at=datetime.datetime.now()
    )
    db.session.add(review)
    print("Added: 5-star Review")

    review2 = Review(
        user_id=reviewer.id,
        pharmacy_id=pharmacy.id,
        rating=4,
        comment="Good stock, but slightly delayed.",
        user_name=reviewer.name,
        created_at=datetime.datetime.now() - datetime.timedelta(days=2)
    )
    db.session.add(review2)
    print("Added: 4-star Review")

    db.session.commit()
    print("Sample data added successfully!")
