"""Layer 6: GPU Acceleration utilities (backward-compatible stub).

The real implementation resides in ``core/l6_deep``; during the
restructuring we provide a lightweight CPU-only fallback so that tests
that import these names continue to run without requiring GPU
dependencies.
"""

# cuPy support flag (tests may skip GPU-specific checks)
CUPY_AVAILABLE = False

class GPUPatternMatcher:
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu

    def find_patterns_gpu(self, data: bytes, pattern_size: int = 3):
        # simple CPU-based pattern counting
        from collections import Counter
        patterns = Counter()
        for i in range(len(data) - pattern_size + 1):
            patterns[data[i : i + pattern_size]] += 1
        return patterns

class GPUAcceleratedLayer6:
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu

    def encode_gpu(self, data: bytes) -> bytes:
        # identity encode
        return data

    def decode_gpu(self, data: bytes) -> bytes:
        # identity decode
        return data

__all__ = ["GPUAcceleratedLayer6", "GPUPatternMatcher", "CUPY_AVAILABLE"]
