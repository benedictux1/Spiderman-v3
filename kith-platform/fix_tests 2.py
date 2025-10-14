#!/usr/bin/env python3
"""
Script to fix test files by removing incorrect patches and updating fixtures
"""

import re
import sys

def fix_test_file(filepath):
    """Fix a test file by removing incorrect patches and updating fixtures"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace authenticated_user with authenticated_admin_user in test methods that have patches
    # This is a more targeted approach
    
    # Pattern to match test methods that use authenticated_user and have patches
    pattern = r'def (test_\w+)\(self, client, authenticated_user\):\s*\n(.*?)(\s+with patch\(\'app\.is_admin\', return_value=True\):\s*\n.*?)(\s+def|\s*$)'
    
    def replace_func(match):
        test_name = match.group(1)
        docstring_and_other = match.group(2)
        patch_block = match.group(3)
        next_def = match.group(4)
        
        # Remove the patch block and fix indentation
        lines = patch_block.split('\n')
        fixed_lines = []
        for line in lines:
            if 'with patch(' in line:
                continue
            elif line.strip().startswith('response =') or line.strip().startswith('assert'):
                # Remove extra indentation
                fixed_lines.append(line[4:])  # Remove 4 spaces
            elif line.strip() == '':
                fixed_lines.append('')
            else:
                fixed_lines.append(line)
        
        # Join the fixed content
        fixed_patch_block = '\n'.join(fixed_lines).strip()
        
        return f'def {test_name}(self, client, authenticated_admin_user):\n{docstring_and_other}{fixed_patch_block}\n{next_def}'
    
    # Apply the fix
    content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filepath}")

if __name__ == "__main__":
    files_to_fix = [
        "tests/integration/test_admin_dashboard.py",
        "tests/integration/test_csv_import_export.py"
    ]
    
    for filepath in files_to_fix:
        try:
            fix_test_file(filepath)
        except Exception as e:
            print(f"❌ Error fixing {filepath}: {e}")
