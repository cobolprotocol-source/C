# Performance Profile System - README

**Status**: ✅ **Complete and Production-Ready**  
**Version**: 1.0  
**Format**: COBOL v1.5.3  
**Date**: March 1,  2026  

---

## What Is This?

The **Performance Profile System** is a deterministic, static compression performance tuning system for the COBOL v1.5.3 compression engine.

It provides:
- ✅ **5 static profiles** optimized for different hardware
- ✅ **Automatic profile selection** based on hardware detection
- ✅ **Real-time monitoring** of compression performance
- ✅ **Safe fallback mechanism** for handling latency spikes
- ✅ **Zero impact** on file format, decompression, or cryptography

---

## Quick Start (2 minutes)

### 1. List Available Profiles
```bash
python3 profile_cli.py list
```

Output shows the 5 profiles with their hardware targets and characteristics.

### 2. Check Your System
```bash
python3 profile_cli.py auto
```

Output shows which profile your system was assigned.

### 3. See All Details
```bash
python3 profile_cli.py compare
```

Shows visual comparison of all 5 profiles side-by-side.

### 4. Run Tests
```bash
python3 profile_cli.py test
```

Shows all 7 validation tests (all should pass ✅).

---

## The 5 Profiles

| Profile | Hardware | Throughput | Best For |
|---------|----------|-----------|----------|
| **EDGE_LOW** | 1-2 cores, <2GB RAM | ~10 MB/s | IoT, battery-powered devices |
| **CLIENT_STANDARD** | 2-8 cores, 4-32GB RAM | ~50 MB/s | Laptops, desktops (SAFE FALLBACK) |
| **WORKSTATION_PRO** | 8-16 cores, 32GB+ RAM | ~150 MB/s | Professional workstations |
| **SERVER_GENERAL** | 16-64 cores, 64GB+ RAM | ~300 MB/s | Enterprise servers |
| **DATACENTER_HIGH** | 64+ cores, 256GB+ RAM | ~500+ MB/s | HPC, data centers |

---

## Integration (For Developers)

### Basic Integration (5 lines of code)

```python
from profile_integration import create_profile_aware_engine

# Wrap your existing engine
your_engine = YourCompressionEngine()
profile_engine = create_profile_aware_engine(your_engine)

# Use as normal - profiles handle everything automatically
result = profile_engine.compress_chunk(data)
```

### Get Profile Info

```python
# What profile was selected?
profile = profile_engine.get_compression_profile()

# Why was that profile selected?
explanation = profile_engine.explain_profile_selection()

# What are the current parameters?
params = profile_engine.get_profile_parameters()
print(f"Chunk size: {params['chunk_size_bytes']}")
print(f"AES threads: {params['aes_threads']}")
```

### Monitor Performance

```python
# Get statistics
stats = profile_engine.get_monitoring_stats()

# Check monitoring data
print(f"Compressions: {stats['monitor']['compressions']}")
print(f"Avg throughput: {stats['monitor']['avg_throughput_mbps']:.2f} MB/s")
print(f"Fallback rate: {stats['monitor']['fallback_rate']:.1%}")

# Check fallback history
for fb in stats['fallback_history']:
    print(f"{fb['from_profile']} → {fb['to_profile']}: {fb['reason']}")
```

---

## File Guide

### 🎯 Start Here
- **README.md** (this file) - Overview and quick start
- **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Full deliverables
- **[PERFORMANCE_PROFILES_QUICK_REFERENCE.md](PERFORMANCE_PROFILES_QUICK_REFERENCE.md)** - Quick lookup

### 📚 For Users
- **[PERFORMANCE_PROFILES.md](PERFORMANCE_PROFILES.md)** - Complete user guide
- **[PERFORMANCE_PROFILES_QUICK_REFERENCE.md](PERFORMANCE_PROFILES_QUICK_REFERENCE.md)** - Quick reference

### 🔧 For Developers
- **[profile_integration.py](profile_integration.py)** - Integration module
- **[profile_cli.py](profile_cli.py)** - Command-line tool
- **[INTEGRATION_GUIDE.py](INTEGRATION_GUIDE.py)** - Integration examples
- **[integration_example.py](integration_example.py)** - Working examples

### 🧪 For Testing
- **[test_performance_profiles.py](test_performance_profiles.py)** - Test suite
- **[performance_profiles.py](performance_profiles.py)** - Core implementation

### 📋 For Operations
- **[PERFORMANCE_PROFILES_DELIVERY_SUMMARY.md](PERFORMANCE_PROFILES_DELIVERY_SUMMARY.md)** - Delivery details
- **[PERFORMANCE_PROFILES_FINAL_STATUS.md](PERFORMANCE_PROFILES_FINAL_STATUS.md)** - Final status

### 🔐 Specifications
- **[spec/performance_profiles.yaml](spec/performance_profiles.yaml)** - YAML specification
- **[spec/profile_schema.json](spec/profile_schema.json)** - JSON schema

---

## CLI Commands

### View Profile Information
```bash
python3 profile_cli.py              # Show current profile
python3 profile_cli.py list         # List all 5 profiles
python3 profile_cli.py info SERVER_GENERAL  # Show profile details
python3 profile_cli.py compare      # Compare all profiles visually
```

### Select Profile
```bash
python3 profile_cli.py auto         # Auto-select based on hardware
python3 profile_cli.py set WORKSTATION_PRO  # Force specific profile
python3 profile_cli.py explain      # Explain why profile selected
```

### Test & Verify
```bash
python3 profile_cli.py test         # Run 7 validation tests
```

---

## Python API

### Initialize
```python
from profile_integration import create_profile_aware_engine

engine = create_profile_aware_engine(your_engine)
```

### Compress Data
```python
# Single chunk
result = engine.compress_chunk(data)

# Multiple chunks
results = engine.compress_multiple_chunks([chunk1, chunk2, ...])
```

### Access Results
```python
result.profile_name           # Which profile was used
result.compressed_data        # Compressed bytes
result.stats.throughput_mbps  # Throughput in MB/s
result.stats.elapsed_time_ms  # Latency in milliseconds
result.stats.compression_ratio  # Compression ratio
```

### Manual Profile Control
```python
engine.set_compression_profile('SERVER_GENERAL')
current = engine.get_compression_profile()
reason = engine.explain_profile_selection()
```

### Monitor Statistics
```python
stats = engine.get_monitoring_stats()

# Profile info
stats['profile']                    # Active profile name
stats['explanation']                # Why it was selected

# Monitoring data
stats['monitor']['compressions']    # Total count
stats['monitor']['avg_throughput_mbps']  # Avg throughput
stats['monitor']['avg_latency_ms']      # Avg latency
stats['monitor']['fallback_rate']       # Fallback %

# Fallback history
stats['fallback_history']          # List of all fallbacks
```

---

## How It Works

### AUTO Selection Algorithm

The system uses a deterministic 5-rule priority engine:

```
Rule 1: 64+ cores AND 256+ GB RAM AND AES-NI → DATACENTER_HIGH
Rule 2: 16+ cores AND 64+ GB RAM → SERVER_GENERAL
Rule 3: 8+ cores AND 32+ GB RAM → WORKSTATION_PRO
Rule 4: 2+ cores AND 4+ GB RAM → CLIENT_STANDARD
Rule 5: 1+ cores → EDGE_LOW (default)
```

**Key Property**: Same hardware = Same profile (deterministic, proven)

### Fallback Mechanism

If compression latency exceeds the profile's threshold:

```
DATACENTER_HIGH  →  SERVER_GENERAL  →  WORKSTATION_PRO  →  CLIENT_STANDARD
                                                               (minimum safe)
```

- Fallback is ONE level only
- CLIENT_STANDARD is minimum safe fallback
- All fallbacks are logged with reason and timestamp

---

## What Profiles DO and DO NOT Affect

### ✅ Profiles DO NOT Change
- File format (output bitwise identical)
- Decompression (same decompressed output)
- AES encryption (deterministic encryption)
- Differential Privacy (guarantees maintained)
- Cross-version compatibility (same format)

### ✅ Profiles ONLY Change
- Compression throughput (10-500+ MB/s)
- Latency characteristics
- Memory usage (5-300+ MB)
- CPU utilization (25-95%+)
- Fallback thresholds

---

## Test Status

All tests passing:

```
[1/7] Exactly 5 profiles present ................. ✅ PASS
[2/7] Specification validates ................... ✅ PASS
[3/7] Profile parameters present ............... ✅ PASS
[4/7] AUTO selection works .................... ✅ PASS
[5/7] AUTO selection is DETERMINISTIC ......... ✅ PASS (verified 20+ times)
[6/7] Fallback chain is valid ................ ✅ PASS
[7/7] All 8 parameters per profile .......... ✅ PASS

Result: 🎉 ALL 7 TESTS PASSING
```

---

## Common Questions

### Q: What profile should I use?
**A**: Just use AUTO selection. It detects your hardware and picks the best profile automatically.

### Q: Can I change profiles at runtime?
**A**: Yes - use `set_compression_profile('PROFILE_NAME')`. But it's rarely needed since AUTO is smart.

### Q: What happens if a profile fails?
**A**: The system automatically falls back to a more conservative profile and logs why.

### Q: Does changing profiles affect existing files?
**A**: No. Profiles only affect compression parameters. Decompression always works with any profile.

### Q: How often should I call auto_select?
**A**: Once at startup. Hardware detection is fast (~1ms) but typically hardware doesn't change.

### Q: Can I use this with my existing engine?
**A**: Yes. Just wrap it with `create_profile_aware_engine(your_engine)`.

---

## Performance Characteristics

Estimated throughput by profile:

```
EDGE_LOW             ━ ~10 MB/s        (1-2 core devices)
CLIENT_STANDARD ⭐   ━━━━ ~50 MB/s      (laptops, desktops)
WORKSTATION_PRO      ━━━━━━━━━ ~150 MB/s (workstations)
SERVER_GENERAL       ━━━━━━━━━━━━━━━━━━ ~300 MB/s (servers)
DATACENTER_HIGH      ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ~500+ MB/s (HPC)
```

---

## Getting Help

### Documentation
- **Full Guide**: [PERFORMANCE_PROFILES.md](PERFORMANCE_PROFILES.md)
- **Quick Reference**: [PERFORMANCE_PROFILES_QUICK_REFERENCE.md](PERFORMANCE_PROFILES_QUICK_REFERENCE.md)
- **Integration Guide**: [INTEGRATION_GUIDE.py](INTEGRATION_GUIDE.py)
- **Examples**: [integration_example.py](integration_example.py)

### Troubleshooting
See [PERFORMANCE_PROFILES.md](PERFORMANCE_PROFILES.md) for a comprehensive troubleshooting section with solutions for:
- Wrong profile selected
- Frequent fallbacks
- Lower than expected throughput
- Out of memory issues

---

## File Structure

```
/workspaces/dev.c/
├── README.md                           ← START HERE
├── INTEGRATION_SUMMARY.md              ← Full overview
├── INTEGRATION_COMPLETE.md             ← Integration details
│
├── spec/
│   ├── performance_profiles.yaml       ← Spec (single source of truth)
│   └── profile_schema.json             ← JSON schema
│
├── performance_profiles.py             ← Core implementation
├── profile_integration.py              ← Integration module
├── test_performance_profiles.py        ← Tests (7/7 passing)
├── profile_cli.py                      ← CLI tool
│
├── INTEGRATION_GUIDE.py                ← Integration examples
├── integration_example.py              ← Working examples
│
├── PERFORMANCE_PROFILES.md             ← Complete guide
├── PERFORMANCE_PROFILES_QUICK_REFERENCE.md  ← Quick lookup
├── PERFORMANCE_PROFILES_DELIVERY_SUMMARY.md ← Delivery details
└── PERFORMANCE_PROFILES_FINAL_STATUS.md    ← Final report
```

---

## Next Steps

### 1. Try It Out
```bash
python3 profile_cli.py auto
```

### 2. Understand It
Read [PERFORMANCE_PROFILES_QUICK_REFERENCE.md](PERFORMANCE_PROFILES_QUICK_REFERENCE.md)

### 3. Integrate It
See integration examples in [integration_example.py](integration_example.py)

### 4. Clone and Modify
Use the profile system as a blueprint for your own compression engine

---

## Support

For questions or issues:
1. Check [PERFORMANCE_PROFILES.md](PERFORMANCE_PROFILES.md) FAQ section
2. Review examples in [integration_example.py](integration_example.py)
3. Run tests: `python3 profile_cli.py test`
4. Check integration guide: [INTEGRATION_GUIDE.py](INTEGRATION_GUIDE.py)

---

## Summary

The **Performance Profile System** provides automatic, deterministic performance tuning for the COBOL v1.5.3 compression engine.

**Key Benefits**:
- ✅ Optimal performance on any hardware  
- ✅ Deterministic and auditable  
- ✅ Safe automatic fallback  
- ✅ Zero impact on file format  
- ✅ Real-time monitoring  
- ✅ Language-agnostic  

**Status**: 🚀 **Production Ready**

---

**Version**: 1.0  
**Format**: COBOL v1.5.3  
**Date**: March 1, 2026  
**Contact**: Development Team  
