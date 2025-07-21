#!/usr/bin/env python3
import re
import os

# Get all function definitions
function_defs = []
function_calls = {}

# First pass: extract all function definitions
for root, dirs, files in os.walk('.'):
    if '.venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        # Match function definitions
                        match = re.match(r'^(async )?def (\w+)', line.strip())
                        if match:
                            func_name = match.group(2)
                            function_defs.append((func_name, filepath, i))
                            function_calls[func_name] = []
            except Exception as e:
                print(f'Error reading {filepath}: {e}')

# Second pass: find function calls
for root, dirs, files in os.walk('.'):
    if '.venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        for func_name, _, _ in function_defs:
                            # Look for function calls (not definitions)
                            if func_name in line and not re.match(r'^(async )?def ' + func_name, line.strip()):
                                # Check if it's a function call pattern
                                if re.search(r'\b' + func_name + r'\s*\(', line):
                                    function_calls[func_name].append((filepath, i))
            except Exception as e:
                print(f'Error reading {filepath}: {e}')

# Find unused functions
unused_functions = []
for func_name, def_file, def_line in function_defs:
    calls = function_calls.get(func_name, [])
    # Filter out self-references (definition file)
    external_calls = [call for call in calls if call[0] != def_file]
    
    # Skip __init__ methods and test functions for this analysis
    if func_name == '__init__':
        continue
    if func_name.startswith('test_'):
        continue
    if 'main' in func_name and 'tests/' in def_file:
        continue
    if 'run_' in func_name and 'tests/' in def_file:
        continue
        
    if not external_calls:
        unused_functions.append((func_name, def_file, def_line))

print('POTENTIALLY UNUSED FUNCTIONS:')
print('============================')
print('These functions are defined but not called from other files:')
print()

# Group by category for better readability
categories = {
    'Private/Helper Functions': [],
    'Service Functions': [],
    'Repository Functions': [],
    'Router Functions': [],
    'Core Functions': [],
    'Script Functions': [],
    'Other': []
}

for func_name, filepath, line_num in sorted(unused_functions):
    if func_name.startswith('_'):
        categories['Private/Helper Functions'].append((func_name, filepath, line_num))
    elif '/services/' in filepath:
        categories['Service Functions'].append((func_name, filepath, line_num))
    elif '/repositories/' in filepath:
        categories['Repository Functions'].append((func_name, filepath, line_num))
    elif '/routers/' in filepath:
        categories['Router Functions'].append((func_name, filepath, line_num))
    elif '/core/' in filepath:
        categories['Core Functions'].append((func_name, filepath, line_num))
    elif '/scripts/' in filepath:
        categories['Script Functions'].append((func_name, filepath, line_num))
    else:
        categories['Other'].append((func_name, filepath, line_num))

for category, functions in categories.items():
    if functions:
        print(f'{category}:')
        print('-' * len(category))
        for func_name, filepath, line_num in functions:
            print(f'  • {func_name}() - {filepath}:{line_num}')
        print()

print(f'Total unused functions (excluding __init__ and tests): {len(unused_functions)}')
print(f'Total functions analyzed: {len([f for f in function_defs if f[0] != "__init__" and not f[0].startswith("test_")])}')