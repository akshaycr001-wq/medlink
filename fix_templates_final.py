
import os
import re

def fix_file(path, replacements):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Also handle the "{ {" and " } }" patterns with regex
    content = re.sub(r'\{\s+\{', '{{', content)
    content = re.sub(r'\}\s+\}', '}}', content)
    
    if content != original_content:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        print(f"Fixed: {path}")
    else:
        print(f"No changes needed for: {path}")

# Pharmacy replacements
pharmacy_path = r'templates\pharmacy.html'
pharmacy_reps = [
    ('inventory: {{ inventory_json | safe }\n        },', 'inventory: {{ inventory_json | safe }},\n                emergencies: {{ emergencies_json | safe }}.map(e => ({'),
    ('emergencies: {{ emergencies_json | safe }}.map(e => ({', 'emergencies: {{ emergencies_json | safe }}.map(e => ({'),
]

# Admin replacements
admin_path = r'templates\admin_dashboard.html'
admin_reps = [
    ('pharmacies: {{ pharmacies_json | safe }\n        },', 'pharmacies: {{ pharmacies_json | safe }},'),
]

fix_file(pharmacy_path, pharmacy_reps)
fix_file(admin_path, admin_reps)
