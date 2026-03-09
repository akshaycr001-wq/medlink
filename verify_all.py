from app import app, Hospital, Ambulance

def verify():
    with app.app_context():
        print("--- HOSPITALS ---")
        hospitals = Hospital.query.all()
        for h in hospitals:
            print(f"{h.name}: ({h.latitude}, {h.longitude}) Address: {h.address}")
            
        print("\n--- AMBULANCES ---")
        ambulances = Ambulance.query.all()
        for a in ambulances:
            hosp_name = a.hospital.name if a.hospital else "NO HOSPITAL"
            print(f"Amb {a.vehicle_number} tied to {hosp_name}")

if __name__ == "__main__":
    verify()
