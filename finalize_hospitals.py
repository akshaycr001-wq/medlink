from app import app, db, Hospital

def finalize():
    with app.app_context():
        # Delete independent fleet placeholders
        Hospital.query.filter_by(name="Independent Ambulance Fleet").delete()
        
        # Delete entries without coordinates
        Hospital.query.filter(Hospital.latitude.is_(None)).delete()
        Hospital.query.filter(Hospital.longitude.is_(None)).delete()
        
        db.session.commit()
        print("Duplicates and placeholders removed.")

if __name__ == "__main__":
    finalize()
