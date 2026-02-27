import re

path = 'templates/admin_dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix triple braces that might have been created by previous run
content = content.replace('}}}', '}}')

# Ensure all JS object properties ending in }} are followed by a comma or newline correctly
# and don't have stray }
content = re.sub(r'\}\} \},', '}},', content)
content = re.sub(r'\}\} \}', '}}', content)

# One more pass to catch any single } that are still alone after {{
content = re.sub(r'(\{\{.*?)\}(?!\})', r'\1}}', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Refined repair script executed.")
