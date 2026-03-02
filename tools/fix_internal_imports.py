#!/usr/bin/env python3
"""Auto-fix import statements in src/ to use proper namespacing.

For files within src/, converts:
  from layer5_optimized import X -> from .layer5_optimized import X
  import huffman_gpu -> from . import huffman_gpu

For relative imports (level > 0), they are left alone.
"""
import ast
import pathlib
import re

SRC = pathlib.Path('src')
src_modules = {p.stem for p in SRC.glob('*.py') if p.is_file() and p.stem != '__init__'}

def fix_imports(filepath: pathlib.Path) -> int:
    """Fix imports in a single file. Returns number of changes made."""
    text = filepath.read_text()
    original = text
    
    # Pattern 1: from module_name import (where module_name is src module)
    for mod in src_modules:
        pattern = rf'^(\s*)from\s+{re.escape(mod)}\s+import\s+'
        replacement = rf'\1from .{mod} import '
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    
    # Pattern 2: import module_name (where module_name is src module)
    for mod in src_modules:
        pattern = rf'^(\s*)import\s+{re.escape(mod)}(\s|$)'
        replacement = rf'\1from . import {mod}\2'
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    
    changes = 1 if text != original else 0
    if changes:
        filepath.write_text(text)
    return changes

fixed_files = []
total_changes = 0
for f in SRC.rglob('*.py'):
    if f.name == '__init__.py':
        continue
    changes = fix_imports(f)
    if changes:
        fixed_files.append(str(f.relative_to(SRC)))
        total_changes += 1

print(f'Fixed imports in {len(fixed_files)} files')
for fn in sorted(fixed_files):
    print(f'  - {fn}')

print(f'\nTotal files modified: {len(fixed_files)}')
