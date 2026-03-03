from .gpu_acceleration import GPUTrieAccelerator, GPUDetector
import logging
from .protocol_bridge import TypedBuffer, ProtocolLanguage
import numpy as np

class Layer6Recursive:
    def encode(self, buffer: TypedBuffer) -> TypedBuffer:
        # Integrasi akselerasi GPU untuk pencarian pola pada Layer 6
        detector = GPUDetector()
        accelerator = GPUTrieAccelerator(detector)
        # FIX: Normalize input data types to ndarray before any operations
        data = buffer.data
        if isinstance(data, bytes):
            norm_data = np.frombuffer(data, dtype=np.uint8)
        elif isinstance(data, str):
            norm_data = np.array([ord(c) % 256 for c in data], dtype=np.uint8)
        elif isinstance(data, np.ndarray):
            norm_data = data
        else:
            norm_data = np.asarray(data)
        patterns = {}  # Patterns dapat diisi sesuai kebutuhan aplikasi
        try:
            if detector.gpu_available:
                matches = accelerator.search_patterns_gpu(norm_data, patterns)
                logging.info(f"Layer6Recursive: GPU acceleration active, matches={len(matches)}")
            else:
                matches = []
                logging.info("Layer6Recursive: GPU not available, fallback to CPU")
        except Exception as e:
            matches = []
            logging.warning(f"Layer6Recursive: GPU acceleration error: {e}")
        # Dummy: apply numeric offset (use wider integer to avoid overflow)
        if not isinstance(norm_data, np.ndarray) or norm_data.dtype == np.uint8:
            # promote to signed 32-bit for arithmetic
            norm_array = np.asarray(norm_data, dtype=np.int32)
        else:
            norm_array = norm_data.astype(np.int32)
        nested = norm_array + 1000
        return TypedBuffer.create(nested, ProtocolLanguage.L6_PTR, np.ndarray)

    def decode(self, buffer: TypedBuffer) -> TypedBuffer:
        # Only one decode method, operate on ndarray
        data = buffer.data
        if isinstance(data, np.ndarray):
            pointers = data - 1000
        else:
            pointers = data
        return TypedBuffer.create(pointers, ProtocolLanguage.L5_TRIE, np.ndarray)
