from app import app
from models import db, MedicineAlternative

def init_alternatives():
    """Initialize common medicine alternatives"""
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        print("Database tables created/verified")
        
        # Clear existing alternatives
        try:
            MedicineAlternative.query.delete()
        except:
            pass  # Table might be empty
        
        # Common brand to generic mappings
        alternatives = [
            ('Dolo', 'Paracetamol'),
            ('Crocin', 'Paracetamol'),
            ('Calpol', 'Paracetamol'),
            ('Metacin', 'Paracetamol'),
            ('Disprin', 'Aspirin'),
            ('Ecosprin', 'Aspirin'),
            ('Brufen', 'Ibuprofen'),
            ('Combiflam', 'Ibuprofen'),
            ('Avomine', 'Promethazine'),
            ('Phenergan', 'Promethazine'),
            ('Voveran', 'Diclofenac'),
            ('Volini', 'Diclofenac'),
            ('Augmentin', 'Amoxicillin'),
            ('Mox', 'Amoxicillin'),
            ('Azithral', 'Azithromycin'),
            ('Zithromax', 'Azithromycin'),
        ]
        
        for brand, generic in alternatives:
            alt = MedicineAlternative(
                medicine_name=brand,
                alternative_name=generic
            )
            db.session.add(alt)
        
        db.session.commit()
        print(f"[SUCCESS] Added {len(alternatives)} medicine alternatives")
        print("\nSample mappings:")
        for brand, generic in alternatives[:5]:
            print(f"  {brand} -> {generic}")

if __name__ == '__main__':
    init_alternatives()
