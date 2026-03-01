# Profile Versioning System

**COBOL v1.5.3 Compression Engine**  
**Status**: Production Ready  
**Version**: 1.0  
**Date**: March 1, 2026  

---

## Executive Summary

The **Profile Versioning System** provides enterprise-grade version management for performance profiles with:

✅ **Immutable Versions** - Once released, versions never change  
✅ **Explicit Opt-In Upgrades** - No automatic version changes  
✅ **Deterministic Behavior** - Same hardware = same profile = same version  
✅ **Complete Auditability** - All changes logged for compliance  
✅ **Backward Compatibility** - All versions maintain file format, decompression, crypto  
✅ **Safe Fallback** - Profile downgrades, but versions never change  

---

## Core Principle

```
No performance profile or profile version 
will ever change automatically.
```

This guarantee enables:
- Enterprise adoption without fear of silent behavior changes
- Regulatory compliance and auditability
- Deterministic compression across deployments
- Safe experimentation with opt-in upgrades

---

## Profiles and Versions

### Understanding the Model

```
A "Profile" is a stable identity:              DATACENTER_HIGH
A "Version" is an implementation of that:      DATACENTER_HIGH@1.0
                                               DATACENTER_HIGH@1.1
                                               DATACENTER_HIGH@2.0@experimental
```

**Key Rules**:
- Profile name NEVER changes
- Version number increases with improvements
- Version behavior is IMMUTABLE
- Upgrades require EXPLICIT USER ACTION

### The 5 Static Profiles

Each has ONE DEFAULT version, plus optional upgrades:

| Profile | Default Version | Available Upgrades | Min Hardware |
|---------|-----------------|-------------------|-------------|
| EDGE_LOW | 1.1 | (none yet) | 1 core, <2GB |
| CLIENT_STANDARD | 1.1 | (none yet) | 2 cores, 4GB |
| WORKSTATION_PRO | 1.0 | (none yet) | 8 cores, 32GB |
| SERVER_GENERAL | 1.0 | (none yet) | 16 cores, 64GB |
| DATACENTER_HIGH | 1.0 | 2.0@experimental | 64 cores, 256GB |

**Important**: Different versions of same profile may have different performance characteristics but identical behavior guarantees.

---

## Profile Version Lifecycle

### Stages of a Version

```
┌─────────────────────────────────────────────────────────────┐
│                   VERSION LIFECYCLE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROPOSAL                                                   │
│  ↓                                                           │
│  Internal design review                                     │
│                                                             │
│  ↓                                                           │
│  EXPERIMENTAL (marked @experimental)                        │
│  - Requires explicit opt-in                                 │
│  - Visible to opt-in users only                             │
│  - Monitored for issues                                     │
│  - 24-72 hour soak test required                            │
│                                                             │
│  ↓                                                           │
│  PROMOTION DECISION                                         │
│  - All soak tests must pass                                 │
│  - Determinism verified (20+ runs)                          │
│  - DP correctness validated                                 │
│  - AES correctness validated                                │
│  - Manual human approval required                           │
│                                                             │
│  ↓                                                           │
│  RELEASED STABLE VERSION                                    │
│  - New version number (e.g., 1.0 → 2.0)                    │
│  - Users notified of upgrade availability                  │
│  - Automatic upgrades: NO                                   │
│  - Users must explicitly opt-in                             │
│  - Fully reversible to previous version                     │
│                                                             │
│  ↓                                                           │
│  STABLE (indefinite)                                        │
│  - Immutable forever                                        │
│  - Can be used alongside newer versions                     │
│  - Always supported for decompression                       │
│                                                             │
│  ↓ (Eventually)                                              │
│  DEPRECATED (announcement + 2 year support)                │
│  - Marked for phase-out                                     │
│  - Users encouraged to upgrade                              │
│  - Still fully functional                                   │
│                                                             │
│  ↓                                                           │
│  END-OF-LIFE (after 2-year deprecation)                     │
│  - No longer supported/updated                              │
│  - Can still decompress files                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Auto-Selection vs. Manual Version Selection

### AUTO Selection (Hardware-Based)

```python
# AUTO selection - deterministic hardware detection
profile, default_version = profile_manager.auto_select_profile()

# Result examples:
#   profile = "DATACENTER_HIGH"
#   default_version = "1.0"   # NOT "@2.0@experimental"
```

**What AUTO does**:
- Automatically detect hardware characteristics
- Select optimal profile NAME based on cores/RAM
- Return DEFAULT stable version for that profile
- Same hardware = same profile + same version

**What AUTO does NOT do**:
- Automatically upgrade existing versions
- Select experimental versions
- Change user's existing version without action

---

### Manual Version Selection (User-Controlled)

```python
# User explicitly chooses different version
success, msg = upgrade_manager.set_version(
    'CLIENT_STANDARD@1.1',
    confirm=True  # Explicit confirmation required
)

# Other options:
upgrade_manager.set_version('DATACENTER_HIGH@2.0@experimental', confirm=True)
upgrade_manager.rollback_to_previous()
```

**User controls**:
- When to upgrade (not automatic)
- Which version to use (not prescribed)
- Can downgrade to previous stable
- All upgrades logged for audit

---

## Version Upgrade Workflow

### Step 1: Check Availability

```python
# What versions are available?
available = version_manager.get_all_versions('CLIENT_STANDARD')
# Returns: ['1.0', '1.1']

# What's stable vs experimental?
stable = version_manager.get_stable_versions('CLIENT_STANDARD')
experimental = version_manager.get_experimental_versions('DATACENTER_HIGH')
```

### Step 2: Get Upgrade Information

```python
# Before upgrading, understand what changes
info = upgrade_manager.propose_upgrade('CLIENT_STANDARD@1.1')

print(info.summary())
# Output:
# Upgrade: CLIENT_STANDARD@1.0 → CLIENT_STANDARD@1.1
#
# Changes:
#   - Improved thread pool scheduling
#   - Better performance on hyperthreaded systems
#   - Reduced P95 latency by ~8%
#
# What DID NOT change:
#   - File format
#   - Decompression
#   - AES-256-GCM behavior
#   - DP guarantees
```

### Step 3: Explicit Upgrade (With Confirmation)

```python
# Upgrade REQUIRES explicit confirmation
success, msg = upgrade_manager.set_version(
    'CLIENT_STANDARD@1.1',
    confirm=True  # <-- Must be True
)

if success:
    print(f"Upgraded to {upgrade_manager.get_current_version()}")
else:
    print(f"Upgrade failed: {msg}")
```

### Step 4: Rollback (If Needed)

```python
# Always reversible - downgrade to previous version
success, msg = upgrade_manager.rollback_to_previous()

if success:
    print(f"Rolled back to {upgrade_manager.get_current_version()}")
```

---

## Version Immutability Guarantee

### What This Means

Once a profile version is released, **its behavior NEVER changes**.

```
CLIENT_STANDARD@1.0 → Always behaves identically
CLIENT_STANDARD@1.0 → Same input + same  parameters = same output
CLIENT_STANDARD@1.0 → Determinism held across 20+ identical runs
CLIENT_STANDARD@1.0 → Immutable forever (not retroactively changed)
```

### Why It Matters

- **Predictability**: Version is a stable reference point
- **Compliance**: Audits can reference specific versions
- **Performance**: Can optimize specific versions for specific workloads
- **Safety**: No surprise behavior changes

### How It's Enforced

1. Version parameters are LOCKED in spec file
2. Parameter changes = new version number
3. Tests verify parameter immutability
4. Versions hashed to detect tampering

---

## What DOES Change Between Versions?

Profile versions enable improvements in:

✓ **Performance** - Throughput, latency, memory usage  
✓ **Stability** - Better handling of edge cases  
✓ **Compatibility** - Better handling of specific hardware  
✓ **Default settings** - DP epsilon can increase (better privacy-utility tradeoff)  

All changes are:
- **Documented** - Release notes explain each change
- **Logged** - Audit trail shows when applied
- **Reversible** - Can downgrade to previous version
- **Additive** - Never break existing behavior

---

## What DOES NOT Change Between Versions?

Versions are NEVER allowed to change:

✗ **File Format** - Files compressed with any version are identical
✗ **Decompression** - Decompressor works with any profile version
✗ **AES-256-GCM** - Cryptographic algorithm is immutable
✗ **DP Guarantees** - Privacy bound bounds are maintained  
✗ **Output Determinism** - Same input = same output always

This is GUARANTEED across all versions of all profiles.

---

## Experimental Versions (Model-5 Track)

Only DATACENTER_HIGH supports experimental versions for R&D:

###  Safety Rules

```
EXPERIMENTAL versions MUST:
- Be clearly marked with @experimental suffix
- Require explicit opt-in (no accidental selection)
- Complete 24-72 hour soak test before promotion
- Pass determinism validation (20+ identical runs)
- Pass DP correctness validation
- Pass AES correctness validation
- Receive manual human approval
- Never become default automatically
- Be fully reversible
```

### Experimental Version Promotion Flow

```
Step 1: EXPERIMENTAL released (DATACENTER_HIGH@2.0@experimental)
        → Users can opt-in for testing
        → Not default for anyone

Step 2: Soak testing (24-72 hours under load)
        → Run 20+ consecutive identical inputs
        → Verify determinism
        → Validate DP epsilon/delta guarantees
        → Validate AES output matches reference

Step 3: Promotion decision
        → Review all test results
        → Manual human approval required
        → NO automatic promotion

Step 4: Released as stable (DATACENTER_HIGH@2.0)
        → Remove @experimental suffix
        → Increment version number
        → Users can upgrade (explicit opt-in)
        → Experimental version deprecated

Step 5: Full support
        → Treated as stable version
        → Available alongside previous versions
        → No automatic upgrades
        → Always reversible
```

---

## Fallback (Safety Mechanism)

Fallback downgrades the PROFILE only, never the VERSION.

```
DATACENTER_HIGH@2.0@experimental experiencing latency spike
↓
Fallback activated
↓
Result: SERVER_GENERAL@1.0 (profile downgraded, version matched down)
```

**Rules**:
- ONE level downgrade only (no cascading)
- Version in same direction as profile
- CLIENT_STANDARD@1.1 is absolute minimum (never falls below)
- All fallbacks logged with reason and timestamp

---

## Examples

### Example 1: Stable Upgrade

```python
# User is on CLIENT_STANDARD@1.0
# wants to try CLIENT_STANDARD@1.1
# which provides better threading performance

upgrade_manager.current_version = 'CLIENT_STANDARD@1.0'

# 1. Check what's available
info = upgrade_manager.propose_upgrade('CLIENT_STANDARD@1.1')
print(f"Improvements: {info.performance_improvements}")
#   Output: ['Improved thread pool scheduling', 'Better performance on hyperthreaded systems']

print(f"Not changing: {info.what_did_not_change}")
#   Output: ['File format', 'Decompression', 'AES-256-GCM behavior', 'DP guarantees']

# 2. Explicit upgrade with confirmation
success, msg = upgrade_manager.set_version('CLIENT_STANDARD@1.1', confirm=True)

# 3. Verify
print(f"Current: {upgrade_manager.get_current_version()}")
#   Output: CLIENT_STANDARD@1.1

# 4. Check audit trail
for entry in upgrade_manager.version_manager.get_audit_log():
    print(entry.log_entry())
#   Output: [2026-03-01T12:34:56.123456] SUCCESS: CLIENT_STANDARD@1.0 → CLIENT_STANDARD@1.1 (user_request)
```

### Example 2: Experimental Opt-In

```python
# Advanced user wants to test experimental DATACENTER_HIGH@2.0@experimental

# 1. Get experimental versions
exp_versions = version_manager.get_experimental_versions('DATACENTER_HIGH')
print(exp_versions)
#   Output: ['2.0@experimental']

# 2. Get upgrade information (what's experimental about it?)
info = upgrade_manager.propose_upgrade('DATACENTER_HIGH@2.0@experimental')
print(f"Experimental features: {info.changes}")
#   Output: ['NUMA-aware work stealing', 'Dynamic batch sizing', ...]

# 3. Review soak test requirements
pv = version_manager.get_version('DATACENTER_HIGH', '2.0@experimental')
print(f"Minimum soak hours: {pv.min_soak_hours_required}")
#   Output: 24

# 4. Explicit opt-in  (must be very intentional)
success, msg = upgrade_manager.set_version(
    'DATACENTER_HIGH@2.0@experimental',
    confirm=True
)

# 5. Provide feedback
experimental_manager.log_soak_test_result('2.0@experimental', 'Test 1: PASS')
experimental_manager.log_soak_test_result('2.0@experimental', 'Determinism: VERIFIED (20 runs)')
```

### Example 3: Forced Rollback

```python
# Something goes wrong with new version, user rolls back

# 1. Fall back immediately
success, msg = upgrade_manager.rollback_to_previous()
print(msg)
#   Output: Successfully rolled back to CLIENT_STANDARD@1.0

# This is automatically logged
# Audit trail shows:
# [2026-03-01T12:36:00] SUCCESS: CLIENT_STANDARD@1.1 → CLIENT_STANDARD@1.0 (user_request)
```

---

## Testing & Validation

### Developer Testing

```bash
# Run versioning tests
pytest test_profile_versioning.py -v

# Key tests:
#   - test_version_immutability (versions don't change)
#   - test_opt_in_enforcement (no automatic upgrades)
#   - test_auto_selection_determinism (same hardware = same version)
#   - test_experimental_isolation (explicit opt-in required)
#   - test_safe_fallback (version never changes in fallback)
#   - test_audit_logging (all changes logged)
```

### Operator Validation

```python
# Verify current state
print(upgrade_manager.get_current_version())  # e.g., "CLIENT_STANDARD@1.1"

# Check available upgrades
available = version_manager.get_all_versions('CLIENT_STANDARD')
print(f"Available versions: {available}")

# Review upgrade history
print(version_manager.print_audit_log())
```

---

## Production Deployment Checklist

- [ ] All profile versions validated in spec
- [ ] All versions pass immutability tests
- [ ] Explicit upgrade policy documented
- [ ] Audit logging configured
- [ ] Rollback procedures tested
- [ ] Cross-language consistency verified
- [ ] Monitoring configured for audit trail
- [ ] User communication prepared
- [ ] Support team trained
- [ ] Approval signatures collected

---

## Guarantees

### Safety Guarantee #1: Immutability

✅ Once released, profile versions NEVER change  
✅ Parameter changes = new version number  
✅ Hash verification prevents tampering  

### Safety Guarantee #2: Auditability

✅ All version selections logged  
✅ All version upgrades logged  
✅ All fallbacks logged  
✅ Timestamp and reason recorded  

### Safety Guarantee #3: Backward Compatibility

✅ File format identical across all versions  
✅ Decompression works with any profile version  
✅ AES-256-GCM identical across versions  
✅ DP guarantees maintained  

### Safety Guarantee #4: User Control

✅ No silent behavior changes  
✅ Explicit opt-in required for upgrades  
✅ All upgrades reversible  
✅ User always knows current version  

---

## Troubleshooting

### Q: How do I check my current version?
```python
print(upgrade_manager.get_current_version())
```

### Q: Can I skip a version? (e.g., 1.0 → 2.0 directly)
```python
# Yes, all upgrades are allowed, you control the target
success, msg = upgrade_manager.set_version('CLIENT_STANDARD@2.0', confirm=True)
```

### Q: What if I don't like the new version?
```python
# Rollback is always available and automatic
success, msg = upgrade_manager.rollback_to_previous()
```

### Q: Are experimental versions safe?
```text
Experimental versions:
- Require explicit opt-in
- Are fully reversible
- Pass 24-72 hour soak tests before release
- Are marked clearly
- Can be toggled off anytime
```

### Q: How do I know if a version is experimental?
```python
pv = version_manager.get_version('DATACENTER_HIGH', '2.0@experimental')
print(pv.is_experimental())  # True
print(pv.requires_explicit_opt_in)  # True
```

### Q: Can versions be forced on me?
```text
No. System NEVER automatically upgrades versions.
All upgrades require explicit set_version(..., confirm=True) call.
```

---

## References

- **[UPGRADE_POLICY.md](UPGRADE_POLICY.md)** - Corporate policy on upgrades
- **[MODEL_LIFECYCLE.md](MODEL_LIFECYCLE.md)** - Experimental version lifecycle
- **[spec/performance_profiles_v2.yaml](../spec/performance_profiles_v2.yaml)** - Version spec
- **[profile_versioning.py](../profile_versioning.py)** - Implementation
- **[test_profile_versioning.py](../test_profile_versioning.py)** - Tests

---

**Version**: 1.0  
**Status**: Production Ready  
**Last Updated**: March 1, 2026  
