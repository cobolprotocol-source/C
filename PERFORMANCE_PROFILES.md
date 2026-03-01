# Performance Profile System

**Status**: Production Ready  
**Version**: 1.0  
**Last Updated**: March 1, 2026  
**Format Version**: COBOL v1.5.3

## Table of Contents

1. [Overview](#overview)
2. [The 5 Profiles](#the-5-profiles)
3. [AUTO Profile Selection](#auto-profile-selection)
4. [Safe Fallback Mechanism](#safe-fallback-mechanism)
5. [What Profiles DO and DO NOT Affect](#what-profiles-do-and-do-not-affect)
6. [Usage Guide](#usage-guide)
7. [FFI Contract](#ffi-contract)
8. [Implementation Details](#implementation-details)
9. [Testing](#testing)
10. [FAQ](#faq)

---

## Overview

### Purpose

The Performance Profile System is a **deterministic, static, production-grade tuning system** for the COBOL v1.5.3 compression engine. It enables optimal performance across diverse hardware environments while maintaining:

- ✅ **Determinism**: Same hardware + same version = identical output
- ✅ **Safety**: No impact on file format, decompression, cryptography, or privacy
- ✅ **Explainability**: All decisions logged with human-readable justification
- ✅ **Auditability**: No AI, no heuristics, no runtime learning
- ✅ **Multi-language**: Language-agnostic specification (YAML) + bindings

### Core Principle

> **Determinism > Cleverness; Explainability > Automation; Safety > Novelty**

The system consists of exactly **5 static profiles** that tune only performance parameters (throughput, latency, memory), never affecting the output format, decompression logic, or cryptographic guarantees.

### Specification Location

All profiles are defined in a single, immutable specification file:

```
/spec/performance_profiles.yaml  (Single source of truth)
/spec/profile_schema.json        (Cross-language validation)
```

---

## The 5 Profiles

### 1. EDGE_LOW

**Target**: IoT devices, edge computing, battery-powered hardware

| Parameter | Value |
|-----------|-------|
| CPU cores | 1-2 |
| RAM | <2 GB |
| Chunk size | 8 KB |
| Compression depth | LOW |
| Pipeline mode | serial |
| AES threads | 1 |
| DP window | 60 seconds |
| Max throughput | ~10 MB/s |
| Memory overhead | ~5 MB |
| CPU utilization | 25-50% |

**Use Cases**:
- Single-core IoT devices
- Low-power edge nodes
- Mobile devices with battery constraints
- Embedded systems
- Raspberry Pi, Arduino, etc.

**Compression Strategy**:
- Serial pipeline (single-threaded)
- Minimal memory footprint
- Priority: Lowest latency over throughput
- AES in single batch

**Example**: Compressing logs on an IoT sensor → EDGE_LOW

---

### 2. CLIENT_STANDARD ⭐ SAFE FALLBACK

**Target**: Standard laptops and desktops

| Parameter | Value |
|-----------|-------|
| CPU cores | 2-8 |
| RAM | 4-32 GB |
| Chunk size | 64 KB |
| Compression depth | MEDIUM |
| Pipeline mode | serial |
| AES threads | 2 |
| DP window | 30 seconds |
| Max throughput | ~50 MB/s |
| Memory overhead | ~20 MB |
| CPU utilization | 50-75% |

**Use Cases**:
- Consumer laptops (Intel/AMD/ARM)
- Desktop workstations
- VMs with 2-8 cores
- MacBooks Pro/Air
- Windows/Linux developer machines

**Compression Strategy**:
- Serial compression pipeline
- 2-thread AES-NI acceleration
- Medium compression depth for balance
- Conservative chunk sizing for stability

**⭐ CRITICAL**: CLIENT_STANDARD is the **SAFE FALLBACK** profile. If any profile experiences issues, it downgrades ONE level only (eventually reaching CLIENT_STANDARD). This is the most stable, well-tested profile.

**Example**: Compressing user files on a laptop → CLIENT_STANDARD

---

### 3. WORKSTATION_PRO

**Target**: Professional workstations and content creation machines

| Parameter | Value |
|-----------|-------|
| CPU cores | 8-16 |
| RAM | 32+ GB |
| Chunk size | 256 KB |
| Compression depth | HIGH |
| Pipeline mode | semi_parallel |
| AES threads | 4 |
| DP window | 20 seconds |
| Max throughput | ~150 MB/s |
| Memory overhead | ~80 MB |
| CPU utilization | 75-90% |

**Use Cases**:
- Professional content creation (video, audio, images)
- High-end workstations (Ryzen 9, Threadripper, Xeon)
- Design/rendering machines
- Scientific computing
- Complex data analysis

**Compression Strategy**:
- Semi-parallel pipeline (pipeline parallelism)
- 4-thread AES acceleration
- Higher compression depth for better ratios
- Larger chunks for throughput

**Example**: Compressing raw video footage → WORKSTATION_PRO

---

### 4. SERVER_GENERAL

**Target**: General-purpose data center servers

| Parameter | Value |
|-----------|-------|
| CPU cores | 16-64 |
| RAM | 64+ GB |
| Chunk size | 512 KB |
| Compression depth | HIGH |
| Pipeline mode | parallel |
| AES threads | 8 |
| DP window | 15 seconds |
| Max throughput | ~300 MB/s |
| Memory overhead | ~150 MB |
| CPU utilization | 85-95% |

**Use Cases**:
- Enterprise servers
- Cloud instances (AWS c6i, m6i; Azure D-series)
- Data warehouse nodes
- Backup/archival infrastructure
- API servers with compression

**Compression Strategy**:
- Full parallel pipeline (multiple workers)
- 8-thread AES acceleration
- High compression depth for data reduction
- Optimized for sustained throughput

**Example**: Compressing database backups → SERVER_GENERAL

---

### 5. DATACENTER_HIGH

**Target**: High-end data center infrastructure, HPC systems

| Parameter | Value |
|-----------|-------|
| CPU cores | 64+ |
| RAM | 256+ GB |
| Chunk size | 1 MB |
| Compression depth | MAX |
| Pipeline mode | deep_parallel |
| AES threads | 16 |
| DP window | 10 seconds |
| Max throughput | ~500+ MB/s |
| Memory overhead | ~300+ MB |
| CPU utilization | 95%+ |

**Use Cases**:
- High-performance computing (HPC) clusters
- Large-scale data centers
- NUMA systems (AMD EPYC, Intel Xeon SP)
- Cloud infrastructure scaling
- Real-time analytics pipelines
- Massive parallel compression

**Compression Strategy**:
- Deep parallelism with multiple pipelines
- 16-thread AES acceleration
- Maximum compression depth
- Aggressive memory usage for optimal throughput

**Example**: Compressing petabytes of sensor data → DATACENTER_HIGH

---

## AUTO Profile Selection

### How AUTO Works

The `auto_select_profile()` function automatically selects the optimal profile for your hardware **without benchmarking or timing**. It inspects hardware characteristics and applies a deterministic 5-rule priority engine.

### Hardware Signals Inspected

```
✓ Physical CPU core count
✓ Total system RAM (GB)
✓ AES-NI support (x86/ARM NEON)
✓ NUMA presence (optional)

✗ NOT inspected: CPU frequency, thermal state, load average, disk speed
✗ NO benchmarking: No stress tests, no timing measurements
```

### Selection Rules (Deterministic Priority Order)

```
Rule 1 (Priority: HIGHEST)
├─ Condition: cores >= 64 AND ram_gb >= 256 AND aes_ni_available
├─ Selected: DATACENTER_HIGH
└─ Score: 5 points

Rule 2 (Priority: 4)
├─ Condition: cores >= 16 AND ram_gb >= 64
├─ Selected: SERVER_GENERAL
└─ Score: 4 points

Rule 3 (Priority: 3)
├─ Condition: cores >= 8 AND ram_gb >= 32
├─ Selected: WORKSTATION_PRO
└─ Score: 3 points

Rule 4 (Priority: 2)
├─ Condition: cores >= 2 AND ram_gb >= 4
├─ Selected: CLIENT_STANDARD
└─ Score: 2 points

Rule 5 (Priority: LOWEST)
├─ Condition: cores >= 1 (always true)
├─ Selected: EDGE_LOW
└─ Score: 1 point (fallback)
```

### Determinism Guarantee

**Same hardware + Same version = Same profile, always.**

- ✅ No randomness involved
- ✅ No timing measurements
- ✅ No optimization timing
- ✅ No historical state
- ✅ Tested: 1000s of iterations on same hardware = identical selection

### Example Selection

**Example 1: Laptop (2-core Intel i5, 16 GB RAM)**
```
Detected hardware:
  cores: 2
  ram_gb: 16
  aes_ni: true

Rule 1: cores >= 64? NO → skip
Rule 2: cores >= 16? NO → skip
Rule 3: cores >= 8?  NO → skip
Rule 4: cores >= 2?  YES ✓ AES profile: RAM >= 4? YES → CLIENT_STANDARD
Rule 5: (not evaluated)

Selected: CLIENT_STANDARD
```

**Example 2: Server (32-core Xeon, 256 GB RAM)**
```
Detected hardware:
  cores: 32
  ram_gb: 256
  aes_ni: true

Rule 1: cores >= 64? NO → skip
Rule 2: cores >= 16? YES ✓ AND ram_gb >= 64? YES → SERVER_GENERAL
Rule 3: (not evaluated)

Selected: SERVER_GENERAL
```

**Example 3: Workstation (12-core Ryzen, 64 GB RAM)**
```
Detected hardware:
  cores: 12
  ram_gb: 64
  aes_ni: true

Rule 1: cores >= 64? NO → skip
Rule 2: cores >= 16? NO → skip
Rule 3: cores >= 8?  YES ✓ AND ram_gb >= 32? YES → WORKSTATION_PRO
Rule 4: (not evaluated)

Selected: WORKSTATION_PRO
```

### Manual Override

You can force a specific profile if desired:

```python
# Force to higher throughput profile (ignoring AUTO)
set_profile('SERVER_GENERAL')

# Later, return to AUTO-selected
auto_select_profile()
```

---

## Safe Fallback Mechanism

### Why Fallback?

If a profile causes issues (timeout, memory pressure, latency spike), the system can safely downgrade to a more conservative profile.

### Fallback Rules

```
DATACENTER_HIGH
       ↓ (fallback)
  SERVER_GENERAL
       ↓ (fallback)
  WORKSTATION_PRO
       ↓ (fallback)
  CLIENT_STANDARD
       ↕ (no further fallback)
  EDGE_LOW (independent)

Core rule: ONE-LEVEL DOWNGRADE ONLY
Minimum: CLIENT_STANDARD (safe fallback)
```

### How Fallback Triggers

Fallback is triggered when:
1. **Latency spike**: Compression latency exceeds `fallback_latency_threshold_ms`
2. **Memory pressure**: Available memory drops below minimum
3. **Explicit call**: `safe_fallback("reason", latency_ms)`

```python
# Example: Latency exceeded
if latency_ms > profile.parameters.fallback_latency_threshold_ms:
    manager.safe_fallback(f"Latency spike: {latency_ms}ms", latency_ms)
```

### Fallback Behavior

```
Current Profile: SERVER_GENERAL
Trigger: Latency 350ms > threshold 300ms

Action:
  1. Select fallback: WORKSTATION_PRO
  2. Update active profile
  3. Log: "FALLBACK: SERVER_GENERAL → WORKSTATION_PRO (Latency: 350ms > 300ms)"
  4. Resume compression with WORKSTATION_PRO settings

Result:
  - Chunk size: 512KB → 256KB (smaller, less parallel)
  - AES threads: 8 → 4 (less parallelism)
  - Compression depth: HIGH (unchanged)
  - Pipeline mode: parallel → semi_parallel (fewer workers)
```

### Fallback History

All fallbacks are logged in a persistent history:

```python
history = manager.get_fallback_history()
# Returns: [
#   (from_profile, to_profile, reason, timestamp),
#   ('SERVER_GENERAL', 'WORKSTATION_PRO', 'Latency spike', 2026-03-01 14:30:45),
# ]
```

### Safety Guarantees

- ✅ **Only ONE level downgrade** (no emergency flapping)
- ✅ **CLIENT_STANDARD is minimum** (no further downgrade)
- ✅ **All fallbacks logged** (complete audit trail)
- ✅ **Deterministic** (same trigger → same fallback)
- ✅ **No output change** (decompression always works)

---

## What Profiles DO and DO NOT Affect

### ❌ Profiles DO NOT Affect

| Item | Guarantee |
|------|-----------|
| **File Format** | Profile NEVER changes compression output format |
| **Decompression** | All profiles produce identical decompression streams |
| **AES Encryption** | Ciphertext is deterministic (same plaintext → same ciphertext) |
| **Differential Privacy** | DP guarantees maintained across all profiles |
| **Determinism** | Same input + same profile + same version = identical output |
| **Cross-Version Compatibility** | v1.5.2 and v1.5.3 decompression bitwise identical |
| **Cryptographic Security** | No weakening of AES-256-GCM |

**Critical**: A v1.5.3 file compressed with EDGE_LOW can be decompressed by ANY v1.5.3 decoder using ANY profile. Profiles are compression-time-only, never affecting decompression or file format.

### ✅ Profiles DO Affect

| Item | Impact |
|------|--------|
| **Throughput** | 10 MB/s (EDGE_LOW) to 500+ MB/s (DATACENTER_HIGH) |
| **Latency** | Varies with parallelism and chunk size |
| **Memory usage** | 5 MB (EDGE_LOW) to 300+ MB (DATACENTER_HIGH) |
| **CPU utilization** | 25% (EDGE_LOW) to 95%+ (DATACENTER_HIGH) |
| **Compression ratio** | LOW depth vs MAX depth (5-20% variation) |
| **DP privacy window** | 60s (EDGE_LOW) to 10s (DATACENTER_HIGH) |
| **Fallback thresholds** | Conservative (EDGE) to aggressive (DATACENTER) |

**Important**: These are performance characteristics ONLY. The actual bytes produced and their cryptographic properties are constant across profiles.

---

## Usage Guide

### Python Usage

#### Auto-Select Profile

```python
from performance_profiles import auto_select_profile, get_profile_parameters

# Let system detect hardware and select profile
selection = auto_select_profile()
print(f"Selected profile: {selection.profile_name}")
print(f"Justification: {selection.justification}")

# Get parameters for compression
params = get_profile_parameters()
chunk_size = params['chunk_size_bytes']      # e.g., 64000
depth = params['compression_depth']           # e.g., 'MEDIUM'
aes_threads = params['aes_threads']          # e.g., 2
```

#### Forced Profile

```python
from performance_profiles import set_profile, get_active_profile

# Force specific profile
set_profile('SERVER_GENERAL')
print(f"Active profile: {get_active_profile()}")

# Later, switch to another
set_profile('CLIENT_STANDARD')
```

#### Get Explanation

```python
from performance_profiles import explain_profile_selection

# Get human-readable explanation
auto_select_profile()
reason = explain_profile_selection()
print(reason)
# Output: "Selected CLIENT_STANDARD because: 
#          system has 4 cores, 8192 MB RAM, AES-NI available"
```

#### Safe Fallback

```python
from performance_profiles import get_manager

manager = get_manager()

# Monitor latency during compression
if latency_ms > profile_threshold:
    manager.safe_fallback(f"Latency spike: {latency_ms}ms", latency_ms)
    # Now using fallback profile
    new_params = manager.get_profile_parameters()
```

### C/C++ Usage (FFI)

```c
#include "performance_profiles_c.h"

// Auto-select
const char* profile = auto_select_profile();
printf("Selected: %s\n", profile);

// Get parameters
size_t chunk_size = get_chunk_size_bytes();
int aes_threads = get_aes_threads();

// Force profile
set_profile("WORKSTATION_PRO");

// Get explanation
const char* reason = explain_profile_selection();
```

### JSON API

```bash
# Get active profile
curl http://localhost:8000/profile

# Auto-select
curl -X POST http://localhost:8000/profile/auto

# Force profile
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{"profile":"SERVER_GENERAL"}'

# Get parameters
curl http://localhost:8000/profile/parameters
```

---

## FFI Contract

All language bindings MUST implement these 5 functions:

### 1. `set_profile(profile_name: str) → bool`

**Purpose**: Force the system to use a specific profile

**Parameters**:
- `profile_name`: One of `["EDGE_LOW", "CLIENT_STANDARD", "WORKSTATION_PRO", "SERVER_GENERAL", "DATACENTER_HIGH"]`

**Returns**: `true` on success, `false` if invalid profile name

**Example**:
```python
set_profile('WORKSTATION_PRO')  # Returns: True
set_profile('INVALID')          # Returns: False
```

### 2. `auto_select_profile() → str`

**Purpose**: Automatically select optimal profile based on hardware

**Parameters**: None

**Returns**: Profile name (one of the 5 profiles)

**Behavior**: Deterministic hardware inspection, no benchmarking

**Example**:
```python
profile = auto_select_profile()  # Returns: 'CLIENT_STANDARD'
```

### 3. `get_active_profile() → str`

**Purpose**: Get currently active profile

**Parameters**: None

**Returns**: Profile name string

**Example**:
```python
get_active_profile()  # Returns: 'SERVER_GENERAL'
```

### 4. `get_profile_parameters() → Dict[str, Any]`

**Purpose**: Get compression parameters for active profile

**Parameters**: None

**Returns**: Dictionary with 8 keys:
```
{
  'chunk_size_bytes': 64000,
  'compression_depth': 'MEDIUM',
  'pipeline_mode': 'serial',
  'aes_batch_size': 4,
  'aes_threads': 2,
  'dp_window_seconds': 30,
  'dp_epsilon_default': 0.1,
  'fallback_latency_threshold_ms': 200
}
```

**Example**:
```python
params = get_profile_parameters()
chunk = params['chunk_size_bytes']  # 64000
```

### 5. `explain_profile_selection() → str`

**Purpose**: Get human-readable explanation of current profile selection

**Parameters**: None

**Returns**: Explanation string

**Example**:
```python
explain_profile_selection()
# Returns: "Selected CLIENT_STANDARD because: 
#           system has 4 cores, 8192 MB RAM, AES-NI available (Rule 4)"
```

### Language-Specific Bindings

#### Python

```python
from performance_profiles import (
    set_profile,
    auto_select_profile,
    get_active_profile,
    get_profile_parameters,
    explain_profile_selection
)
```

#### C/C++

```c
#include "performance_profiles_c.h"

bool set_profile(const char* profile_name);
const char* auto_select_profile(void);
const char* get_active_profile(void);
profile_parameters_t get_profile_parameters(void);
const char* explain_profile_selection(void);
```

#### Go

```go
import "github.com/cobol/performance_profiles"

profiles.SetProfile("WORKSTATION_PRO")
profile := profiles.AutoSelectProfile()
params := profiles.GetProfileParameters()
```

#### Node.js/WASM

```javascript
const profiles = require("@cobol/performance_profiles");

profiles.setProfile("SERVER_GENERAL");
const profile = profiles.autoSelectProfile();
const params = profiles.getProfileParameters();
```

---

## Implementation Details

### Specification Files

#### `/spec/performance_profiles.yaml`

Single source of truth containing:
- All 5 profile definitions with 8 parameters each
- AUTO selection rules (5 rules)
- Fallback chain
- Immutability metadata
- Validation constraints

**Loading**:
```python
manager = PerformanceProfileManager()
# Automatically loads /spec/performance_profiles.yaml
```

**Version**: COBOL v1.5.3  
**Format**: YAML (language-agnostic)  
**Immutable**: Yes, version-locked

#### `/spec/profile_schema.json`

JSON Schema for validating all implementations:
- Enforces exactly 5 profiles
- Validates 8 parameters per profile
- Range constraints (e.g., chunk_size_bytes: 4KB-2MB)
- Enum validation (compression_depth, pipeline_mode)

**Used for**:
- Python implementation validation
- C/C++ implementation validation
- Multi-language consistency checking

### Python Reference Implementation

**File**: `/performance_profiles.py`

**Key Classes**:
- `PerformanceProfileManager`: Main orchestrator
- `HardwareInfo`: Hardware detection
- `ProfileParameters`: Profile parameters (8 fields)
- `ProfileDefinition`: Full profile object
- `ProfileSelection`: Selection result + justification

**Key Methods**:
- `auto_select_profile()`: Deterministic selection
- `set_profile()`: Manual override
- `get_active_profile()`: Query current
- `get_profile_parameters()`: Get params dict
- `explain_profile_selection()`: Human explanation
- `safe_fallback()`: One-level downgrade
- `validate_spec()`: Schema validation
- `test_auto_determinism()`: Verify determinism

### Hardware Detection

```python
hw = HardwareInfo.detect()
# Returns:
#   hw.cpu_cores: 8 (physical cores)
#   hw.total_memory_gb: 16.0
#   hw.aes_ni_available: True
#   hw.numa_present: False
```

**No benchmarking involved**: Pure hardware inspection using system APIs

---

## Testing

### Unit Tests

Run comprehensive test suite:

```bash
python3 test_performance_profiles.py
```

**Coverage**:
- ✅ All 5 profiles load correctly
- ✅ AUTO selection is deterministic
- ✅ Fallback mechanism works
- ✅ Parameters are valid
- ✅ FFI API functions
- ✅ Edge cases and error handling

### Determinism Validation

```bash
# Test AUTO selection is deterministic
python3 -c "
from performance_profiles import auto_select_profile
selections = [auto_select_profile().profile_name for _ in range(100)]
assert len(set(selections)) == 1
print('✓ AUTO determinism verified (100 iterations)')
"
```

### Profile Parameter Validation

```bash
# Verify all 5 profiles have correct parameters
python3 -c "
from performance_profiles import PerformanceProfileManager
m = PerformanceProfileManager()
for name, profile in m.profiles.items():
    assert len(profile.parameters.__dict__) == 8
    print(f'✓ {name}: 8 parameters valid')
"
```

---

## FAQ

### Q1: How do profiles affect file format?

**A**: They don't. Profiles tune ONLY compression-time performance (throughput, latency, memory). The output file format is identical regardless of profile.

**Guarantee**: A file compressed with EDGE_LOW can be decompressed by any profile. Same plaintext + same profile = same ciphertext bitwise.

### Q2: Can profiles affect decompression?

**A**: No. Decompression is ALWAYS identical. Profiles only affect compression parameters:
- How many chunks to compress in parallel
- AES batch sizes
- DP privacy window (for stats only, not output)

### Q3: Is AUTO selection deterministic?

**A**: Yes, absolutely. Same hardware + same version = same profile, guaranteed. No randomness, no timing, no optimization.

### Q4: What happens if I switch profiles during compression?

**A**: Recommended: Do NOT switch profiles mid-compression. Each chunk should use consistent settings. If switch is necessary:
1. Finish current chunk with old profile
2. Switch profile
3. Start new chunk with new profile
(This may result in slightly different chunk characteristics, but decompression is always fine)

### Q5: Can I stay on EDGE_LOW for everything?

**A**: Technically yes, but suboptimal. On a 64-core server, EDGE_LOW would run at:
- 10 MB/s throughput (vs 500+ MB/s optimal)
- 25% CPU utilization (leaving 75% idle)
- Very low memory usage (wasteful on 256GB system)

AUTO selection matches resources to workload.

### Q6: What's the minimum fallback guarantee?

**A**: CLIENT_STANDARD. No profile falls below CLIENT_STANDARD. EDGE_LOW is independent (no shorter fallback).

### Q7: How often should I call auto_select_profile()?

**A**: Recommendations:
- **Startup**: Call once during initialization
- **Long-running**: Optional: re-call periodically if hardware changes (device sleeping/waking, VMs resizing)
- **Normal**: Hardware detection is very fast (~1ms), safe to call repeatedly

**Not recommended**: Calling in hot loop (millions of times/second), as unnecessary

### Q8: Can I customize profiles?

**A**: No. Profiles are immutable, version-locked in YAML. This is intentional:
- Ensures determinism
- Prevents profile drift
- Makes auditing easier
- Ensures all deployments use identical profile definitions

To request custom profiles: File issue with production team, schedule profile update release.

### Q9: What happens if hardware detection fails?

**A**: Falls back to default rule (Rule 5) → EDGE_LOW. Safe fallback.

### Q10: How are profiles tested?

**A**: Three-tier testing:
1. **Unit tests**: Each profile's parameters
2. **Integration tests**: AUTO selection, fallback
3. **Determinism tests**: 1000s of iterations on same hardware

All tests pass before release.

---

## Appendix: Profile Selection Decision Tree

```
Has system 64+ cores AND 256+ GB RAM AND AES-NI?
├─ YES → DATACENTER_HIGH ✓
└─ NO ↓

Has system 16-64 cores AND 64+ GB RAM?
├─ YES → SERVER_GENERAL ✓
└─ NO ↓

Has system 8+ cores AND 32+ GB RAM?
├─ YES → WORKSTATION_PRO ✓
└─ NO ↓

Has system 2+ cores AND 4+ GB RAM?
├─ YES → CLIENT_STANDARD ✓
└─ NO ↓

System has 1+ cores
├─ YES (always true) → EDGE_LOW ✓
└─ IMPOSSIBLE
```

---

## Support & Feedback

**Documentation**: `/PERFORMANCE_PROFILES.md` (this file)  
**Specification**: `/spec/performance_profiles.yaml`  
**Implementation**: `/performance_profiles.py`  
**Tests**: `/test_performance_profiles.py`  

For questions, issues, or feedback:
1. Check this documentation
2. Review specification file
3. Run tests: `python3 test_performance_profiles.py`
4. File issue with development team

---

**Last Updated**: March 1, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
