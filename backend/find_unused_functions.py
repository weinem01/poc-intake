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
    if not external_calls:
        unused_functions.append((func_name, def_file, def_line))

print('UNUSED FUNCTIONS:')
print('================')
for func_name, filepath, line_num in sorted(unused_functions):
    print(f'{func_name} - {filepath}:{line_num}')

print(f'\nTotal functions found: {len(function_defs)}')
print(f'Unused functions: {len(unused_functions)}')

# Also show functions with calls for verification
print('\nFUNCTIONS WITH CALLS:')
print('====================')
for func_name, def_file, def_line in sorted(function_defs):
    calls = function_calls.get(func_name, [])
    external_calls = [call for call in calls if call[0] != def_file]
    if external_calls:
        print(f'{func_name} - {def_file}:{def_line} - called {len(external_calls)} times')