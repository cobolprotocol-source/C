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


@pytest.mark.parametrize("mode", [CompressionMode.LEGACY, CompressionMode.BRIDGE, CompressionMode.MAXIMAL])
def test_compress_decompress_roundtrip(mode):
    """Non-invasive roundtrip test: compressed -> decompressed == original.

    This test will be skipped if the chosen mode's dependencies are not available.
    """
    engine = DualModeEngine(mode)

    # Skip if required implementation not available
    if mode == CompressionMode.LEGACY and not getattr(engine, 'legacy_available', False):
        pytest.skip("Legacy layers not available")
    if mode in (CompressionMode.BRIDGE, CompressionMode.MAXIMAL) and not getattr(engine, 'bridge_available', False):
        pytest.skip("Protocol bridge not available")

    data = (b"hello deterministic world\n" * 16)

    compressed = engine.compress(data)
    decompressed = engine.decompress(compressed)

    assert decompressed == data
