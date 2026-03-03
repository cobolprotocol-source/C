from core.protocol_bridge import TypedBuffer, ProtocolLanguage
import numpy as np

class Layer1Semantic:
    def encode(self, buffer: TypedBuffer) -> TypedBuffer:
        """Raw text -> Semantic tokens (np.uint8 array)"""
        # FIX: Add type guard for input normalization
        data = buffer.data
        if isinstance(data, np.ndarray):
            # if array, try decode to string
            try:
                data = data.tobytes().decode('utf-8')
            except Exception:
                # fallback: convert each element to char
                data = ''.join(chr(int(x) % 256) for x in data)
        tokens = np.array([ord(c) % 256 for c in str(data)], dtype=np.uint8)
        return TypedBuffer.create(tokens, ProtocolLanguage.L1_SEM, np.ndarray)

    def decode(self, buffer: TypedBuffer) -> TypedBuffer:
        """Semantic tokens -> Text"""
        # FIX: Normalize input before constructing text
        data = buffer.data
        if isinstance(data, bytes):
            data = np.frombuffer(data, dtype=np.uint8)
        elif isinstance(data, str):
            data = np.array([ord(c) % 256 for c in data], dtype=np.uint8)
        text = ''.join([chr(int(t) % 256) for t in data])
        return TypedBuffer.create(text, ProtocolLanguage.L1_SEM, str)
