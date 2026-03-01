"""
COBOL Protocol: High-performance multi-layer compression library
Native bindings for Python with L1-L8 compression layers.
"""

try:
    # Try importing the compiled Rust extension
    from .cobol_core import CobolCompressor as _RustCobolCompressor
    _has_rust_native = True
except ImportError:
    _has_rust_native = False
    _RustCobolCompressor = None


class CobolCompressor:
    """
    Python interface to COBOL Core Rust compression library.
    
    Features:
    - L1: Adaptive byte-pair encoding
    - L2: Structural XOR masking  
    - L3: Delta encoding with RLE
    
    Example:
        >>> from cobol_protocol import CobolCompressor
        >>> compressor = CobolCompressor()
        >>> compressed = compressor.compress(b"Hello World")
        >>> decompressed = compressor.decompress(compressed)
        >>> assert decompressed == b"Hello World"
    """
    
    def __init__(self, enable_l1: bool = True, enable_l2: bool = True, 
                 enable_l3: bool = True):
        """
        Initialize compressor with optional layer configuration.
        
        Args:
            enable_l1: Enable L1 layer (byte-pair encoding)
            enable_l2: Enable L2 layer (XOR masking)
            enable_l3: Enable L3 layer (delta + RLE)
        """
        self.enable_l1 = enable_l1
        self.enable_l2 = enable_l2
        self.enable_l3 = enable_l3
        
        # Use Rust native if available, otherwise prepare fallback
        if _has_rust_native:
            self._rust = _RustCobolCompressor(enable_l1, enable_l2, enable_l3)
            self._use_native = True
        else:
            self._rust = None
            self._use_native = False
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress input data through enabled layers.
        
        Args:
            data: Input bytes to compress
            
        Returns:
            Compressed bytes
            
        Raises:
            ValueError: If data is empty or invalid
            RuntimeError: If compression fails
        """
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("Data must be bytes or bytearray")
        
        if len(data) == 0:
            return b''
        
        if self._use_native and self._rust:
            result = self._rust.compress(bytes(data))
            # PyO3 may return list of u8, convert to bytes
            if isinstance(result, list):
                return bytes(result)
            return result
        else:
            # Fallback to pure Python implementation
            return self._compress_python(bytes(data))
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data through enabled layers in reverse order.
        
        Args:
            data: Input bytes to decompress
            
        Returns:
            Decompressed bytes
            
        Raises:
            ValueError: If data is empty or invalid
            RuntimeError: If decompression fails
        """
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("Data must be bytes or bytearray")
        
        if len(data) == 0:
            return b''
        
        if self._use_native and self._rust:
            result = self._rust.decompress(bytes(data))
            # PyO3 may return list of u8, convert to bytes
            if isinstance(result, list):
                return bytes(result)
            return result
        else:
            # Fallback to pure Python implementation
            return self._decompress_python(bytes(data))
    
    @staticmethod
    def _compress_python(data: bytes) -> bytes:
        """Pure Python fallback for compression."""
        import zlib
        # Simple fallback: use zlib
        return zlib.compress(data, level=9)
    
    @staticmethod
    def _decompress_python(data: bytes) -> bytes:
        """Pure Python fallback for decompression."""
        import zlib
        return zlib.decompress(data)


def is_native_available() -> bool:
    """Check if native Rust bindings are available."""
    return _has_rust_native


__all__ = [
    'CobolCompressor',
    'is_native_available',
]

__version__ = '0.1.0'
