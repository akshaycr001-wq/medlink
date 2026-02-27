import re
import os

path = 'templates/pharmacy.html'
if not os.path.exists(path):
    print(f"Error: {path} not found")
    exit(1)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken inventory line
content = content.replace('inventory: {{ inventory_json | safe }', 'inventory: {{ inventory_json | safe }},')

# Fix the spaced tags
content = content.replace('{ { alerts_json | safe } }', '{{ alerts_json | safe }},')
content = content.replace('{ { emergencies_json | safe } }', '{{ emergencies_json | safe }},')

# Remove the stray closing brace if it's there
content = content.replace('        },', '')

# Ensure everything is correctly formatted
content = content.replace('inventory: {{ inventory_json | safe }},,', 'inventory: {{ inventory_json | safe }},')
content = content.replace('alerts: {{ alerts_json | safe }},,', 'alerts: {{ alerts_json | safe }},')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Pharmacy dashboard repair executed.")
