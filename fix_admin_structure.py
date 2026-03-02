
import os

def fix_admin():
    path = r'templates\admin_dashboard.html'
    if not os.path.exists(path):
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the stats closing brace that closes the return object too early
    bad_stats = """        stats: {
            pharmacies: {{ pharmacies_count }},
            hospitals: {{ hospitals_count }},
            medicines: {{ medicines_count }},
            ambulances: {{ ambulances_count }}},"""
    
    good_stats = """                stats: {
                    pharmacies: {{ pharmacies_count }},
                    hospitals: {{ hospitals_count }},
                    medicines: {{ medicines_count }},
                    ambulances: {{ ambulances_count }}
                },"""
    
    content = content.replace(bad_stats, good_stats)
    
    # Ensure tabs is correctly indented and follows stats
    bad_tabs = """        tabs: ["""
    good_tabs = """                tabs: ["""
    content = content.replace(bad_tabs, good_tabs)
    
    # Fix other potentially mis-indented methods
    methods = ['init()', 'isNearExpiry', 'viewPharmacyStock', 'verifyPharma', 'deletePharma', 
               'deleteMedicine', 'deleteAmbulance', 'deleteAdmin', 'resolveSOS', 
               'openAlertModal', 'submitAlert', 'scanAndAlert']
    
    for m in methods:
        content = content.replace(f'\n        {m}', f'\n                {m}')
        content = content.replace(f'\n            {m}', f'\n                {m}')

    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print("Fixed admin structure")

fix_admin()
