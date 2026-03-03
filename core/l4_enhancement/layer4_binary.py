from core.protocol_bridge import TypedBuffer, ProtocolLanguage
import numpy as np

class Layer4Binary:
    def encode(self, buffer: TypedBuffer) -> TypedBuffer:
        """Deltas → Variable-Width Bitstream"""
        # FIX: Normalize data and handle bytes/string/ndarray safely
        data = buffer.data
        if isinstance(data, bytes):
            binary_form = data
        elif isinstance(data, str):
            binary_form = data.encode('utf-8')
        elif isinstance(data, np.ndarray):
            binary_form = data.tobytes()
        else:
            binary_form = np.asarray(data, dtype=np.uint8).tobytes()
        return TypedBuffer.create(binary_form, ProtocolLanguage.L4_BIN, bytes)

    def decode(self, buffer: TypedBuffer) -> TypedBuffer:
        deltas = np.frombuffer(buffer.data, dtype=np.int16)
        return TypedBuffer.create(deltas, ProtocolLanguage.L3_DELTA, np.ndarray)
