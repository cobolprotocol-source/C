import hashlib
import importlib.util
import sys
import pathlib
import pytest

# Load DualModeEngine directly to avoid importing package `src` which triggers
# heavy imports in package __init__ (non-invasive test helper).
spec = importlib.util.spec_from_file_location(
    "dual_mode_engine", str(pathlib.Path(__file__).resolve().parents[1] / "src" / "dual_mode_engine.py")
)
dual_mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dual_mod
spec.loader.exec_module(dual_mod)

DualModeEngine = dual_mod.DualModeEngine
CompressionMode = dual_mod.CompressionMode


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@pytest.mark.parametrize("repeats", [2, 3])
def test_repeated_roundtrip_consistency(repeats):
    """Run compress->decompress repeatedly and ensure output is stable.

    Non-invasive: only asserts decompressed == original for multiple runs.
    """
    mode = CompressionMode.LEGACY
    engine = DualModeEngine(mode)

    if not getattr(engine, 'legacy_available', False):
        pytest.skip("Legacy layers not available for determinism audit")

    original = b"determinism-audit-sample-data\n" * 32
    baseline_hash = None

    for _ in range(repeats):
        comp = engine.compress(original)
        decomp = engine.decompress(comp)
        assert decomp == original
        h = _sha256(decomp)
        if baseline_hash is None:
            baseline_hash = h
        else:
            assert h == baseline_hash
