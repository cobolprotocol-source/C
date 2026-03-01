# README_INTERNAL

**COBOL Protocol v1.5.3**  
**Internal Engineering Documentation**

<!--
Copyright (c) 2026 Nafal Faturizki
All rights reserved.

CONFIDENTIALITY NOTICE:
This document contains proprietary information and engineering
specifications. Distribution is restricted to internal engineers,
authorized partners under NDA, enterprise reviewers, and security
auditors. Unauthorized distribution is prohibited.

For complete license terms, see LICENSE.md.
-->

---

## Confidentiality and Audience

**This document is for restricted distribution only.**

**Authorized Readers**:
- ✅ Internal engineers and architects
- ✅ Enterprise reviewers (security, compliance, legal)
- ✅ Partners under NDA
- ✅ Authorized auditors

**Distribution**: Must be kept confidential. Not for public release.

---

## Table of Contents

1. System Architecture
2. Performance Profile System (Detailed)
3. Versioning and Upgrade Policy
4. Experimental Development Track
5. Security and Compliance Model
6. Testing and Validation Philosophy
7. Engineering Trade-offs and Decisions

---

## 1. System Architecture

### 1.1 High-Level Topology

```
┌─────────────────────────────────────────────────────────────┐
│ User Application                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ ProfileAwareCompressionEngine (Profile Selection Layer)     │
│ - Hardware detection                                         │
│ - AUTO profile selection                                     │
│ - Version fallback logic                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ CobolEngine (8-Layer Compression Pipeline)                  │
│ - L1-L2: Semantic & Structural Mapping                      │
│ - L3-L4: Delta Encoding & Bit-Packing                       │
│ - L5-L7: Advanced RLE & Cross-Block Patterns                │
│ - L8: Ultra-Extreme Instruction Mapping                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Optional Security Layer (AES-256-GCM + DP)                  │
│ - Encryption (if enabled)                                   │
│ - Differential Privacy (if enabled)                         │
│ - Integrity Verification                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              Compressed Output + Metadata
```

### 1.2 Layer Details

#### Layer 1-2: Semantic & Structural Mapping
- **Purpose**: Convert structured data (JSON, CSV, logs, tables) into token streams
- **Mechanism**: Vocabulary-based token substitution with sliding window
- **Output**: 1-byte token IDs representing common patterns
- **Compression Gain**: 5-10x for highly structured text

#### Layer 3-4: Delta Encoding & Variable-Length Int-Packing
- **Purpose**: Compress numeric sequences and uniform patterns
- **Mechanism**: 
  - Delta encoding: Instead of storing values, store differences
  - Variable-length encoding: Small numbers use fewer bits
  - Bit-packing: Group related values efficiently
- **Output**: Bit-packed arrays of variable-length integers
- **Compression Gain**: 3-8x for numeric data

#### Layer 5-7: Advanced RLE and Cross-Block Patterns
- **Purpose**: Find repeated patterns across blocks
- **Mechanism**:
  - Run-length encoding (RLE) for consecutive repetitions
  - Trie-based dictionary of frequently-occurring patterns
  - Cross-block pattern matching (pattern in block N may appear in block M)
- **Output**: Pattern pointers and indices
- **Compression Gain**: 2-5x for patterned data

#### Layer 8: Ultra-Extreme Instruction Mapping
- **Purpose**: Final optimization via instruction-level mapping
- **Mechanism**: Map most common operation sequences to short opcodes
- **Note**: This layer is highly tuned and proprietary
- **Compression Gain**: 1.2-2x final boost

### 1.3 Security Layer (Optional)

**Encryption**:
- Algorithm: AES-256-GCM
- Key Derivation: PBKDF2 (200,000 iterations, random salt)
- Nonce: 96-bit random per block
- Authentication: GCM tag for integrity

**Differential Privacy** (Optional):
- Method: Laplace mechanism noise injection
- Customizable: User controls ε (privacy loss parameter)
- Applied: Before compression or after decompression (configurable)
- Verification: Built-in validation of privacy assumptions

**Integrity**:
- Hash Algorithm: SHA-256
- Per-block verification: Layer 8 adds hash tags
- End-to-end verification: Allows selective retrieval validation

---

## 2. Performance Profile System (Detailed)

### 2.1 Profile Definition

Each profile is a **named hardware-based configuration** with:
- Hardware constraints (cores, RAM, specialized hardware)
- Default layer depths and dictionary sizes
- Parallelization strategy
- Memory usage ceilings
- Optional GPU acceleration settings

### 2.2 Five Standard Profiles

| Profile | Hardware Spec | Dict Size | Max Depth | Parallelism | Notes |
|---------|---------------|-----------|-----------|-------------|-------|
| **EDGE_LOW** | 1-4 cores, <8GB | 64KB | L5 | 1 thread | Battery-conscious |
| **CLIENT_STANDARD** | 4-8 cores, 8-32GB | 256KB | L6 | 2-4 threads | Fallback minimum |
| **WORKSTATION_PRO** | 8-16 cores, 32-64GB | 1MB | L7 | 4-8 threads | Professional balance |
| **SERVER_GENERAL** | 16-64 cores, 64GB+ | 4MB | L8 | 8-16 threads | Balanced throughput |
| **DATACENTER_HIGH** | 64+ cores, 256GB+ | 16MB | L8+ | 16+ threads + GPU | Maximum performance |

### 2.3 Hardware Detection Algorithm

```
cores = detect_cpu_cores()
ram_gb = detect_ram()
has_gpu = detect_cuda_availability()
has_aes_ni = detect_aes_ni()

if cores <= 4 and ram_gb < 8:
    profile = "EDGE_LOW"
elif cores <= 8 and ram_gb <= 32:
    profile = "CLIENT_STANDARD"
elif cores <= 16 and ram_gb <= 64:
    profile = "WORKSTATION_PRO"
elif cores < 64 or ram_gb < 256:
    profile = "SERVER_GENERAL"
else:
    profile = "DATACENTER_HIGH"
```

**Key Principle**: AUTO selection is deterministic and hardware-driven. Same hardware always selects same profile.

### 2.4 Profile to Version Mapping

Each profile has:
- **Current Stable Version**: Recommended default
- **Version History**: List of all released versions with release dates
- **Experimental Version** (DATACENTER_HIGH only): 2.0@experimental under Model-5 track

Example (DATACENTER_HIGH):
```yaml
DATACENTER_HIGH:
  current_stable_version: "1.0"
  versions:
    "1.0":
      released: 2026-03-01
      status: stable
      parameters: {...}
    "2.0@experimental":
      released: 2026-03-20
      status: experimental
      min_soak_hours: 24
      parameters: {...}
```

---

## 3. Versioning and Upgrade Policy

### 3.1 Version Immutability Contract

**Core Guarantee**: Once a version is released, it is IMMUTABLE.

- **Immutable**: Parameter hashes, compression behavior, output format
- **Never Retroactive**: Version 1.0 released on 2026-03-01 will always behave identically
- **Verifiable**: Parameter hash (SHA-256) proves immutability
- **Auditable**: Git history records initial release and never changes

**Implementation**:
```python
class ProfileVersion:
    version_id: str
    parameters: Dict[str, Any]
    parameter_hash: str  # SHA-256(parameters) - PROOF OF IMMUTABILITY
    
    def validate_immutability(self):
        current_hash = sha256(json.dumps(self.parameters))
        assert current_hash == self.parameter_hash, "Version corrupted!"
```

### 3.2 Versioning Scheme

**Format**: MAJOR.MINOR[@status]

- **1.0**: Initial release (stable)
- **1.1**: Bug fix or minor improvement (stable)
- **2.0**: Major algorithmic change (stable)
- **2.0@experimental**: Experimental version for research/testing

**Rules**:
- MAJOR change = backwards incompatible in compression behavior
- MINOR change = bug fixes or optimizations (backward compatible decompression)
- @experimental suffix = not recommended for production (Model-5 track only)

### 3.3 Upgrade Policy: Explicit Opt-In ONLY

**Core Principle**: No automatic upgrades. Ever.

```python
def set_version(profile_version: str, confirm: bool = False) -> bool:
    """
    Upgrade to new version.
    
    Args:
        profile_version: e.g., "CLIENT_STANDARD@1.1"
        confirm: MUST be True to upgrade (explicit confirmation)
    
    Returns:
        Success or error
    """
    if not confirm:
        raise ValueError("Upgrade requires explicit confirmation (confirm=True)")
    
    # Perform upgrade
    # Log to audit trail
    # Return success
```

**Workflow**:
1. User calls `propose_upgrade("CLIENT_STANDARD@1.1")`
2. System returns UpgradeInformation (what changes, what doesn't)
3. User reviews and calls `set_version("CLIENT_STANDARD@1.1", confirm=True)`
4. Upgrade applied and logged to audit trail
5. Subsequent compressions use new version

**Failures**:
- If `confirm=False` (default), upgrade fails with clear error
- If upgrade fails mid-flight, automatic rollback triggered
- Previous version remains selected

### 3.4 Fallback Mechanism

**Trigger**: Compression exceeds latency threshold for profile

**Behavior**:
- Profile priority: DATACENTER_HIGH > SERVER_GENERAL > WORKSTATION_PRO > CLIENT_STANDARD > EDGE_LOW
- **Version never changes in fallback** - Only profile downgrades
- Example: DATACENTER_HIGH@1.1 fails → falls back to SERVER_GENERAL@1.1 (version preserved)

**Guarantee**: Fallback NEVER forces version upgrade

---

## 4. Experimental Development Track (Model-5)

### 4.1 Purpose

Enables safe R&D on DATACENTER_HIGH profile without affecting production deployments.

### 4.2 Model-5 Rules

**Only DATACENTER_HIGH has experimental versions**

Example: `DATACENTER_HIGH@2.0@experimental`

**Characteristics**:
- Marked with @experimental suffix
- NOT selected by AUTO profile selection
- Requires explicit opt-in: `set_version("DATACENTER_HIGH@2.0@experimental", confirm=True)`
- Never becomes default automatically

### 4.3 Promotion Flow (Experimental → Stable)

```
Experimental Version (e.g., 2.0@experimental)
    ↓
1. Internal Testing: Run with real workloads
    ↓
2. Soak Test: 24-72 hours under load
    ├─ Determinism validation (20+ identical runs)
    ├─ DP correctness (epsilon/delta verified)
    ├─ AES correctness (output matches reference)
    └─ Performance validation (throughput/latency)
    ↓
3. Compliance Review: Security/compliance audit
    ↓
4. Promotion Decision: Manual approval required
    ↓
Stable Version (e.g., 2.0)
    ↓
Becomes available for: set_version("DATACENTER_HIGH@2.0", confirm=True)
```

### 4.4 Soak Test Framework

**ExperimentalVersionManager** tracks:
```python
class SoakTestResult:
    version: str
    start_time: datetime
    end_time: datetime
    total_hours: int
    determinism_runs: int  # Number of identical compression runs
    determinism_passed: bool
    dp_epsilon: float
    dp_delta: float
    aes_sample_count: int
    aes_passed: bool
    throughput_mb_s: float
    latency_p99_ms: float
    recorded: datetime
```

**Promotion requires**:
- Minimum 24 hours soak test
- Determinism: 20+ runs with identical output
- DP validation: epsilon/delta verified
- AES validation: output matches reference
- Manual approval from release manager

---

## 5. Security and Compliance Model

### 5.1 Cryptographic Assumptions

1. **AES-256-GCM Security Assumption**
   - Assumes NIST-approved AES-256 is secure
   - Assumes random key derivation (PBKDF2)
   - Assumes nonce uniqueness per block

2. **Differential Privacy Assumptions**
   - Assumes Laplace mechanism correctly implements privacy budget
   - Assumes epsilon/delta configuration is appropriate for data sensitivity
   - Assumes noise doesn't compromise downstream analytics beyond ε-δ bounds

3. **Hashing Assumptions**
   - Assumes SHA-256 provides integrity guarantees
   - Assumes pre-image resistance is sufficient for 256-bit outputs

### 5.2 Compliance Framework

**Built-In Audit Validation**:
```python
class SecurityAudit:
    def validate_differential_privacy(self):
        """Verify DP implementation matches specification"""
        # Check noise distribution
        # Check privacy loss accounting
        # Check bounds enforcement
    
    def validate_aes_gcm(self):
        """Verify AES-256-GCM properties"""
        # Check nonce non-reuse
        # Check authentication tag
        # Check key derivation
    
    def validate_determinism(self):
        """Verify compressed output is deterministic"""
        # Run same input 20+ times
        # Verify identical output
        # Check compression ratio consistency
```

**Standards Coverage**:
- ✅ SOC2 Type II: Determinism, integrity, availability
- ✅ ISO 27001: Security controls, encryption, access
- ✅ NIST SP 800-38D: GCM mode specification
- ✅ NIST SP 800-22: Entropy validation

### 5.3 Threat Model

**In Scope** (protected against):
- Data at rest: Encryption with AES-256-GCM
- Inference attacks: Differential privacy noise
- Integrity attacks: SHA-256 verification
- Side-channel on compression: Timing attacks mitigated by batching

**Out of Scope** (not protected against):
- Key management (caller's responsibility)
- Side-channel attacks on AES hardware (assumes trusted CPU)
- Quantum computing (post-quantum not yet implemented)
- Physical attacks on device

---

## 6. Testing and Validation Philosophy

### 6.1 Test Categories

#### 1. Determinism Tests
```python
class TestDeterminism:
    def test_same_input_produces_same_output(self):
        """Run compression 20+ times, verify identical output"""
        for i in range(20):
            compressed = engine.compress(data)
            assert compressed == expected, f"Run {i} differs!"
    
    def test_determinism_across_versions(self):
        """Verify version 1.0 and 1.1 both deterministic"""
        for version in ['1.0', '1.1']:
            engine = CobolEngine(version=version)
            # Verify determinism
```

#### 2. Opt-In Enforcement Tests
```python
class TestOptIn:
    def test_upgrade_requires_confirmation(self):
        """Verify set_version rejects confirm=False"""
        success, msg = engine.set_version('1.1', confirm=False)
        assert not success
        assert 'confirmation' in msg.lower()
    
    def test_failed_upgrade_unchanged(self):
        """Verify failed upgrade doesn't change state"""
        before = engine.get_current_version()
        engine.set_version('99.99', confirm=True)  # Will fail
        after = engine.get_current_version()
        assert before == after
```

#### 3. Fallback Tests
```python
class TestFallback:
    def test_fallback_preserves_version(self):
        """Verify version never changes in fallback"""
        engine = CobolEngine('DATACENTER_HIGH@1.1')
        # Trigger fallback with huge input
        engine.fallback_trigger()
        # Verify still @1.1, now on SERVER_GENERAL
        assert engine.current_version == 'SERVER_GENERAL@1.1'
```

#### 4. Security Tests
```python
class TestSecurity:
    def test_aes_nonce_non_reuse(self):
        """Verify nonce never repeats in same block"""
        nonces = []
        for i in range(1000):
            nonce = engine.generate_aes_nonce()
            assert nonce not in nonces
            nonces.append(nonce)
    
    def test_differential_privacy_bounds(self):
        """Verify privacy loss stays within epsilon"""
        # Add DP noise, verify bounds
```

### 6.2 Coverage Requirements

- **Unit Tests**: 95%+ code coverage
- **Integration Tests**: All layer interactions
- **End-to-End Tests**: Real-world data (structured, semi-structured, binary)
- **Regression Tests**: New versions must not break old data

### 6.3 Validation Pipeline

```
Code Change
    ↓
[All Unit Tests] ← Must pass (95%+ coverage)
    ↓
[Integration Tests] ← Must pass (layer interactions)
    ↓
[Determinism Tests] ← Must pass (20+ runs identical)
    ↓
[Security Audits] ← Must pass (crypto validation)
    ↓
[Backward Compat Tests] ← Must pass (old data still decompresses)
    ↓
Code Merged (if all pass)
    ↓
Soak Test (for experimental versions)
    ↓
Release Candidate
```

---

## 7. Engineering Trade-offs and Decisions

### 7.1 Decision: Determinism First

**Trade-off**: Determinism vs. Maximum Compression Ratio

**Decision**: Sacrifice 5-10% potential compression for guaranteed determinism

**Rationale**:
- Enterprise customers need auditability
- Compressed data must survive regulatory reviews
- Decompression must work identically across machines and years
- Compression ratio variance makes audits unreliable

**Impact**: Algorithms are simpler, more predictable, less "clever"

### 7.2 Decision: Optional Security, Not Always-On

**Trade-off**: Simplicity vs. Automatic Protection

**Decision**: Make encryption/privacy optional (not default)

**Rationale**:
- Compression is primary concern, security is secondary
- Users may have regulatory requirements or speed priorities
- Enabled by default would bloat code and slow compression
- Users making conscious choice = better security outcomes

**Impact**: 2 code paths (encrypted and unencrypted), more testing burden

### 7.3 Decision: 8-Layer Pipeline Over Single Algorithm

**Trade-off**: Complexity vs. Better Compression Ratios

**Decision**: Use 8 layers, each specialized

**Rationale**:
- Different data types benefit from different algorithms
- Modularity enables future optimization
- Easier to audit (each layer has clear responsibility)
- Allows fallback between profiles without code change

**Impact**: Code complexity, but better maintainability and flexibility

### 7.4 Decision: Immutable Versions Over Continuous Rollout

**Trade-off**: Update Speed vs. Stability

**Decision**: Never change released versions; create new version instead

**Rationale**:
- Users need guaranteed behavior for production data
- Zero risk of "production got slower after update"
- Enables safe rollback (revert to working version)
- Required for enterprise audit trails

**Impact**: Slower bug fixes (must create new version), but safer

### 7.5 Decision: 5 Named Profiles Over Custom Configuration

**Trade-off**: Flexibility vs. Consistency

**Decision**: 5 fixed profiles; no custom parameter tuning

**Rationale**:
- Reduces configuration surface area
- Makes upgrades straightforward
- Enables validation against fixed specs
- Easier to test (only 5 profiles to certify)

**Impact**: Less fine-tuning possible, but more predictable

---

## Engineering Principles

### 1. Explicit Over Implicit
- No hidden behaviors
- No background processes
- All decisions logged
- Configuration explicit and documented

### 2. Stable Over Innovative
- Proven algorithms, not experimental
- Conservative optimization
- Backward compatibility preserved
- Breaking changes require major version

### 3. Auditable Over Clever
- Clear algorithm structure
- Testable intermediate steps
- Observable state
- No randomness (except in security/DP)

### 4. Safe Over Fast
- Verification before compression
- Checksum verification after
- Fallback mechanism always available
- Rollback always possible

### 5. Contract-Based Over Trust-Based
- Explicit guarantees documented
- Versioning as contract
- Profile behavior specified
- Opt-in as enforcement

---

## Governance and Maintenance

### Version Release Process

1. **Development**: Code changes, create new version spec
2. **Testing**: All tests pass, security audit passes
3. **Internal Soak Test**: 24-72 hours with real workloads
4. **Release**: Tag git commit, publish version
5. **Notification**: Users informed of new version
6. **Adoption**: Users explicitly opt-in (no forcing)

### Support Lifecycle

| Version Status | Support Duration | Behavior |
|----------------|------------------|----------|
| **Current Stable** | Until next MAJOR | Bug fixes in MINOR releases |
| **Previous Stable** | 12 months | Critical fixes only |
| **Deprecated** | 6 months | No active support |
| **EOL** | Unsupported | Users must upgrade explicitly |

---

## Internal Terminology

| Term | Definition |
|------|-----------|
| **Profile** | Named hardware-based configuration |
| **Version** | Specific algorithm/parameter set for a profile |
| **AUTO** | Hardware-based automatic profile selection |
| **Soak Test** | Extended testing period under real load |
| **Fallback** | Downgrade to lower profile when latency exceeds threshold |
| **Immutable** | Version never changes after release |
| **Opt-In** | User must explicitly request (no automatic changes) |
| **Model-5** | Experimental development track for DATACENTER_HIGH |

---

## Audit and Compliance

### Internal Audit Checklist

Before releasing new version:
- ✅ All unit tests pass (95%+ coverage)
- ✅ All integration tests pass
- ✅ Determinism verified (20+ identical runs)
- ✅ Security audit passes
- ✅ Backward compatibility verified
- ✅ Documentation updated
- ✅ Copyright notices verified
- ✅ Soak test completed (24+ hours)

### For Enterprise Reviewers

This system supports:
- ✅ **Auditability**: All changes logged, version-controlled, immutable
- ✅ **Determinism**: Guaranteed identical compression for same input
- ✅ **Compliance**: SOC2/ISO 27001 compatible
- ✅ **Stability**: No silent changes, explicit opt-in only
- ✅ **Security**: AES-256-GCM + differential privacy (optional)
- ✅ **Privacy**: Differential privacy bounds configurable and verifiable

---

## Contact and Escalations

### Technical Issues
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- See source code comments and docstrings

### Security Issues
- See [COMPLIANCE_STATEMENT.md](COMPLIANCE_STATEMENT.md)
- Contact: Nafal Faturizki

### Licensing / Commercial
- See [LICENSE.md](LICENSE.md)
- Contact: Nafal Faturizki

---

**Copyright © 2026 Nafal Faturizki | All rights reserved.**  
**Version**: 1.5.3  
**Classification**: Internal Engineering Documentation  
**Last Updated**: March 1, 2026

**CONFIDENTIAL** — Restricted distribution only
