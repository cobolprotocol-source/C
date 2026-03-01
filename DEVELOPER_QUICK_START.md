# Developer Quick Start Guide

**Performance Profile System** - Integration for Developers  
**Version**: 1.0  
**Date**: March 1, 2026  

---

## 30-Second Integration

```python
from profile_integration import create_profile_aware_engine

# Wrap your engine
your_engine = YourCompressionEngine()
engine = create_profile_aware_engine(your_engine)

# Use it
result = engine.compress_chunk(data)
print(f"Profile: {result.profile_name}")
print(f"Speed: {result.stats.throughput_mbps:.1f} MB/s")
```

That's it. Everything else is optional.

---

## What Each Profile Does

### EDGE_LOW
```python
# 1-2 cores, <2GB RAM
# Chunks: 8 KB | Threads: 1 | Speed: ~10 MB/s
# Use: IoT, battery, edge devices
```

### CLIENT_STANDARD ⭐ (Safe Fallback)
```python
# 2-8 cores, 4-32GB RAM  
# Chunks: 64 KB | Threads: 2 | Speed: ~50 MB/s
# Use: Laptops, desktops - AUTOMATIC FALLBACK TARGET
```

### WORKSTATION_PRO
```python
# 8-16 cores, 32GB+ RAM
# Chunks: 256 KB | Threads: 4 | Speed: ~150 MB/s
# Use: Professional workstations
```

### SERVER_GENERAL
```python
# 16-64 cores, 64GB+ RAM
# Chunks: 512 KB | Threads: 8 | Speed: ~300 MB/s
# Use: Enterprise servers
```

### DATACENTER_HIGH
```python
# 64+ cores, 256GB+ RAM
# Chunks: 1 MB | Threads: 16 | Speed: ~500+ MB/s
# Use: HPC, data centers
```

---

## Common Integration Patterns

### Pattern 1: Auto-Select (Easiest)

```python
from profile_integration import create_profile_aware_engine

engine = create_profile_aware_engine(your_engine)
result = engine.compress_chunk(data)
# Automatically selects best profile for your hardware
```

### Pattern 2: Manual Selection

```python
engine = create_profile_aware_engine(your_engine)
engine.set_compression_profile('SERVER_GENERAL')
result = engine.compress_chunk(data)
# Forces specific profile
```

### Pattern 3: With Monitoring

```python
engine = create_profile_aware_engine(your_engine)

for chunk in chunks:
    result = engine.compress_chunk(chunk)
    print(f"{result.stats.throughput_mbps:.1f} MB/s")

stats = engine.get_monitoring_stats()
print(f"Average: {stats['monitor']['avg_throughput_mbps']:.1f} MB/s")
```

### Pattern 4: Batch Compression

```python
engine = create_profile_aware_engine(your_engine)
results = engine.compress_multiple_chunks(chunks)

for result in results:
    print(f"{result.profile_name}: {result.stats.throughput_mbps:.1f} MB/s")
```

### Pattern 5: Understanding Selection

```python
engine = create_profile_aware_engine(your_engine)
profile = engine.get_compression_profile()
reason = engine.explain_profile_selection()

print(f"Using: {profile}")
print(f"Because: {reason}")
```

---

## API Reference

### Initialization

```python
from profile_integration import create_profile_aware_engine

engine = create_profile_aware_engine(
    base_engine,                    # Your compression engine
    enable_monitoring=True,         # Collect stats
    auto_select=True,              # Use AUTO profile
    fallback_latency_ms=50.0       # Fallback threshold
)
```

### Compression Methods

#### Single Chunk
```python
result = engine.compress_chunk(
    data,                          # bytes
    monitor_latency=True           # Optional: measure speed
)

# result.profile_name → 'CLIENT_STANDARD'
# result.compressed_data → compressed bytes
# result.stats.throughput_mbps → 48.5
# result.stats.latency_ms → 21
# result.stats.compression_ratio → 0.42
```

#### Multiple Chunks
```python
results = engine.compress_multiple_chunks(
    chunks,                        # list of bytes
    monitor_latency=True
)

# results → list of ProfiledCompressedChunk
for r in results:
    print(r.profile_name, r.stats.throughput_mbps)
```

### Profile Control

```python
# Get active profile
profile_name = engine.get_compression_profile()
# Returns: 'CLIENT_STANDARD'

# Force specific profile
success = engine.set_compression_profile('SERVER_GENERAL')
# Returns: True if valid, False otherwise

# Get profile parameters
params = engine.get_profile_parameters()
# Returns: {'chunk_size_bytes': 512000, 'aes_threads': 8, ...}

# Understand the selection
explanation = engine.explain_profile_selection()
# Returns: "Selected SERVER_GENERAL (16 cores detected, 64GB RAM available)"
```

### Monitoring

```python
stats = engine.get_monitoring_stats()

# stats['profile'] → active profile name
# stats['explanation'] → why it was selected

# stats['monitor'] contains:
#   - compressions → count
#   - successful_compressions → count
#   - failed_compressions → count
#   - avg_throughput_mbps → float
#   - avg_latency_ms → float
#   - fallback_rate → float (0-1)

# stats['fallback_history'] → list of:
#   - from_profile, to_profile, reason, timestamp
```

---

## What You Get

### Per-Compression Result
```python
result = engine.compress_chunk(data)

result.profile_name              # Which profile was used
result.compressed_data           # The compressed bytes
result.stats.throughput_mbps     # MB/s
result.stats.latency_ms          # milliseconds
result.stats.compression_ratio   # bytes_out / bytes_in
result.timestamp                 # When compression happened
```

### Aggregate Statistics
```python
stats = engine.get_monitoring_stats()

stats['profile']['name']                    # Current profile
stats['monitor']['compressions']            # Total count
stats['monitor']['avg_throughput_mbps']     # Average speed
stats['monitor']['avg_latency_ms']          # Average latency
stats['monitor']['fallback_rate']           # % fallbacks
stats['fallback_history']                   # All fallback events
```

---

## Configuration Options

### Latency-Based Fallback

```python
# Use default fallback threshold (profile-dependent)
engine = create_profile_aware_engine(your_engine)

# Or set custom threshold
engine = create_profile_aware_engine(
    your_engine,
    fallback_latency_ms=100.0  # Fall back if latency > 100ms
)
```

### Monitoring

```python
# Enable full monitoring (default)
engine = create_profile_aware_engine(
    your_engine,
    enable_monitoring=True
)

# Disable if you need maximum performance
engine = create_profile_aware_engine(
    your_engine,
    enable_monitoring=False  # No stats collection
)
```

### Profile Selection

```python
# Auto-select based on hardware (default)
engine = create_profile_aware_engine(
    your_engine,
    auto_select=True
)

# Or create with specific profile
engine = create_profile_aware_engine(your_engine)
engine.set_compression_profile('SERVER_GENERAL')
```

---

## Real-World Example

```python
from profile_integration import create_profile_aware_engine
from your_engine import YourCompressionEngine
import time

# Initialize
engine = create_profile_aware_engine(YourCompressionEngine())

# Understand what we're working with
profile = engine.get_compression_profile()
reason = engine.explain_profile_selection()
print(f"✓ Selected {profile}: {reason}")

# Compress some data
data_to_compress = b"..." * 1000000  # 1MB of data
start = time.time()
result = engine.compress_chunk(data_to_compress)
elapsed = time.time() - start

print(f"✓ Compressed {len(data_to_compress)} → {len(result.compressed_data)} bytes")
print(f"✓ Speed: {result.stats.throughput_mbps:.1f} MB/s")
print(f"✓ Ratio: {result.stats.compression_ratio:.1%}")

# Get aggregate statistics
stats = engine.get_monitoring_stats()
print(f"✓ Compressions so far: {stats['monitor']['compressions']}")
print(f"✓ Average throughput: {stats['monitor']['avg_throughput_mbps']:.1f} MB/s")

# Check if fallback happened
if stats['fallback_history']:
    print(f"⚠️  Fallbacks: {len(stats['fallback_history'])}")
    for fb in stats['fallback_history']:
        print(f"   {fb['from_profile']} → {fb['to_profile']}: {fb['reason']}")
```

---

## Testing

### Run Auto Tests
```bash
python3 profile_cli.py test
```

Expected: 7/7 tests passing ✅

### Run Integration Examples
```bash
python3 integration_example.py
```

Shows 6 working examples with real output.

### Manual Testing
```python
from profile_integration import create_profile_aware_engine
from performance_profiles import MockCompressionEngine

# Test with mock engine
engine = create_profile_aware_engine(MockCompressionEngine())

# Test each profile
for profile_name in ['EDGE_LOW', 'CLIENT_STANDARD', 'WORKSTATION_PRO', 'SERVER_GENERAL', 'DATACENTER_HIGH']:
    engine.set_compression_profile(profile_name)
    result = engine.compress_chunk(b'test' * 1000)
    print(f"✓ {profile_name}: {result.stats.throughput_mbps:.1f} MB/s")
```

---

## Troubleshooting

### Q: Wrong profile selected?
```python
# Check what it detected
reason = engine.explain_profile_selection()
print(reason)  # Shows hardware detected and why profile selected

# Force specific profile
engine.set_compression_profile('CLIENT_STANDARD')
```

### Q: Throughput lower than expected?
```python
# Check current profile
profile = engine.get_compression_profile()
print(profile)

# Compare to baseline throughput for that profile
# See PERFORMANCE_PROFILES.md for expected ranges

# If much lower, check hardware resources
# Could indicate system is under load
```

### Q: High fallback rate?
```python
# Check fallback history
stats = engine.get_monitoring_stats()
for fb in stats['fallback_history']:
    print(f"{fb['from_profile']} → {fb['to_profile']}: {fb['reason']}")

# If many fallbacks due to latency:
# - Increase fallback threshold
# - Or check if hardware is overloaded
# - Or manually select more conservative profile
```

### Q: How do I integrate with my engine?
```python
# Step 1: Get your engine ready
your_engine = YourCompressionEngine()

# Step 2: Wrap it with profile system
from profile_integration import create_profile_aware_engine
engine = create_profile_aware_engine(your_engine)

# Step 3: Use as normal
result = engine.compress_chunk(data)

# That's it! No changes to your_engine needed.
```

---

## Files You Need

### Minimal Integration
- `profile_integration.py` - The wrapper
- `performance_profiles.py` - The core
- `spec/performance_profiles.yaml` - The spec

### Good to Have
- `INTEGRATION_GUIDE.py` - Examples
- `profile_cli.py` - CLI testing
- `test_performance_profiles.py` - Tests

### Documentation
- `PERFORMANCE_PROFILES.md` - Full guide
- `PERFORMANCE_PROFILES_QUICK_REFERENCE.md` - Quick lookup
- `README_PROFILES.md` - Overview

---

## Performance Expectations

```
Expected throughput by profile on single task:
- EDGE_LOW:          ~10 MB/s
- CLIENT_STANDARD:   ~50 MB/s
- WORKSTATION_PRO:  ~150 MB/s
- SERVER_GENERAL:   ~300 MB/s
- DATACENTER_HIGH:  ~500+ MB/s
```

Your actual speed depends on:
- Data characteristics (compressibility)
- Hardware specs (cores, RAM, crypto support)
- System load (other processes running)
- Network (if distributed)

---

## Advanced: Building Your Own Engine

Use this system as a template for creating your own compression engine:

```python
from performance_profiles import PerformanceProfileManager

class MyCustomCompressionEngine:
    def __init__(self):
        self.profile_manager = PerformanceProfileManager()
        self.profile_manager.auto_select_profile()
    
    def compress_chunk(self, data):
        profile = self.profile_manager.get_active_profile()
        
        # Use profile parameters
        chunk_size = profile['chunk_size_bytes']
        threads = profile['aes_threads']
        
        # ... your compression logic here ...
        
        compressed = self._do_compression(data, chunk_size, threads)
        return compressed
```

---

## Command-Line Testing

### List All Profiles
```bash
python3 profile_cli.py list
```

### Check Your Hardware
```bash
python3 profile_cli.py auto
```

### Compare All Profiles
```bash
python3 profile_cli.py compare
```

### Run Tests
```bash
python3 profile_cli.py test
```

### Force Profile
```bash
python3 profile_cli.py set SERVER_GENERAL
```

### Understand Selection
```bash
python3 profile_cli.py explain
```

---

## Quick Reference Card

```python
# Import
from profile_integration import create_profile_aware_engine

# Initialize (auto-selects profile)
engine = create_profile_aware_engine(your_engine)

# Compress
result = engine.compress_chunk(data)

# Access result
result.profile_name              # 'CLIENT_STANDARD'
result.compressed_data           # bytes
result.stats.throughput_mbps     # 48.5
result.stats.latency_ms          # 21
result.stats.compression_ratio   # 0.42

# Profile management
engine.set_compression_profile('SERVER_GENERAL')
current = engine.get_compression_profile()
reason = engine.explain_profile_selection()

# Monitoring
stats = engine.get_monitoring_stats()
print(f"{stats['monitor']['avg_throughput_mbps']:.1f} MB/s average")

# Multiple chunks
results = engine.compress_multiple_chunks(chunks)
```

---

## Support Resources

| Need | Location |
|------|----------|
| Full Guide | [PERFORMANCE_PROFILES.md](PERFORMANCE_PROFILES.md) |
| Quick Ref | [PERFORMANCE_PROFILES_QUICK_REFERENCE.md](PERFORMANCE_PROFILES_QUICK_REFERENCE.md) |
| Examples | [integration_example.py](integration_example.py) |
| Step-by-Step | [INTEGRATION_GUIDE.py](INTEGRATION_GUIDE.py) |
| Tests | `python3 profile_cli.py test` |
| Overview | [README_PROFILES.md](README_PROFILES.md) |

---

## Next Steps

1. **Try it**: `python3 profile_cli.py auto`
2. **Integrate**: Copy the 30-second integration code above
3. **Test**: `python3 profile_cli.py test`
4. **Monitor**: `engine.get_monitoring_stats()`
5. **Deploy**: See [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md)

---

## Common Mistakes to Avoid

❌ Modifying engine.py (not needed!)
✅ Just wrap it: `create_profile_aware_engine(your_engine)`

❌ Using FFI `auto_select_profile()` function
✅ Let the wrapper handle it automatically

❌ Ignoring fallback statistics
✅ Monitor `stats['fallback_history']` regularly

❌ Expecting same speed on all hardware
✅ Different profiles have different throughputs

❌ Trying to change profiles too frequently
✅ Set once at startup, rarely change

---

**Version**: 1.0  
**Status**: Production Ready  
**Date**: March 1, 2026  

**Quick Start**: 30 seconds | **Full Integration**: < 15 minutes | **Full Understanding**: 1 hour
