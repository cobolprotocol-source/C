package io.cobol.core;

import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Unit tests for CobolCompressor JNI wrapper
 */
public class CobolCompressorTest {

    @Test
    public void testBasicCompression() {
        CobolCompressor compressor = new CobolCompressor();
        byte[] originalData = "Hello World!".getBytes();
        byte[] compressed = compressor.compress(originalData);

        assertNotNull("Compressed data should not be null", compressed);
        assertTrue("Compressed data should not be empty", compressed.length > 0);

        compressor.close();
    }

    @Test
    public void testRoundtrip() {
        CobolCompressor compressor = new CobolCompressor();
        byte[] originalData = "The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.".getBytes();

        byte[] compressed = compressor.compress(originalData);
        byte[] decompressed = compressor.decompress(compressed);

        assertArrayEquals("Decompressed data should match original", originalData, decompressed);

        compressor.close();
    }

    @Test
    public void testSelectiveLayersL1Only() {
        CobolCompressor compressor = new CobolCompressor(true, false, false);
        byte[] data = "test data test data test data".getBytes();

        byte[] compressed = compressor.compress(data);
        byte[] decompressed = compressor.decompress(compressed);

        assertArrayEquals("L1 only roundtrip should be lossless", data, decompressed);

        compressor.close();
    }

    @Test
    public void testSelectiveLayersL2Only() {
        CobolCompressor compressor = new CobolCompressor(false, true, false);
        byte[] data = "test data test data test data".getBytes();

        byte[] compressed = compressor.compress(data);
        byte[] decompressed = compressor.decompress(compressed);

        assertArrayEquals("L2 only roundtrip should be lossless", data, decompressed);

        compressor.close();
    }

    @Test
    public void testSelectiveLayersL3Only() {
        CobolCompressor compressor = new CobolCompressor(false, false, true);
        byte[] data = "test data test data test data".getBytes();

        byte[] compressed = compressor.compress(data);
        byte[] decompressed = compressor.decompress(compressed);

        assertArrayEquals("L3 only roundtrip should be lossless", data, decompressed);

        compressor.close();
    }

    @Test(expected = IllegalArgumentException.class)
    public void testCompressNull() {
        CobolCompressor compressor = new CobolCompressor();
        compressor.compress(null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void testDecompressNull() {
        CobolCompressor compressor = new CobolCompressor();
        compressor.decompress(null);
    }

    @Test
    public void testAutoCloseable() {
        try (CobolCompressor compressor = new CobolCompressor()) {
            byte[] data = "test".getBytes();
            byte[] compressed = compressor.compress(data);
            byte[] decompressed = compressor.decompress(compressed);
            assertArrayEquals("Should work with try-with-resources", data, decompressed);
        }
    }
}
