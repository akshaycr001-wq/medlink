import re

def validate_script_brackets(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find the main script block
        script_pattern = re.compile(r'<script>(.*?)</script>', re.DOTALL)
        scripts = script_pattern.findall(content)
        
        for idx, script in enumerate(scripts):
            if 'Alpine.data' not in script:
                continue
            
            print(f"Validating Script Block {idx}...")
            stack = []
            pairs = {')': '(', '}': '{', ']': '['}
            
            # Simple bracket counter
            for i, char in enumerate(script):
                if char in '({[':
                    stack.append((char, i))
                elif char in ')}]':
                    if not stack:
                        print(f"Error: Unmatched closing bracket '{char}' at position {i}")
                        print(f"Context: {script[max(0, i-20):i+20]}")
                        return
                    top, pos = stack.pop()
                    if pairs[char] != top:
                        print(f"Error: Mismatched bracket '{char}' at position {i}. Expected '{pairs[char]}' to match '{top}' from position {pos}")
                        print(f"Context at error: {script[i-20:i+20]}")
                        return
            
            if stack:
                print(f"Error: {len(stack)} unclosed brackets remain:")
                for char, pos in stack:
                    print(f"- '{char}' at position {pos}")
                    print(f"  Context: {script[pos-10:pos+30]}")
                return
            
            print(f"Script Block {idx} brackets are balanced!")
            
    except Exception as e:
        print(f"Validator system error: {e}")

if __name__ == '__main__':
    validate_script_brackets('templates/admin_dashboard.html')
