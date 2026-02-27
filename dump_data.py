from app import app, db, User, Pharmacy, Hospital, Medicine, SOS, Ambulance, Review, SystemAlert, MedicineAlternative
import json
import os

def dump_data():
    with app.app_context():
        # Force SQLite configuration just for this script
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/medlink.db'
        db.engine.dispose() # Close any existing Postgres connections
        
        data = {
            'users': [u.to_dict() if hasattr(u, 'to_dict') else {'id': u.id, 'username': u.username, 'password': getattr(u, 'password', None), 'email': getattr(u, 'email', None), 'role': getattr(u, 'role', None), 'name': getattr(u, 'name', None)} for u in User.query.all()],
            'pharmacies': [p.to_dict() if hasattr(p, 'to_dict') else {'id': p.id, 'shop_name': p.shop_name, 'location_address': p.location_address, 'prc_no': p.prc_no, 'dl_no': p.dl_no, 'verified': p.verified, 'latitude': p.latitude, 'longitude': p.longitude, 'phone': getattr(p, 'phone', None)} for p in Pharmacy.query.all()],
            'medicines': [m.to_dict() if hasattr(m, 'to_dict') else {'id': m.id, 'name': m.name, 'manufacturer': getattr(m, 'manufacturer', None), 'description': getattr(m, 'description', None), 'quantity': getattr(m, 'quantity', 0), 'price': getattr(m, 'price', None), 'expiry_date': getattr(m, 'expiry_date', None), 'pharmacy_id': getattr(m, 'pharmacy_id', None)} for m in Medicine.query.all()],
            'ambulances': [a.to_dict() if hasattr(a, 'to_dict') else {'id': a.id, 'vehicle_number': a.vehicle_number, 'driver_name': getattr(a, 'driver_name', 'Unknown'), 'phone': getattr(a, 'phone', '0000000000'), 'latitude': getattr(a, 'latitude', None), 'longitude': getattr(a, 'longitude', None), 'status': getattr(a, 'status', 'available'), 'hospital_id': getattr(a, 'hospital_id', None)} for a in Ambulance.query.all()]
        }
        
        with open('data_dump.json', 'w') as f:
            json.dump(data, f, indent=4)
        print("Data dumped successfully with passwords included into data_dump.json")

if __name__ == "__main__":
    dump_data()
