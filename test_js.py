import re

def check_js_syntax():
    with open(r'c:\Users\eldho\Downloads\Templatefolder\templates\admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the Alpine.data block
    start_idx = content.find("Alpine.data('adminSystem'")
    if start_idx == -1:
        print("Could not find Alpine.data block")
        return

    # Extract the object definition (roughly)
    # This is a basic check focusing on where the templating engine injects data
    snippet = content[start_idx:start_idx+2000]
    
    print("--- SNIPPET AROUND DATA INJECTION ---")
    
    lines = snippet.split('\n')
    for i, line in enumerate(lines):
        if '|| []' in line or '|| 0' in line or '{{' in line:
            print(f"Line {i+1}: {line.strip()}")
            
check_js_syntax()
