from core.protocol_bridge import TypedBuffer, ProtocolLanguage
import numpy as np

class Layer3Delta:
    def encode(self, buffer: TypedBuffer) -> TypedBuffer:
        """Schema_IDs → Signed_Delta_Integers"""
        # FIX: Ensure buffer.data is ndarray-like before np.diff()
        data = buffer.data
        if isinstance(data, bytes):
            data = np.frombuffer(data, dtype=np.uint8)
        elif isinstance(data, str):
            data = np.array([ord(c) % 256 for c in data], dtype=np.uint8)
        elif not isinstance(data, np.ndarray):
            data = np.asarray(data, dtype=np.uint8)
        # flatten multi-dimensional
        if data.ndim > 1:
            data = data.flatten()
        deltas = np.diff(data, prepend=0).astype(np.int16)
        return TypedBuffer.create(deltas, ProtocolLanguage.L3_DELTA, np.ndarray)

    def decode(self, buffer: TypedBuffer) -> TypedBuffer:
        # mirror encode normalization
        data = buffer.data
        if isinstance(data, bytes):
            data = np.frombuffer(data, dtype=np.int16)
        elif not isinstance(data, np.ndarray):
            data = np.asarray(data, dtype=np.int16)
        schema_ids = np.cumsum(data).astype(np.uint16)
        return TypedBuffer.create(schema_ids, ProtocolLanguage.L2_STRUCT, np.ndarray)
