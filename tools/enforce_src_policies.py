#!/usr/bin/env python3
"""Repository policy checker for /src rules.

Checks performed:
- Ensures any module under `src/algorithms/` has its top-level class name mentioned in `src/core_interfaces.py`.
- Flags imports that reference other `src` modules without the `src.` namespace.
- Flags classes with more than 12 methods (recommend splitting).

Exit code 0 when no issues found; 2 when issues exist.
"""
import ast
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
CORE_IFACE = SRC / 'core_interfaces.py'
ALG_DIR = SRC / 'algorithms'

issues = []

# Helper: parse all project-level modules (names present in src/)
src_modules = set()
for p in SRC.iterdir():
    if p.is_file() and p.suffix == '.py':
        src_modules.add(p.stem)
    if p.is_dir():
        src_modules.add(p.name)

# 1) Check src/algorithms registration
alg_classes = defaultdict(list)
if ALG_DIR.exists():
    for f in ALG_DIR.rglob('*.py'):
        try:
            tree = ast.parse(f.read_text())
        except Exception:
            continue
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                alg_classes[f.relative_to(SRC).as_posix()].append(node.name)

    if alg_classes:
        core_text = CORE_IFACE.read_text() if CORE_IFACE.exists() else ''
        for fname, classes in alg_classes.items():
            for cname in classes:
                if cname not in core_text:
                    issues.append(f"Algorithm class {cname} in {fname} not referenced in src/core_interfaces.py")
else:
    print('Note: src/algorithms not present; skipping registration checks')

# 2) Check imports that reference src modules without src. prefix
for f in SRC.rglob('*.py'):
    try:
        tree = ast.parse(f.read_text())
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mod = n.name.split('.')[0]
                if mod in src_modules and not n.name.startswith('src.'):
                    # allow relative imports (from . import ...)
                    issues.append(f"File {f.relative_to(ROOT)}: top-level import '{n.name}' should import 'src.{n.name}' instead of bare '{n.name}'")
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            mod = node.module.split('.')[0]
            # relative imports (module starting with '.') are ok
            if not node.module.startswith('src') and mod in src_modules and not node.level:
                issues.append(f"File {f.relative_to(ROOT)}: from-import '{node.module}' should use 'src.{node.module}' or relative import")

# 3) Flag classes with >12 methods
for f in SRC.rglob('*.py'):
    try:
        tree = ast.parse(f.read_text())
    except Exception:
        continue
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            method_count = sum(1 for b in node.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)))
            if method_count > 12:
                issues.append(f"Class {node.name} in {f.relative_to(ROOT)} has {method_count} methods (>{12}) — consider splitting into components/strategies")

# Print report
if not issues:
    print('Policy check passed — no issues found.')
    sys.exit(0)

print('Policy check found issues:')
for it in issues:
    print('- ' + it)

# exit non-zero to indicate failing policy
sys.exit(2)
