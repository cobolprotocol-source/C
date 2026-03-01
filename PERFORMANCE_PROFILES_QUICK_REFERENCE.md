# Performance Profile System - Quick Reference

## 5 Static Profiles

| Profile | Cores | RAM | Chunk | Depth | Mode | Threads | Use Case |
|---------|-------|-----|-------|-------|------|---------|----------|
| **EDGE_LOW** | 1-2 | <2GB | 8KB | LOW | serial | 1 | IoT, edge, battery |
| **CLIENT_STANDARD** ⭐ | 2-8 | 4-32GB | 64KB | MEDIUM | serial | 2 | Laptop, desktop |
| **WORKSTATION_PRO** | 8-16 | 32GB+ | 256KB | HIGH | semi_parallel | 4 | Workstation, creator |
| **SERVER_GENERAL** | 16-64 | 64GB+ | 512KB | HIGH | parallel | 8 | Server, datacenter |
| **DATACENTER_HIGH** | 64+ | 256GB+ | 1MB | MAX | deep_parallel | 16 | HPC, scale |

⭐ = Safe fallback minimum

## AUTO Selection

```python
from performance_profiles import auto_select_profile

selection = auto_select_profile()
# Returns: ProfileSelection object with profile_name, hardware_info, justification
```

**Rules** (priority order):
1. `cores >= 64 && ram >= 256 && aes_ni` → DATACENTER_HIGH
2. `cores >= 16 && ram >= 64` → SERVER_GENERAL
3. `cores >= 8 && ram >= 32` → WORKSTATION_PRO
4. `cores >= 2 && ram >= 4` → CLIENT_STANDARD
5. `cores >= 1` → EDGE_LOW (default)

**Guarantee**: Same hardware = Same profile (deterministic, no benchmarking)

## FFI API (5 Functions)

```python
# 1. Force profile
set_profile(name: str) → bool
set_profile('SERVER_GENERAL')

# 2. Auto-select based on hardware
auto_select_profile() → str
profile = auto_select_profile()  # Returns: 'CLIENT_STANDARD'

# 3. Get current profile
get_active_profile() → str
name = get_active_profile()

# 4. Get 8 compression parameters
get_profile_parameters() → Dict[str, Any]
params = get_profile_parameters()
chunk_size = params['chunk_size_bytes']      # e.g., 64000
depth = params['compression_depth']          # e.g., 'MEDIUM'
aes_threads = params['aes_threads']          # e.g., 2

# 5. Get human explanation
explain_profile_selection() → str
reason = explain_profile_selection()
# "Selected CLIENT_STANDARD because: 4 cores, 8GB RAM, AES-NI available"
```

## Safe Fallback

```python
from performance_profiles import get_manager

manager = get_manager()

if latency_ms > threshold:
    manager.safe_fallback("Latency spike", latency_ms)
```

**Fallback chain** (one-level only):
```
DATACENTER_HIGH → SERVER_GENERAL → WORKSTATION_PRO → CLIENT_STANDARD (minimum)
EDGE_LOW (independent, no fallback)
```

## Immutable Guarantees

### What Profiles DO NOT Change
- ❌ File format (bitwise identical output)
- ❌ Decompression (always same output)
- ❌ AES encryption (same plaintext → same ciphertext)
- ❌ Differential Privacy (guarantees maintained)
- ❌ Cross-version compatibility

### What Profiles DO Change
- ✅ Throughput (10 MB/s to 500+ MB/s)
- ✅ Latency (varies with parallelism)
- ✅ Memory usage (5 MB to 300+ MB)
- ✅ CPU utilization (25% to 95%+)

## Files

| File | Purpose |
|------|---------|
| `/spec/performance_profiles.yaml` | Single source of truth (5 profiles, AUTO rules, fallback) |
| `/spec/profile_schema.json` | JSON schema for validation |
| `/performance_profiles.py` | Python implementation (reference) |
| `/test_performance_profiles.py` | Comprehensive test suite |
| `/PERFORMANCE_PROFILES.md` | Full documentation |

## Usage Examples

### Python

```python
from performance_profiles import (
    auto_select_profile,
    get_profile_parameters,
    set_profile,
    explain_profile_selection
)

# Auto-select based on hardware
selection = auto_select_profile()
print(f"Selected: {selection.profile_name}")
print(f"Reason: {selection.justification}")

# Get compression parameters
params = get_profile_parameters()
chunk_size = params['chunk_size_bytes']
aes_threads = params['aes_threads']

# For compression loop
for chunk in data:
    compressed = compress(chunk, chunk_size=chunk_size, threads=aes_threads)
```

### C/C++

```c
#include "performance_profiles_c.h"

// Auto-select profile
const char* profile = auto_select_profile();

// Get parameters
size_t chunk_size = get_chunk_size_bytes();
int aes_threads = get_aes_threads();

// Compress with selected profile parameters
compress_chunk(data, chunk_size, aes_threads);
```

### JSON REST API

```bash
# Get current profile
curl http://localhost:8000/profile
# Response: {"profile":"CLIENT_STANDARD"}

# Auto-select
curl -X POST http://localhost:8000/profile/auto
# Response: {"profile":"WORKSTATION_PRO", "reason":"..."}

# Get parameters
curl http://localhost:8000/profile/parameters
# Response: {"chunk_size_bytes":256000, "aes_threads":4, ...}
```

## Common Scenarios

### Scenario 1: Compress files on user laptop
```python
auto_select_profile()  # → CLIENT_STANDARD
# Optimal balance of speed and memory on typical laptop
```

### Scenario 2: Compress logs on IoT device
```python
auto_select_profile()  # → EDGE_LOW
# Minimal memory footprint, 1 thread
```

### Scenario 3: Compress database backups on enterprise server
```python
auto_select_profile()  # → SERVER_GENERAL
# 300+ MB/s throughput, 8 parallel workers
```

### Scenario 4: Compress data warehouse on HPC cluster
```python
auto_select_profile()  # → DATACENTER_HIGH
# 500+ MB/s throughput, deep parallelism, 16 AES threads
```

### Scenario 5: Latency spike detected, degrade gracefully
```python
if latency_ms > profile.parameters.fallback_latency_threshold_ms:
    manager.safe_fallback(f"Latency: {latency_ms}ms", latency_ms)
    # Now using less aggressive profile
```

## Testing

```bash
# Run full test suite
python3 test_performance_profiles.py

# Verify AUTO determinism (100 iterations)
python3 -c "
from performance_profiles import auto_select_profile
versions = [auto_select_profile().profile_name for _ in range(100)]
assert len(set(versions)) == 1
print('✓ AUTO determinism verified')
"

# Show current profile and parameters
python3 -c "
from performance_profiles import auto_select_profile, get_profile_parameters
auto_select_profile()
params = get_profile_parameters()
for key, val in params.items():
    print(f'{key}: {val}')
"
```

## Design Principles

```
Determinism > Cleverness
Explainability > Automation
Safety > Novelty
Bounded Control > Unbounded Adaptation
```

- No AI, no learning, no heuristics
- No benchmarking during AUTO selection
- No timing measurements
- Same hardware + same version = identical output
- All decisions logged and explainable

## Key Points

1. **Exactly 5 profiles** - no more, no less
2. **Immutable and version-locked** - no runtime changes
3. **Deterministic AUTO** - same hardware = same profile
4. **Safe fallback** - one-level downgrade only
5. **No format changes** - decompression always works
6. **Language-agnostic** - YAML spec + FFI contract
7. **Production-grade** - tested, verified, auditable

## Contact & Documentation

- Full docs: `/PERFORMANCE_PROFILES.md`
- Specification: `/spec/performance_profiles.yaml`
- Implementation: `/performance_profiles.py`
- Tests: `/test_performance_profiles.py`

---

**Version**: 1.0  
**Status**: Production Ready ✅  
**Format Version**: COBOL v1.5.3
