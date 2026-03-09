from app import app, db, Hospital

fixes = {
    "Rajagiri Hospital": (10.1235, 76.3533),
    "Aster Medcity": (10.0526, 76.2694),
    "Lourdes Hospital": (9.9934, 76.2736),
    "Aster Medcity - Kochi": (10.0526, 76.2694) # Possible variation
}

def cleanup():
    with app.app_context():
        for name, coords in fixes.items():
            hosp = Hospital.query.filter(Hospital.name.like(f"%{name}%")).first()
            if hosp:
                hosp.latitude = coords[0]
                hosp.longitude = coords[1]
                print(f"Updated {hosp.name} to {coords}")
        db.session.commit()

if __name__ == "__main__":
    cleanup()
    print("Cleanup complete!")
