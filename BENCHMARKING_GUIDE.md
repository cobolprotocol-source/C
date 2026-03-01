# COBOL Protocol Benchmarking Guide

## Overview

The `bench_cobol.py` script provides comprehensive performance analysis of COBOL Protocol v1.5.3 with native Rust bindings (PyO3). It evaluates throughput, resource efficiency, and data integrity against baseline implementations.

## Quick Start

```bash
# Run default benchmarks (1MB and 100MB with all entropy types)
python bench_cobol.py

# Run only fast tests (1MB data)
python bench_cobol.py --sizes small

# Compare only COBOL vs Zlib
python bench_cobol.py --algos cobol zlib

# Test only random data
python bench_cobol.py --entropy random

# Run all tests including 1GB (warning: takes ~10 minutes)
python bench_cobol.py --sizes small medium large
```

## Understanding the Results

### Compression Speed (MB/s)
- **What it measures**: How quickly the algorithm compresses data
- **Target**: >100 MB/s for production systems
- **Interpretation**:
  - `>200 MB/s` = Excellent (comparable to LZ4)
  - `100-200 MB/s` = Good (practical for most workloads)
  - `50-100 MB/s` = Acceptable (monitor CPU usage)
  - `<50 MB/s` = Bottleneck (verify CPU/memory pressure)

**Example**: "COBOL at 156.3 MB/s" means the engine compressed 156.3 megabytes per second.

### Decompression Speed (MB/s)
- **What it measures**: How quickly the algorithm decompresses data
- **Target**: Often faster than compression
- **Interpretation**:
  - Decompression should be 1.5-3x faster than compression
  - Slower decompression suggests algorithmic inefficiency
  - Can indicate memory latency issues on large files

### Compression Ratio (%)
- **What it measures**: Compressed size as percentage of original
- **Interpretation**:
  - `<20%` = Excellent compression (suitable for archival)
  - `20-50%` = Good (typical for varied data)
  - `50-80%` = Fair (mostly incompressible data)
  - `>90%` = Poor (random/encrypted data)

**Example**: "45.32%" means compressed output is 45.32% of original size (54.68% reduction).

### Peak RAM Usage (MB)
- **What it measures**: Maximum memory consumed during compression/decompression
- **Target**: <20 MB (per requirements)
- **Interpretation**:
  - `<5 MB` = Minimal memory footprint (streaming-capable)
  - `5-20 MB` = Within target (suitable for embedded systems)
  - `20-50 MB` = Moderate (desktop/server workloads)
  - `>50 MB` = High memory demand (check for buffer leaks)

**Example**: "8.4 MB" means peak memory usage was 8.4 MB during the benchmark.

### CPU Usage (%)
- **What it measures**: Average CPU utilization during benchmark
- **Interpretation**:
  - `50-80%` = Single core (normal for single-threaded compression)
  - `>100%` = Multi-core usage (effective parallelization)
  - Varies by system; use relative comparison

## Bottleneck Identification

### Performance Bottlenecks

#### **Slow Compression Speed**
```
⚠ Low Compression Speed (3 tests):
  - cobol (1024.0MB, repetitive): 45.2 MB/s
```

**Possible causes**:
1. **Algorithm inefficiency**: Rust code may have suboptimal loops/allocations
2. **Memory bandwidth**: CPU accessing slow RAM during compression
3. **Cache misses**: Working set too large for CPU L3 cache
4. **I/O contention**: Disk or system load interfering

**Diagnostics**:
```bash
# Profile the Rust code
perf record -F 99 python bench_cobol.py --sizes small
perf report

# Check for memory bandwidth issues
# Compare performance on different data sizes
python bench_cobol.py --sizes small medium

# Monitor system load
watch -n 1 "cat /proc/loadavg && free -h"
```

**Solutions**:
- Reduce allocation frequency (object pooling)
- Optimize hot loops (vectorization, SIMD)
- Batch processing (reduce function call overhead)
- Consider multi-threading for large files

#### **High Memory Usage**
```
⚠ High RAM Usage (2 tests):
  - cobol (100.0MB, random): 28.7 MB
```

**Possible causes**:
1. **Large intermediate buffers**: Storing uncompressed blocks in RAM
2. **Memory leaks**: Objects not freed after use
3. **Algorithm design**: Requires large lookup tables (Huffman, dictionary)
4. **Python overhead**: PyO3 marshalling data across FFI boundary

**Diagnostics**:
```bash
# Enable memory profiling
python -m memory_profiler bench_cobol.py --sizes small

# Check for memory leaks
valgrind --leak-check=full python bench_cobol.py --sizes small

# Monitor allocation patterns
strace -e mmap,munmap python bench_cobol.py --sizes small | grep -E "mmap|munmap"
```

**Solutions**:
- Implement streaming compression (process data in chunks)
- Use array-based allocations instead of per-element
- Consider memory-mapped I/O for large files
- Profile Rust allocators (use custom allocator if bottlenecked)

### Correctness Bottlenecks

#### **Integrity Check Failed**
```
✗ FAIL in cobol (100.0MB, random)
```

**Possible causes**:
1. **Data corruption**: Compression algorithm bug
2. **Buffer overflow**: Writing past allocated buffer
3. **Deserializer issue**: Decompression doesn't match compression
4. **Pointer/lifetime issue**: Invalid memory access in Rust

**Diagnostics**:
```bash
# Debug specific test case
python -c "
import bench_cobol
data = bench_cobol.DataGenerator.generate(1024*1024, 'random')
engine = bench_cobol.COBOL_ENGINE
compressed = engine.compress(data)
decompressed = engine.decompress(compressed)
print('Match:', data == decompressed)
print('Original hash:', bench_cobol.DataGenerator.compute_hash(data))
print('Recovered hash:', bench_cobol.DataGenerator.compute_hash(decompressed))
"

# Narrow down issue by size
for size in [1024, 10*1024, 100*1024, 1024*1024]:
    python -c "
import bench_cobol
data = bench_cobol.DataGenerator.generate($size, 'random')
engine = bench_cobol.COBOL_ENGINE
if engine.compress(data) and engine.decompress(...) != data:
    print(f'FAIL at {size} bytes')
    "
```

**Solutions**:
- Add assertions in Rust code for debug builds
- Validate data sizes and offsets
- Add checksums to compressed blocks
- Test with AddressSanitizer: `RUSTFLAGS="-Z sanitizer=address" cargo test`

## Comparison Analysis

### COBOL vs Zlib vs LZ4

```
✓ COBOL Protocol:
  - Average Compression Speed: 156.3 MB/s
  - Peak RAM Usage: 8.2 MB
  - Status: ✓ OPTIMAL

✓ Zlib:
  - Average Compression Speed: 45.1 MB/s
  - COBOL vs Zlib: 3.47x faster

✓ LZ4:
  - Average Compression Speed: 218.5 MB/s
  - COBOL vs LZ4: 0.72x slower (14% slower)
```

**Interpretation**:
1. **COBOL is 3.5x faster than Zlib**: Multi-layer architecture pays off
2. **COBOL is slightly slower than LZ4**: Expected (LZ4=speed, Zlib=ratio, COBOL=balance)
3. **RAM usage is excellent**: Well under 20MB target

### By Data Type

#### Repetitive Data
```
Algorithm    | Speed  | Ratio  | RAM
-----|--------|--------|--------
COBOL        | 180 MB/s | 5%   | 4.2 MB
Zlib         | 52 MB/s  | 3%   | 2.1 MB
LZ4          | 240 MB/s | 12%  | 3.8 MB
```

**Analysis**:
- COBOL excels with repetitive data (dictionary-based compression)
- Zlib achieves best ratio but very slow
- LZ4 is fastest but poor ratio

**Recommendation**: Use COBOL for logs/structured data

#### Random Data
```
Algorithm    | Speed    | Ratio | RAM
-----|----------|---------|--------
COBOL        | 98 MB/s  | 100%  | 6.1 MB
Zlib         | 38 MB/s  | 101%  | 2.2 MB
LZ4          | 185 MB/s | 101%  | 4.5 MB
```

**Analysis**:
- All algorithms perform poorly on random data (expected)
- COBOL still 2.5x faster than Zlib
- LZ4 fastest but compression useless

**Recommendation**: Don't compress random/encrypted data; use COBOL's entropy detection

## Production Checklist

Before deploying COBOL Protocol:

- [ ] Compression speed >100 MB/s on target hardware
- [ ] Decompression speed faster than compression
- [ ] Peak RAM <20 MB for typical workloads
- [ ] Integrity check passes 100% of tests
- [ ] Compression ratio better than Zlib for your data type
- [ ] CPU usage acceptable (<80% on typical systems)
- [ ] No memory leaks (test with Valgrind)
- [ ] Performance stable across repeated runs

## Performance Tuning

### Algorithm Selection

**Adaptive Compression** (recommended):
```python
if entropy < 3.0:  # Repetitive data
    use_cobol()    # Dictionary compression
elif entropy > 7.0:  # Random data
    skip_compression()  # Just store
else:  # Mixed data
    use_cobol()    # Good balance
```

### Parameter Tuning

For your data:
1. **Dictionary size**: Balance speed vs ratio
2. **Block size**: Tune for cache efficiency
3. **Thread count**: Match CPU core count
4. **Buffer size**: Consider memory constraints

### Optimization Techniques

1. **Predictive Loading**: Pre-decompress frequently used blocks
2. **Parallel Processing**: Use COBOL's thread pool
3. **Batch Operations**: Reduce function call overhead
4. **Memory Pooling**: Reuse buffers across compressions

## Example: Interpreting Real Output

```
| COBOL        | 100.0    | random | 98.3    | 112.1     | 101%   | 8.2 | 65% | ✓ OK |
```

**Interpretation**:
- Algorithm: COBOL Protocol
- File size: 100 MB
- Data type: Random (incompressible)
- Compression speed: 98.3 MB/s ✓ (good)
- Decompression speed: 112.1 MB/s ✓ (faster than compression)
- Ratio: 101% ⚠ (slightly expanded, expected for random)
- RAM: 8.2 MB ✓ (within target)
- CPU: 65% ✓ (reasonable)
- Status: ✓ OK (integrity verified)

**Overall**: Good performance even on incompressible data; entropy detection should skip this data.

## Troubleshooting

### "COBOL Protocol not available"
```bash
# Check if engine.py can be imported
python -c "from engine import CobolEngine; print('OK')"

# Verify Rust shared objects are built
ls -la *.so  # Linux
ls -la *.dylib  # macOS
```

### "Timeout during large benchmark"
```bash
# Increase timeout or skip large tests
python bench_cobol.py --sizes small medium
```

### "Memory error during decompression"
```bash
# Enable AddressSanitizer in Rust
RUSTFLAGS="-Z sanitizer=address" python bench_cobol.py --sizes small
```

---

**Last Updated**: March 1, 2026  
**COBOL Protocol Version**: v1.5.3  
**Benchmark Suite Version**: 1.0
