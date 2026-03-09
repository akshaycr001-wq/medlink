import os
import sys
import json
import urllib.parse
import urllib.request
from app import app, db, Hospital, Ambulance

def geocode_location(name, address):
    """Attempt to geocode a location name and address using Nominatim (free)."""
    try:
        # Prioritize Name + Kochi for better local results
        query = f"{name}, Kochi, Kerala, India"
        safe_query = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={safe_query}&format=json&limit=1"
        
        headers = {'User-Agent': 'MedLink-Emergency-Network/1.1'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
            
            # Fallback to address if name search fails
            if address:
                query_fallback = f"{address}, Kochi, Kerala, India"
                safe_query_f = urllib.parse.quote(query_fallback)
                url_f = f"https://nominatim.openstreetmap.org/search?q={safe_query_f}&format=json&limit=1"
                req_f = urllib.request.Request(url_f, headers=headers)
                with urllib.request.urlopen(req_f, timeout=10) as res_f:
                    data_f = json.loads(res_f.read().decode())
                    if data_f:
                        return float(data_f[0]['lat']), float(data_f[0]['lon'])
    except Exception as e:
        print(f"DEBUG: Geocoding failed for {name}: {e}")
    return None, None

hospitals_data = [
    {"name": "Aster Medcity", "address": "Cheranelloor, Kochi, Kerala 682027", "phone": "0484 6699999", "emergency": "0484 6699911", "amb": "KL-07-CD-1122"},
    {"name": "Ernakulam Medical Centre", "address": "NH Bypass, Palarivattom, Kochi, Kerala 682025", "phone": "0484 2807101", "emergency": "0484 2807108", "amb": "KL-07-BF-4545"},
    {"name": "Medical Trust Hospital", "address": "MG Road, Kochi, Kerala 682016", "phone": "0484 2358001", "emergency": "0484 2358008", "amb": "KL-07-AL-9000"},
    {"name": "Amrita Hospital", "address": "Ponekkara, Kochi, Kerala 682041", "phone": "0484 2851234", "emergency": "0484 2851100", "amb": "KL-07-ER-7788"},
    {"name": "Rajagiri Hospital", "address": "Chunangamvely, Aluva, Kochi, Kerala 683112", "phone": "0484 2905000", "emergency": "0484 2905999", "amb": "KL-41-TR-3344"},
    {"name": "Lisie Hospital", "address": "Kaloor, Kochi, Kerala 682018", "phone": "0484 2402044", "emergency": "0484 2402050", "amb": "KL-07-LL-1010"},
    {"name": "Lourdes Hospital", "address": "Pachalam, Kochi, Kerala 682012", "phone": "0484 2393720", "emergency": "0484 2393710", "amb": "KL-07-PA-5566"},
    {"name": "VPS Lakeshore Hospital", "address": "Nettoor, Kochi, Kerala 682040", "phone": "0484 2701032", "emergency": "0484 2701099", "amb": "KL-07-LK-2233"},
    {"name": "Renai Medicity", "address": "Palarivattom, Kochi, Kerala 682025", "phone": "0484 2444444", "emergency": "0484 2444400", "amb": "KL-07-RN-9999"},
    {"name": "Sunrise Hospital", "address": "Seaport-Airport Rd, Kakkanad, Kochi, Kerala 682030", "phone": "0484 2428917", "emergency": "0484 2428900", "amb": "KL-07-SR-4455"}
]

def seed_hospitals():
    with app.app_context():
        for h in hospitals_data:
            existing = Hospital.query.filter_by(name=h['name']).first()
            if existing:
                # Update existing to fix data rather than skip
                existing.driver_no = h['emergency']
                db.session.commit()
                print(f"Updated emergency number for {h['name']}")
                # Also update their ambulance record
                amb = Ambulance.query.filter_by(hospital_id=existing.id).first()
                if amb:
                    amb.driver_phone = h['emergency']
                    db.session.commit()
                continue
                
            print(f"Geocoding {h['name']}...")
            lat, lon = geocode_location(h['name'], h['address'])
            
            new_hosp = Hospital(
                name=h['name'],
                address=h['address'],
                phone=h['phone'],
                ambulance_no=h['amb'],
                driver_no=h['emergency'],  # Use distinct emergency line
                latitude=lat,
                longitude=lon
            )
            db.session.add(new_hosp)
            db.session.commit()
            
            # Add to ambulance fleet as well
            new_amb = Ambulance(
                vehicle_number=h['amb'],
                driver_phone=h['emergency'],  # Use distinct emergency line
                hospital_id=new_hosp.id,
                address=h['address']
            )
            db.session.add(new_amb)
            db.session.commit()
            
            print(f"Added {h['name']} at ({lat}, {lon})")

def seed_hospitals():
    with app.app_context():
        # Clear existing hospitals to avoid duplicates for this seed
        # Hospital.query.delete() # Deleting might break relationships if not careful, better to check by name
        
        for h in hospitals_data:
            existing = Hospital.query.filter_by(name=h['name']).first()
            if existing:
                print(f"Skipping {h['name']} - already exists")
                continue
                
            print(f"Geocoding {h['name']}...")
            lat, lon = geocode_location(h['name'], h['address'])
            
            new_hosp = Hospital(
                name=h['name'],
                address=h['address'],
                phone=h['phone'],
                ambulance_no=h['amb'],
                driver_no=h['phone'], # Using hospital phone as dispatch
                latitude=lat,
                longitude=lon
            )
            db.session.add(new_hosp)
            db.session.commit()
            
            # Add to ambulance fleet as well
            new_amb = Ambulance(
                vehicle_number=h['amb'],
                driver_phone=h['phone'],
                hospital_id=new_hosp.id,
                address=h['address']
            )
            db.session.add(new_amb)
            db.session.commit()
            
            print(f"Added {h['name']} at ({lat}, {lon})")

if __name__ == "__main__":
    seed_hospitals()
    print("Seeding complete!")
