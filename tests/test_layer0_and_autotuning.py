import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.layer0_classifier import Layer0Classifier, DataType
from src.auto_tuner import AutoTuner


def test_classifier_source_code():
    """Test detection of source code (or similar text)."""
    # C code sample - compact
    data = b"int x=0;int y=x+1;for(int i=0;i<10;i++){x+=i;}return x;" * 100
    
    classifier = Layer0Classifier()
    result = classifier.classify(data)
    
    # Should be text-like (source code or text document)
    assert result.printable_ratio > 0.85
    assert result.entropy < 4.5
    assert result.data_type in (DataType.SOURCE_CODE, DataType.TEXT_DOCUMENT)


def test_classifier_binary_log():
    """Test detection of binary logs."""
    # Simulate binary log with mixed printable/non-printable
    data = b"\x00\x01\x02timestamp:\x00\x04\x05log entry\x00error\x0f"
    data = data * 200
    
    classifier = Layer0Classifier()
    result = classifier.classify(data)
    
    assert result.data_type == DataType.BINARY_LOG or result.data_type == DataType.UNKNOWN
    assert 0.3 <= result.printable_ratio <= 0.8


def test_classifier_text_document():
    """Test detection of plain text."""
    data = b"""
    This is a plain text document.
    It contains multiple lines.
    The entropy should be moderate.
    """ * 100
    
    classifier = Layer0Classifier()
    result = classifier.classify(data)
    
    assert result.printable_ratio > 0.80
    assert result.data_type in (DataType.TEXT_DOCUMENT, DataType.SOURCE_CODE)


def test_classifier_compressed():
    """Test detection of compressed/mixed-entropy data."""
    import zlib
    original = b"repetitive data " * 1000
    compressed = zlib.compress(original)
    
    classifier = Layer0Classifier()
    result = classifier.classify(compressed)
    
    # Compressed should have mixed entropy or low printable ratio
    # The key is it shouldn't look like clean text
    assert result.printable_ratio < 0.5 or result.data_type in (
        DataType.COMPRESSED, DataType.BINARY_LOG, DataType.UNKNOWN
    )


def test_classifier_llm_dataset():
    """Test detection of LLM-like natural language."""
    data = b"""
    The quick brown fox jumps over the lazy dog.
    Natural language processing is a subfield of linguistics.
    """ * 100
    
    classifier = Layer0Classifier()
    result = classifier.classify(data)
    
    assert result.printable_ratio > 0.80
    # LLM or text document
    assert result.data_type in (DataType.LLM_DATASET, DataType.TEXT_DOCUMENT)


def test_autotuner_source_code():
    """Test auto-tuner recommendation for source code."""
    classifier = Layer0Classifier()
    data = b"int x = 0;\nint y = x + 1;\n" * 100
    classification = classifier.classify(data)
    
    tuner = AutoTuner()
    config = tuner.recommend(classification)
    
    assert config.mode in ("balanced", "bridge")
    assert config.layers[1].enabled
    assert config.layers[3].enabled  # delta layer should be on for source code


def test_autotuner_binary_log():
    """Test auto-tuner recommendation for log-like data."""
    classifier = Layer0Classifier()
    # Mixed binary and text
    data = b"LOG\x00\x01\x02\x03TIME\x00\x04\x05ENTRY" * 500
    classification = classifier.classify(data)
    
    tuner = AutoTuner()
    config = tuner.recommend(classification)
    
    # Binary/mixed logs should enable multiple layers
    enabled_count = sum(1 for lc in config.layers.values() if lc.enabled)
    assert enabled_count >= 3


def test_autotuner_compressed():
    """Test auto-tuner for compressed/binary data."""
    import zlib
    data = zlib.compress(b"test" * 1000) * 10
    
    classifier = Layer0Classifier()
    classification = classifier.classify(data)
    
    tuner = AutoTuner()
    config = tuner.recommend(classification)
    
    # Should recommend something; the key is it's not overly aggressive
    # if low confidence or high entropy
    assert config.mode in ("bridge", "balanced", "maximal")


def test_autotuner_low_confidence():
    """Test auto-tuner falls back to bridge mode on low confidence."""
    classifier = Layer0Classifier()
    data = b"\x00" * 100  # All nulls - ambiguous
    classification = classifier.classify(data)
    
    tuner = AutoTuner()
    config = tuner.recommend(classification)
    
    # Low confidence should trigger bridge mode
    if classification.confidence < 0.6:
        assert config.mode == "bridge"


def test_classifier_entropy_calculation():
    """Test entropy calculations."""
    classifier = Layer0Classifier()
    
    # All same byte: entropy should be ~0
    data1 = b"\x55" * 256
    result1 = classifier.classify(data1)
    assert result1.entropy < 0.1
    
    # Uniform distribution: entropy should be high
    data2 = bytes(range(256))  # all byte values
    result2 = classifier.classify(data2)
    assert result2.entropy > 7.9


def test_classifier_printable_ratio():
    """Test printable ratio calculation."""
    classifier = Layer0Classifier()
    
    # Pure ASCII
    data1 = b"Hello World" * 100
    result1 = classifier.classify(data1)
    assert result1.printable_ratio > 0.95
    
    # Pure binary
    data2 = bytes(range(256)) * 10
    result2 = classifier.classify(data2)
    assert result2.printable_ratio < 0.5
