package io.cobol.core;

/**
 * Java wrapper for COBOL Core Rust compression library
 * Uses JNI (Java Native Interface) to call Rust functions
 */
public class CobolCompressor {
    // Load the native library
    static {
        System.loadLibrary("cobol_core");
    }

    // Native method declarations
    private native long createCompressor();
    private native long createCompressorWithLayers(boolean l1, boolean l2, boolean l3);
    private native void destroyCompressor(long handle);
    private native byte[] compress(long handle, byte[] data);
    private native byte[] decompress(long handle, byte[] data);

    private long handle;

    /**
     * Create a new compressor with all layers enabled
     */
    public CobolCompressor() {
        this.handle = createCompressor();
        if (this.handle == 0) {
            throw new RuntimeException("Failed to create CobolCompressor");
        }
    }

    /**
     * Create a new compressor with selective layers
     *
     * @param enableL1 Enable L1 (Byte-Pair Encoding)
     * @param enableL2 Enable L2 (XOR Masking)
     * @param enableL3 Enable L3 (Delta + RLE)
     */
    public CobolCompressor(boolean enableL1, boolean enableL2, boolean enableL3) {
        this.handle = createCompressorWithLayers(enableL1, enableL2, enableL3);
        if (this.handle == 0) {
            throw new RuntimeException("Failed to create CobolCompressor with layers");
        }
    }

    /**
     * Compress data through enabled layers
     *
     * @param data Input bytes to compress
     * @return Compressed bytes
     * @throws RuntimeException if compression fails
     */
    public byte[] compress(byte[] data) {
        if (handle == 0) {
            throw new RuntimeException("Compressor is not initialized");
        }
        if (data == null) {
            throw new IllegalArgumentException("Data cannot be null");
        }

        byte[] result = compress(handle, data);
        if (result == null) {
            throw new RuntimeException("Compression failed");
        }
        return result;
    }

    /**
     * Decompress data through enabled layers in reverse order
     *
     * @param data Input bytes to decompress
     * @return Decompressed bytes
     * @throws RuntimeException if decompression fails
     */
    public byte[] decompress(byte[] data) {
        if (handle == 0) {
            throw new RuntimeException("Compressor is not initialized");
        }
        if (data == null) {
            throw new IllegalArgumentException("Data cannot be null");
        }

        byte[] result = decompress(handle, data);
        if (result == null) {
            throw new RuntimeException("Decompression failed");
        }
        return result;
    }

    /**
     * Clean up native resources
     */
    public void close() {
        if (handle != 0) {
            destroyCompressor(handle);
            handle = 0;
        }
    }

    /**
     * Clean up resources when object is garbage collected
     */
    @Override
    protected void finalize() throws Throwable {
        close();
        super.finalize();
    }
}
