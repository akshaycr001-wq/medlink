from app import app, db, Hospital, Ambulance

def fix():
    with app.app_context():
        hospitals = Hospital.query.all()
        for h in hospitals:
            if not h.ambulances:
                print(f"Adding missing ambulance for {h.name}")
                new_amb = Ambulance(
                    vehicle_number=h.ambulance_no or f"KL-07-EX-{h.id:02d}",
                    driver_phone=h.driver_no or h.phone,
                    hospital_id=h.id,
                    address=h.address
                )
                db.session.add(new_amb)
        db.session.commit()

if __name__ == "__main__":
    fix()
