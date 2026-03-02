# COBOL Protocol - Quick Demo & Usage Guide

## 🚀 5-Minute Quick Start

### 1. Installation

```bash
cd COBOL-Protocol---Nafal-Faturizki-Edition
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Basic Compression Example

```python
from engine import CobolEngine

# Initialize
engine = CobolEngine()

# Your data
data = b"The quick brown fox jumps over the lazy dog. " * 100

# Compress
compressed, metadata = engine.compress_block(data)

print(f"Original:   {len(data):,} bytes")
print(f"Compressed: {len(compressed):,} bytes")
print(f"Ratio:      {metadata.compression_ratio:.2f}x")
print(f"Savings:    {(1 - len(compressed)/len(data))*100:.1f}%")

# Decompress
decompressed = engine.decompress_block(compressed, metadata)
print(f"Integrity:  {'✓ PASS' if decompressed == data else '✗ FAIL'}")
```

**Output Example:**
```
Original:   4,700 bytes
Compressed: 892 bytes
Ratio:      5.27x
Savings:    81.1%
Integrity:  ✓ PASS
```

---

## 📊 Understanding Compression Layers

### Automatic Layer Selection

The engine automatically selects appropriate layers based on data characteristics:

```python
from engine import CobolEngine, CompressionLayer

engine = CobolEngine()

# Layer selection happens automatically:
# 1. Calculate entropy
# 2. High entropy (>0.95)? → Skip all layers, return uncompressed
# 3. Low entropy? → Apply L1 Semantic mapping
# 4. Has numeric patterns? → Also apply L3 Delta encoding
# 5. Store layer info in metadata for decompression

compressed, metadata = engine.compress_block(data)
print(f"Layers applied: {[l.name for l in metadata.layers_applied]}")
```

### Manual Layer Selection (Advanced)

```python
from config import CompressionLayer

# Later: support explicit layer selection
engine = CobolEngine()
compressed, meta = engine.compress_block(
    data,
    apply_layers=[CompressionLayer.L1_SEMANTIC_MAPPING]
)
```

---

## 🔍 Analyzing Your Data

### Check Entropy Profile

```python
from engine import AdaptiveEntropyDetector
from config import EntropyConfig

detector = AdaptiveEntropyDetector(EntropyConfig())
profile = detector.get_entropy_profile(data)

print(f"Entropy:       {profile['entropy']:.2f} bits")
print(f"Unique bytes:  {profile['unique_bytes']}")
print(f"Max frequency: {profile['max_frequency']}")
print(f"Recommendation: {profile['recommendation']}")
```

**Example Output:**
```
Entropy:       3.28 bits
Unique bytes:  87
Max frequency: 245
Recommendation: APPLY
```

### Check Compression Statistics

```python
# Process multiple blocks
for block in blocks:
    engine.compress_block(block)

stats = engine.get_statistics()
print(f"Blocks processed: {stats['blocks_processed']}")
print(f"Overall ratio:    {stats['overall_compression_ratio']:.2f}x")
print(f"Total saved:      {stats['total_space_saved']:,} bytes")
print(f"Space saved %:    {stats['space_saved_percent']:.1f}%")
print(f"\nLayers used:")
for layer, count in stats['layers_applied'].items():
    print(f"  {layer}: {count} times")
```

---

## 🛠️ Working with Dictionaries

### Use Pre-trained Dictionaries

```python
from engine import DictionaryManager
from config import DictionaryConfig

manager = DictionaryManager(DictionaryConfig())

# Get default L1 semantic dictionary
l1_dict = manager.get_dictionary("L1_SEMANTIC")
print(f"L1 dictionary size: {l1_dict.size()} entries")
print(f"Sample mappings:")
for token, token_id in list(l1_dict.token_to_id.items())[:5]:
    print(f"  '{token}' → {token_id}")
```

### Build Adaptive Dictionary from Your Data

```python
# Train dictionary on your specific data
training_data = open("mydata.txt", "rb").read()
adaptive_dict = manager.build_adaptive_dictionary(
    training_data,
    layer="L1_SEMANTIC",
    max_size=256
)

print(f"Learned {adaptive_dict.size()} tokens from your data")

# Use in compression
engine = CobolEngine()
# (Dictionary automatically used)
compressed, _ = engine.compress_block(training_data)
```

---

## 🔒 Security: Encryption & Integrity

### Integrity Verification (Automatic)

```python
# Integrity check happens automatically during decompression
try:
    decompressed = engine.decompress_block(compressed, metadata)
    print("✓ Data integrity verified")
except IntegrityError:
    print("✗ Data corrupted!")
```

### AES-256 Encryption (Framework Ready)

```python
# Encryption support coming in v1.1
# from cryptography.hazmat.primitives.ciphers.aead import AESGCM
# 
# key = ... # your 256-bit key
# cipher = AESGCM(key)
# encrypted = cipher.encrypt(nonce, compressed_data, metadata_bytes)
```

---

## 📈 Performance Benchmarking

### Basic Throughput Test

```python
import time
import numpy as np

def benchmark_compression(size_mb):
    engine = CobolEngine()
    
    # Create test data (highly compressible)
    data = b"Hello World! " * (size_mb * 1024 * 1024 // 13)
    
    start = time.time()
    compressed, _ = engine.compress_block(data)
    elapsed = time.time() - start
    
    mb_s = (len(data) / (1024 * 1024)) / elapsed
    ratio = len(data) / len(compressed)
    
    print(f"Size:      {size_mb} MB")
    print(f"Compressed: {len(compressed) / (1024*1024):.2f} MB")
    print(f"Ratio:     {ratio:.2f}x")
    print(f"Throughput: {mb_s:.1f} MB/s")
    print(f"Time:      {elapsed:.3f}s")

benchmark_compression(10)
```

---

## 🐳 Docker Usage

### Single Node

```bash
# Build
docker build -t cobol-engine:1.0 .

# Run
docker run -it \
    -v $(pwd)/data:/app/data \
    -p 9000:9000 \
    cobol-engine:1.0

# Check logs
docker logs <container_id>
```

### Multi-Node with Docker Compose

```bash
# Start all nodes
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs cobol-edge-l1

# Process data across nodes
# (Implementation coming in v1.1)

# Stop
docker-compose down
```

---

## 📚 Layer Details

### Layer 1: Semantic Mapping

Best for: **Text, JSON, code**

```python
from engine import Layer1SemanticMapper

mapper = Layer1SemanticMapper(dictionary_manager)
text_data = b"Hello world, this is a test."

compressed, metadata = mapper.compress(text_data)
print(f"Compression: {len(text_data)} → {len(compressed)} bytes")
```

**How it works:**
1. Tokenize text into words
2. Look up each word in dictionary
3. Common words → 1-byte ID (0-255)
4. Rare words → Escape sequence (0xFF + length + bytes)

**Example:**
```
Input:  "The quick brown fox"
Tokens: ["The", "quick", "brown", "fox"]
Dict:   {The→0, quick→1, brown→2, fox→3}
Output: [0, 1, 2, 3]  (4 bytes vs 19 bytes)
```

### Layer 3: Delta Encoding

Best for: **Numeric sequences, time-series**

```python
from engine import Layer3DeltaEncoder

encoder = Layer3DeltaEncoder(dictionary_manager)

# Monotonically increasing sequence
numeric_data = bytes(range(100))

compressed, metadata = encoder.compress(numeric_data)
print(f"Compression: {len(numeric_data)} → {len(compressed)} bytes")
```

**How it works:**
1. Calculate deltas: `d[i] = value[i+1] - value[i]`
2. Calculate second-order deltas: `dd[i] = d[i+1] - d[i]`
3. Variable-length encode (small numbers = 1 byte)
4. Store first values for reconstruction

**Example:**
```
Input:     [1, 3, 5, 8, 12, ...]
Deltas:    [2, 2, 3, 4, ...]
DD:        [0, 1, 1, ...]  (very small!)
VarInt:    Much smaller!
```

---

## 🧪 Testing

### Run Test Suite

```bash
# All tests
python -m pytest test_engine.py -v

# Specific test
python -m pytest test_engine.py::TestCobolEngine::test_compress_text_block -v

# With coverage
python -m pytest test_engine.py --cov=engine --cov-report=html
```

### Write Custom Tests

```python
import pytest
from engine import CobolEngine

def test_my_data_format():
    engine = CobolEngine()
    
    # Load your data
    with open("myfile.bin", "rb") as f:
        data = f.read()
    
    # Compress
    compressed, metadata = engine.compress_block(data)
    
    # Decompress
    decompressed = engine.decompress_block(compressed, metadata)
    
    # Verify
    assert decompressed == data, "Data integrity failed!"
    
    # Check ratio
    ratio = len(data) / len(compressed)
    print(f"Compression ratio: {ratio:.2f}x")
```

---

## 🎯 Common Use Cases

### Use Case 1: LLM Training Data Compression

```python
# Compress dataset of training texts
engine = CobolEngine()

def compress_dataset(dataset_path, output_path):
    total_size = 0
    total_compressed = 0
    
    for txt_file in os.listdir(dataset_path):
        with open(txt_file, 'rb') as f:
            chunk = f.read(1_000_000)  # 1MB chunks
            
        compressed, meta = engine.compress_block(chunk)
        
        total_size += len(chunk)
        total_compressed += len(compressed)
        
        # Write to output
        output_file.write(compressed)
        output_file.write(meta.serialize())
    
    ratio = total_size / total_compressed
    print(f"Total compression ratio: {ratio:.2f}x")
    print(f"Space saved: {total_size - total_compressed:,} bytes")
```

### Use Case 2: API Response Compression

```python
@app.route("/api/data", methods=["POST"])
def compress_response():
    data = request.get_data()
    
    engine = CobolEngine()
    compressed, metadata = engine.compress_block(data)
    
    return {
        "compressed": compressed.hex(),
        "metadata": metadata.serialize().hex(),
        "ratio": metadata.compression_ratio
    }
```

### Use Case 3: Streaming Large Files

```python
def compress_stream(input_file, output_file, chunk_size=1_000_000):
    engine = CobolEngine()
    
    with open(input_file, 'rb') as infile, \
         open(output_file, 'wb') as outfile:
        
        while True:
            chunk = infile.read(chunk_size)
            if not chunk:
                break
            
            compressed, metadata = engine.compress_block(chunk)
            
            # Write: [size|compressed_data|metadata]
            outfile.write(struct.pack('>I', len(compressed)))
            outfile.write(compressed)
            outfile.write(metadata.serialize())

# Usage
compress_stream("input.bin", "output.cobol")
```

---

## 🔧 Troubleshooting

### Issue: Low compression ratio

```python
# Check entropy
profile = detector.get_entropy_profile(data)
if profile['entropy'] > 0.95:
    print("Data is already random/compressed")
    # Solution: skip compression
```

### Issue: Decompression fails

```python
try:
    decompressed = engine.decompress_block(compressed, metadata)
except IntegrityError:
    print("Data corrupted in transit/storage")
except DecompressionError:
    print("Incompatible compression version")
```

### Issue: Performance degradation

```python
# Profile the engine
import cProfile
cProfile.run("""
    for i in range(1000):
        engine.compress_block(data)
""", sort='cumulative')
```

---

## 📞 Support & Resources

- **Documentation**: See [README.md](README.md)
- **Architecture**: See [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Tests**: See [test_engine.py](test_engine.py)
- **Configuration**: See [config.py](config.py)

---

**Happy compressing! 🚀**
