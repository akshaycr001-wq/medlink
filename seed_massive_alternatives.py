import sys
sys.path.append(r"c:\Users\eldho\Downloads\Templatefolder")
from app import app, db
from models import MedicineAlternative

# A massive, comprehensive list of common Indian medicines (Brand -> Generic)
# Compiled from pharmaceutical databases for MedLink search mapping.
massive_alternatives = [
    # Analgesics & Painkillers
    ("Dolo 650", "Paracetamol"),
    ("Calpol 500", "Paracetamol"),
    ("Crocin Advance", "Paracetamol"),
    ("Combiflam", "Ibuprofen + Paracetamol"),
    ("Flexon", "Ibuprofen + Paracetamol"),
    ("Brufen 400", "Ibuprofen"),
    ("Meftal Spas", "Mefenamic Acid + Dicyclomine"),
    ("Zerodol P", "Aceclofenac + Paracetamol"),
    ("Zerodol SP", "Aceclofenac + Serratiopeptidase + Paracetamol"),
    ("Aldigesic P", "Aceclofenac + Paracetamol"),
    ("Aldigesic SP", "Aceclofenac + Serratiopeptidase + Paracetamol"),
    ("Voveran SR 100", "Diclofenac"),
    ("Voveran 50", "Diclofenac"),
    ("Reactin SR", "Diclofenac"),
    ("Nise", "Nimesulide"),
    ("Sumo", "Nimesulide + Paracetamol"),
    ("Nimulid", "Nimesulide"),
    ("Novamin", "Prochlorperazine"),
    ("Ultracet", "Tramadol + Paracetamol"),
    ("Ketorol DT", "Ketorolac"),
    ("Dolokind Plus", "Aceclofenac + Paracetamol"),
    ("Hifenac P", "Aceclofenac + Paracetamol"),
    ("Signoflam", "Aceclofenac + Paracetamol + Serratiopeptidase"),

    # Antacids, Ulcer, Digestion
    ("Omez 20", "Omeprazole"),
    ("Omecip 20", "Omeprazole"),
    ("Pan 40", "Pantoprazole"),
    ("Pantocid 40", "Pantoprazole"),
    ("Pantosec", "Pantoprazole"),
    ("Pan D", "Pantoprazole + Domperidone"),
    ("Pantocid DSR", "Pantoprazole + Domperidone"),
    ("Pantop D", "Pantoprazole + Domperidone"),
    ("Rantac 150", "Ranitidine"),
    ("Aciloc 150", "Ranitidine"),
    ("Zinetac", "Ranitidine"),
    ("Rabium 20", "Rabeprazole"),
    ("Rablet 20", "Rabeprazole"),
    ("Rabemac 20", "Rabeprazole"),
    ("Rabium DSR", "Rabeprazole + Domperidone"),
    ("Domstal", "Domperidone"),
    ("Econorm", "Saccharomyces Boulardii"),
    ("Enterogermina", "Bacillus Clausii"),
    ("Vomitrol", "Ondansetron"),
    ("Ondem 4", "Ondansetron"),
    ("Ondem MD 4", "Ondansetron"),
    ("Zofer", "Ondansetron"),
    ("Digene", "Magaldrate + Simethicone"),
    ("Gelusil", "Aluminum Hydroxide + Magnesium + Simethicone"),
    ("Mucaine Gel", "Oxethazaine + Aluminum Hydroxide + Magnesium"),
    ("Polycrol", "Magaldrate + Simethicone"),
    ("Cremaffin", "Liquid Paraffin + Milk of Magnesia"),
    ("Dulcolax", "Bisacodyl"),

    # Antibiotics (Broad Spectrum)
    ("Augmentin 625 Duo", "Amoxicillin + Clavulanic Acid"),
    ("Moxikind CV 625", "Amoxicillin + Clavulanic Acid"),
    ("Clavam 625", "Amoxicillin + Clavulanic Acid"),
    ("Advent 625", "Amoxicillin + Clavulanic Acid"),
    ("Novamox 500", "Amoxicillin"),
    ("Taxim O 200", "Cefixime"),
    ("Zifi 200", "Cefixime"),
    ("Mahacef 200", "Cefixime"),
    ("Cefolac 200", "Cefixime"),
    ("Omnicef O", "Cefixime"),
    ("Azithral 500", "Azithromycin"),
    ("Azee 500", "Azithromycin"),
    ("Zithrox 500", "Azithromycin"),
    ("Cepodem 200", "Cefpodoxime"),
    ("Monocef O 200", "Cefpodoxime"),
    ("Oflomac 200", "Ofloxacin"),
    ("Zanocin 200", "Ofloxacin"),
    ("Norflox TZ", "Norfloxacin + Tinidazole"),
    ("Norflox 400", "Norfloxacin"),
    ("Metrogyl 400", "Metronidazole"),
    ("Flagyl 400", "Metronidazole"),
    ("Ciprobid 500", "Ciprofloxacin"),
    ("Ciplox 500", "Ciprofloxacin"),
    ("Levomac 500", "Levofloxacin"),
    ("Loxof 500", "Levofloxacin"),
    ("Doxy 1", "Doxycycline"),

    # Cough & Cold, Allergies
    ("Allegra 120", "Fexofenadine"),
    ("Allegra 180", "Fexofenadine"),
    ("Avil 25", "Pheniramine Maleate"),
    ("Okacet", "Cetirizine"),
    ("Cetzine", "Cetirizine"),
    ("Alerid", "Cetirizine"),
    ("Levocet M", "Levocetirizine + Montelukast"),
    ("Montair LC", "Levocetirizine + Montelukast"),
    ("Telekast L", "Levocetirizine + Montelukast"),
    ("Montelekast", "Montelukast"),
    ("Sinarest", "Paracetamol + Phenylephrine + Chlorpheniramine"),
    ("Wikoryl", "Paracetamol + Phenylephrine + Chlorpheniramine"),
    ("Cheston Cold", "Cetirizine + Paracetamol + Phenylephrine"),
    ("Maxtra", "Phenylephrine + Chlorpheniramine"),
    ("Alex Syrup", "Dextromethorphan + Chlorpheniramine"),
    ("Benadryl Cough", "Diphenhydramine + Ammonium Chloride"),
    ("Corex DX", "Dextromethorphan + Chlorpheniramine"),
    ("Ascoril LS", "Ambroxol + Levosalbutamol + Guaiphenesin"),
    ("Ascoril D Plus", "Dextromethorphan + Chlorpheniramine + Phenylephrine"),
    ("Grilinctus", "Dextromethorphan + Chlorpheniramine + Guaifenesin"),
    ("Asthalin", "Salbutamol"),
    ("Deriphyllin", "Etofylline + Theophylline"),

    # Cardiovascular & Blood Pressure
    ("Amlokind 5", "Amlodipine"),
    ("Amlong 5", "Amlodipine"),
    ("Stamlo 5", "Amlodipine"),
    ("Telmikind 40", "Telmisartan"),
    ("Telvas 40", "Telmisartan"),
    ("Cresar 40", "Telmisartan"),
    ("Telma 40", "Telmisartan"),
    ("Tazloc 40", "Telmisartan"),
    ("Telmikind H", "Telmisartan + Hydrochlorothiazide"),
    ("Telma H", "Telmisartan + Hydrochlorothiazide"),
    ("Losar 50", "Losartan"),
    ("Repace 50", "Losartan"),
    ("Losar H", "Losartan + Hydrochlorothiazide"),
    ("Ecosprin 75", "Aspirin"),
    ("Ecosprin 150", "Aspirin"),
    ("Atorva 10", "Atorvastatin"),
    ("Atorva 20", "Atorvastatin"),
    ("Lipicure 10", "Atorvastatin"),
    ("Storvas 10", "Atorvastatin"),
    ("Rosuvas 10", "Rosuvastatin"),
    ("Rozavel 10", "Rosuvastatin"),
    ("Concor 5", "Bisoprolol"),
    ("Inderal 10", "Propranolol"),
    ("Ciplar 10", "Propranolol"),

    # Diabetes
    ("Glycomet 500", "Metformin"),
    ("Glycomet 500 SR", "Metformin"),
    ("Glucophage 500", "Metformin"),
    ("Okamet 500", "Metformin"),
    ("Amaryl 1mg", "Glimepiride"),
    ("Amaryl 2mg", "Glimepiride"),
    ("Zoryl 1", "Glimepiride"),
    ("Zoryl M1", "Glimepiride + Metformin"),
    ("Amaryl M1", "Glimepiride + Metformin"),
    ("Gemcor 1", "Glimepiride"),
    ("Galvus Met 50/500", "Vildagliptin + Metformin"),
    ("Janumet 50/500", "Sitagliptin + Metformin"),
    ("Forxiga 10mg", "Dapagliflozin"),
    ("Jardiance 10mg", "Empagliflozin"),
    ("Trajenta 5mg", "Linagliptin"),

    # Vitamins, Supplements, Blood Builders
    ("Zincovit", "Multivitamins + Minerals"),
    ("Supradyn", "Multivitamins"),
    ("A to Z NS", "Multivitamins + Minerals"),
    ("Maxirich", "Multivitamins"),
    ("Revital H", "Multivitamins + Ginseng"),
    ("Shelcal 500", "Calcium + Vitamin D3"),
    ("Gemcal", "Calcium + Vitamin D3"),
    ("Calcimax 500", "Calcium + Vitamin D3"),
    ("Uprise D3 60K", "Cholecalciferol (Vitamin D3)"),
    ("Calcirol", "Cholecalciferol (Vitamin D3)"),
    ("Neurobion Forte", "Vitamin B Complex"),
    ("Becosules", "Vitamin B Complex + Vitamin C"),
    ("Evion 400", "Vitamin E"),
    ("Limcee 500", "Vitamin C (Ascorbic Acid)"),
    ("Celin 500", "Vitamin C (Ascorbic Acid)"),
    ("Dexorange", "Iron + Folic Acid + Vitamin B12"),
    ("Orofer XT", "Ferrous Ascorbate + Folic Acid"),
    ("Livogen", "Iron + Folic Acid"),
    ("Folvite 5mg", "Folic Acid"),

    # Thyroid & Hormones
    ("Thyronorm 50", "Thyroxine Sodium"),
    ("Eltroxin 50", "Thyroxine Sodium"),
    ("Thyrox 50", "Thyroxine Sodium"),
    ("Susten 200", "Progesterone"),
    ("Duphaston 10mg", "Dydrogesterone"),
    ("Crimson 35", "Cyproterone + Ethinyl Estradiol"),
    ("Meche 500", "Methylcobalamin"),
    ("Nurokind OD", "Methylcobalamin"),

    # Dermatological, Creams, Ointments
    ("Betadine", "Povidone-Iodine"),
    ("Soframycin", "Framycetin Skin Cream"),
    ("Volini", "Diclofenac Gel"),
    ("Moov", "Diclofenac + Menthol"),
    ("Omnigel", "Diclofenac + Linseed Oil + Menthol + Methyl Salicylate"),
    ("Burnol", "Aminacrine + Cetrimide"),
    ("Candid", "Clotrimazole"),
    ("Surfaz SN", "Clotrimazole + Beclometasone + Neomycin"),
    ("Quadriderm", "Betamethasone + Clioquinol + Gentamicin + Tolnaftate"),
    ("T-Bact", "Mupirocin"),
    ("Bactroban", "Mupirocin"),
    ("Dermikem OC", "Clobetasol + Neomycin + Miconazole"),
    ("Betnovate C", "Betamethasone + Clioquinol"),
    ("Betnovate N", "Betamethasone + Neomycin"),

    # Anti-fungal & Infections
    ("Fluconazole 150", "Fluconazole"),
    ("Zocon 150", "Fluconazole"),
    ("Forcan 150", "Fluconazole"),
    ("Canditral 100", "Itraconazole"),
    ("Itra 100", "Itraconazole"),
    ("Terbinaforce 250", "Terbinafine"),
    
    # Neurology & Psychiatry
    ("Alprax 0.25", "Alprazolam"),
    ("Alprax 0.5", "Alprazolam"),
    ("Restyl 0.25", "Alprazolam"),
    ("Ativan 1mg", "Lorazepam"),
    ("Lopez 1mg", "Lorazepam"),
    ("Clonotril 0.5", "Clonazepam"),
    ("Nexito 10", "Escitalopram"),
    ("Nexito Plus", "Escitalopram + Clonazepam"),
    ("Zolfresh 10", "Zolpidem"),
    ("Dilantin 100", "Phenytoin"),
    ("Eptoin 100", "Phenytoin"),
    ("Tegrital 200", "Carbamazepine"),
    ("Zeptol 200", "Carbamazepine"),

    # Ophthalmic & Ear
    ("Refresh Tears", "Carboxymethylcellulose Ophthalmic"),
    ("Systane Ultra", "Polyethylene Glycol + Propylene Glycol Ophthalmic"),
    ("Moxicip Eye Drop", "Moxifloxacin Ophthalmic"),
    ("Mahaflox Eye Drop", "Moxifloxacin Ophthalmic"),
    ("Ciplox Eye/Ear Drops", "Ciprofloxacin Ophthalmic"),
    ("Otrivin Adult", "Xylometazoline"),
    ("Nasivion", "Oxymetazoline"),

    # Steroids
    ("Wysolone 5", "Prednisolone"),
    ("Omnacortil 5", "Prednisolone"),
    ("Dexona", "Dexamethasone"),
    ("Defza 6", "Deflazacort"),

    # Others
    ("Vertin 16", "Betahistine"),
    ("Stugeron 25", "Cinnarizine"),
    ("Stemetil MD", "Prochlorperazine"),
    ("Lasix 40", "Furosemide"),
    ("Aldactone 25", "Spironolactone")
]

def seed_alternatives():
    with app.app_context():
        print(f"Starting seeding process for {len(massive_alternatives)} massive Medicine Alternatives...")
        added_count = 0
        skipped_count = 0
        
        # Build existing dict to significantly speed up
        existing = {m.medicine_name.lower() for m in MedicineAlternative.query.all()}
        
        batch = []
        for brand, generic in massive_alternatives:
            # Check if this exact mapping already exists to prevent duplicates (case insensitive)
            if brand.lower() not in existing:
                new_alt = MedicineAlternative(
                    medicine_name=brand,
                    alternative_name=generic
                )
                batch.append(new_alt)
                existing.add(brand.lower())
                added_count += 1
            else:
                skipped_count += 1
                
        try:
            if batch:
                db.session.bulk_save_objects(batch)
                db.session.commit()
            print(f"Seeding Complete. Added {added_count} new alternatives. Skipped {skipped_count} existing.")
        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {e}")

if __name__ == "__main__":
    seed_alternatives()
