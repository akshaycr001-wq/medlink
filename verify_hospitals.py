from app import app, Hospital

def verify():
    with app.app_context():
        hospitals = Hospital.query.all()
        for h in hospitals:
            print(f"{h.name}: ({h.latitude}, {h.longitude})")

if __name__ == "__main__":
    verify()
