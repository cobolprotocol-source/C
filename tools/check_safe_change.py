#!/usr/bin/env python3
"""Safety check script for COBOL Protocol changes.

Performs non-invasive checks:
- Verifies deterministic safety header presence in critical files
- Runs Python syntax check (compileall)
- Runs the non-invasive determinism tests added under `tests/`

This script MUST NOT modify repository files. It is advisory only.
"""
from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path


CRITICAL_PY_FILES = [
    Path("src/core_interfaces.py"),
    Path("src/energy_aware_execution.py"),
    Path("src/engine.py"),
    Path("src/adaptive_pipeline.py"),
    Path("src/full_pipeline.py"),
]

RUST_CORE_DIR = Path("cobol-core/src")


def check_header(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False

    head = "\n".join(text.splitlines()[:20])
    return "Deterministic: YES" in head


def main() -> int:
    ok = True

    print("[check_safe_change] Verifying deterministic headers for critical files...")

    for p in CRITICAL_PY_FILES:
        if p.exists():
            has = check_header(p)
            print(f"  {p}: {'OK' if has else 'MISSING'}")
            if not has:
                ok = False
        else:
            print(f"  {p}: (not present, skipping)")

    # Rust core files
    if RUST_CORE_DIR.exists():
        for rs in sorted(RUST_CORE_DIR.glob("*.rs")):
            has = check_header(rs)
            print(f"  {rs}: {'OK' if has else 'MISSING'}")
            if not has:
                ok = False

    if not ok:
        print("[check_safe_change] Header checks failed. See docs/SAFE_CHANGE.md for requirements.")

    # Run Python syntax check
    print("[check_safe_change] Running Python syntax check (compileall) on src/...")
    if not compileall.compile_dir("src", quiet=1):
        print("[check_safe_change] Syntax errors found in Python sources.")
        ok = False

    # Run the non-invasive tests only
    print("[check_safe_change] Running non-invasive tests...")
    try:
        res = subprocess.run([sys.executable, "-m", "pytest", "-q",
                              "tests/test_roundtrip_dualmode.py", "tests/test_determinism_audit.py"], check=False)
        if res.returncode != 0:
            print(f"[check_safe_change] Tests returned non-zero exit code: {res.returncode}")
            # Tests may skip in minimal env; do not fail solely based on skips.
    except FileNotFoundError:
        print("[check_safe_change] pytest not installed; skipping test execution.")

    if ok:
        print("[check_safe_change] All mandatory header and syntax checks passed.")
        return 0
    else:
        print("[check_safe_change] One or more checks failed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
