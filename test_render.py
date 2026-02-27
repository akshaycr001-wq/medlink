from app import app, db, User, Pharmacy, Hospital, Medicine, SOS, Ambulance
from flask import render_template

with app.test_request_context():
    # Create some dummy data
    pharmacies = [Pharmacy(id=1, shop_name="Test Pharma", verified=True)]
    sub_admins = [User(id=2, username="sub@test.com", name="Sub Admin", role="sub_admin")]
    hospitals = [Hospital(id=1, name="Test Hospital")]
    medicines = [Medicine(id=1, name="Medicine A")]
    ambulances = [Ambulance(id=1, vehicle_number="AMB01")]
    emergencies = [SOS(id=1, medicine_name="SOS A", patient_id=1)]
    
    try:
        html = render_template('admin_dashboard.html', 
                               pharmacies=pharmacies, 
                               sub_admins=sub_admins, 
                               hospitals=hospitals,
                               medicines=medicines,
                               ambulances=ambulances,
                               emergencies=emergencies,
                               medicines_count=1,
                               ambulances_count=1)
        print("Template rendered successfully")
    except Exception as e:
        import traceback
        print(f"Template rendering failed: {e}")
        traceback.print_exc()
