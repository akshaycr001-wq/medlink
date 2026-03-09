import sys
sys.path.append(r"c:\Users\eldho\Downloads\Templatefolder")
from app import app, db
from models import MedicineAlternative

common_alternatives = [
    # Analgesics & Antipyretics (Pain & Fever)
    ("Dolo 650", "Paracetamol"),
    ("Calpol 500", "Paracetamol"),
    ("Crocin Advance", "Paracetamol"),
    ("Panadol", "Paracetamol"),
    ("Tylenol", "Paracetamol"),
    ("Combiflam", "Ibuprofen + Paracetamol"),
    ("Flexon", "Ibuprofen + Paracetamol"),
    ("Brufen 400", "Ibuprofen"),
    ("Advil", "Ibuprofen"),
    ("Meftal Spas", "Mefenamic Acid + Dicyclomine"),
    ("Meftal 500", "Mefenamic Acid"),
    ("Zerodol P", "Aceclofenac + Paracetamol"),
    ("Aldigesic P", "Aceclofenac + Paracetamol"),
    ("Voveran SR", "Diclofenac"),
    ("Reactin SR", "Diclofenac"),
    ("Nise", "Nimesulide"),
    ("Sumo", "Nimesulide + Paracetamol"),

    # Antacids & Gastrointestinal (Acid Reflux, Digestion)
    ("Digene", "Magaldrate + Simethicone"),
    ("Gelusil", "Aluminum Hydroxide + Magnesium + Simethicone"),
    ("Omez", "Omeprazole"),
    ("Omecip", "Omeprazole"),
    ("Pan 40", "Pantoprazole"),
    ("Pantocid 40", "Pantoprazole"),
    ("Pantosec", "Pantoprazole"),
    ("Rantac 150", "Ranitidine"),
    ("Aciloc 150", "Ranitidine"),
    ("Zinetac", "Ranitidine"),
    ("Rabium 20", "Rabeprazole"),
    ("Rablet 20", "Rabeprazole"),
    ("Domstal", "Domperidone"),
    ("Vomitrol", "Ondansetron"),
    ("Ondem 4", "Ondansetron"),
    ("Zofer", "Ondansetron"),
    ("Econorm", "Saccharomyces Boulardii (Probiotic)"),
    ("Enterogermina", "Bacillus Clausii (Probiotic)"),

    # Anti-allergics & Cough/Cold
    ("Allegra 120", "Fexofenadine"),
    ("Avil 25", "Pheniramine Maleate"),
    ("Cetirizine Tablet", "Levocetirizine / Cetirizine"),
    ("Okacet", "Cetirizine"),
    ("Cetzine", "Cetirizine"),
    ("Alerid", "Cetirizine"),
    ("Levocet M", "Levocetirizine + Montelukast"),
    ("Montair LC", "Levocetirizine + Montelukast"),
    ("Montelekast", "Montelukast"),
    ("Cheston Cold", "Cetirizine + Paracetamol + Phenylephrine"),
    ("Sinarest", "Paracetamol + Phenylephrine + Chlorpheniramine"),
    ("Wikoryl", "Paracetamol + Phenylephrine + Chlorpheniramine"),
    ("Alex Syrup", "Dextromethorphan + Chlorpheniramine"),
    ("Benadryl Cough", "Diphenhydramine + Ammonium Chloride"),
    ("Corex DX", "Dextromethorphan + Chlorpheniramine"),
    ("Ascoril LS", "Ambroxol + Levosalbutamol + Guaiphenesin"),

    # Antibiotics (Requires Prescription, but commonly searched)
    ("Augmentin 625 Duo", "Amoxicillin + Clavulanic Acid"),
    ("Moxikind CV 625", "Amoxicillin + Clavulanic Acid"),
    ("Taxim O 200", "Cefixime"),
    ("Zifi 200", "Cefixime"),
    ("Mahacef 200", "Cefixime"),
    ("Azithral 500", "Azithromycin"),
    ("Azee 500", "Azithromycin"),
    ("Novamox 500", "Amoxicillin"),
    ("Cepodem 200", "Cefpodoxime"),
    ("Oflomac 200", "Ofloxacin"),
    ("Zanocin 200", "Ofloxacin"),
    ("Norflox TZ", "Norfloxacin + Tinidazole"),
    ("Metrogyl 400", "Metronidazole"),
    ("Ciprobid 500", "Ciprofloxacin"),
    ("Ciplox 500", "Ciprofloxacin"),
    ("Clavam 625", "Amoxicillin + Clavulanic Acid"),

    # Blood Pressure & Heart
    ("Amlokind 5", "Amlodipine"),
    ("Amlong 5", "Amlodipine"),
    ("Stamlo 5", "Amlodipine"),
    ("Telmikind 40", "Telmisartan"),
    ("Telvas 40", "Telmisartan"),
    ("Cresar 40", "Telmisartan"),
    ("Losar 50", "Losartan"),
    ("Repace 50", "Losartan"),
    ("Ecosprin 75", "Aspirin"),
    ("Atorva 10", "Atorvastatin"),
    ("Lipicure 10", "Atorvastatin"),
    ("Storvas 10", "Atorvastatin"),
    ("Rosuvas 10", "Rosuvastatin"),
    ("Concor 5", "Bisoprolol"),

    # Diabetes
    ("Glycomet 500", "Metformin"),
    ("Glucophage", "Metformin"),
    ("Okamet 500", "Metformin"),
    ("Amaryl 1mg", "Glimepiride"),
    ("Zoryl 1", "Glimepiride"),
    ("Gemcor 1", "Glimepiride"),
    ("Galvus Met", "Vildagliptin + Metformin"),
    ("Janumet", "Sitagliptin + Metformin"),
    ("Forxiga", "Dapagliflozin"),

    # Vitamins & Supplements
    ("Zincovit", "Multivitamins + Minerals"),
    ("Supradyn", "Multivitamins"),
    ("A to Z NS", "Multivitamins + Minerals"),
    ("Shelcal 500", "Calcium + Vitamin D3"),
    ("Gemcal", "Calcium + Vitamin D3"),
    ("Neurobion Forte", "Vitamin B Complex"),
    ("Becosules", "Vitamin B Complex + Vitamin C"),
    ("Evion 400", "Vitamin E"),
    ("Limcee 500", "Vitamin C (Ascorbic Acid)"),
    ("Celin 500", "Vitamin C (Ascorbic Acid)"),
    ("Dexorange", "Iron + Folic Acid + Vitamin B12"),
    ("Orofer XT", "Ferrous Ascorbate + Folic Acid"),
    
    # Miscellaneous / First Aid
    ("Betadine", "Povidone-Iodine"),
    ("Soframycin", "Framycetin Skin Cream"),
    ("Volini", "Diclofenac Gel"),
    ("Moov", "Diclofenac + Menthol"),
    ("Burnol", "Aminacrine + Cetrimide")
]

def seed_alternatives():
    with app.app_context():
        print("Starting seeding process for Medicine Alternatives...")
        added_count = 0
        skipped_count = 0
        
        for brand, generic in common_alternatives:
            # Check if this exact mapping already exists to prevent duplicates
            existing = MedicineAlternative.query.filter_by(medicine_name=brand).first()
            if not existing:
                new_alt = MedicineAlternative(
                    medicine_name=brand,
                    alternative_name=generic
                )
                db.session.add(new_alt)
                added_count += 1
            else:
                skipped_count += 1
                
        try:
            db.session.commit()
            print(f"Success Seeding Complete. Added {added_count} new alternatives. Skipped {skipped_count} existing.")
        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {e}")

if __name__ == "__main__":
    seed_alternatives()
