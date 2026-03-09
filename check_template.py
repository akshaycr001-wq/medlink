import sys
import json

def check_template():
    try:
        with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for unescaped quotes or invalid JS syntax around Alpine data
        start = content.find("Alpine.data('adminSystem'")
        if start == -1:
            print("Could not find Alpine.data block")
            return
            
        print("Alpine block found. Checking for syntax anomalies...")
        snippet = content[start:start+1500]
        
        # Specifically looking for missing delimiters or unclosed brackets
        for i, line in enumerate(snippet.split('\n')):
            if ('{{' in line or '||' in line or 'stats:' in line) and len(line.strip()) > 0:
                print(f"L{i}: {line.strip()}")
                
    except Exception as e:
        print(f"Error checking template: {e}")

if __name__ == '__main__':
    check_template()
