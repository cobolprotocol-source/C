# 🗺️ PHASE 1 REFACTORING ROADMAP - DETAILED EXECUTION PLAN

**Document Status:** Final Execution Specification  
**Date Created:** March 4, 2026  
**Phase:** 1 / 4  
**Overall Completion:** 40% (after shadow removal + cleanup)

---

## 📌 EXECUTIVE SUMMARY

This document defines the complete refactoring roadmap for consolidating the COBOL Protocol repository architecture. It builds on the completed Phase 1 Part 1 (shadow removal) and details Phase 1 Part 2-4 with explicit task breakdowns, dependencies, and risk assessment.

### Current State (After Phase 1 Part 1):
```
Root-level files: 62 (down from 81)
Canonical layers: 54 files (source of truth)
Archived safely: 19 files (recoverable)

Remaining work: 48 files to consolidate + 3 critical workstreams
```

---

## 🎯 STRATEGIC GOALS

### Goal 1: Single Source of Truth
- ✅ Canonical layer structure in `/src/layers/` only
- ✅ No duplicate implementations anywhere
- Target: 100% of compression logic in canonical location

### Goal 2: Clear Entry Points
- ✅ `/src/api.py` as single authoritative API
- ✅ Deprecate all competing entry points gracefully
- Target: Users have ONE clear path to compression

### Goal 3: Federated Learning Security
- ✅ Add encryption wrapper for pattern transmission
- ✅ Implement TTL enforcement on shared patterns
- ✅ Local-only fallback on federation failure
- Target: Zero pattern information leakage

### Goal 4: Adaptive Execution Foundation
- ✅ Pre-pipeline entropy gating (wrap, don't modify L1-L8)
- ✅ Optional layer skipping for low-gain operations
- ✅ Revert-on-no-gain logic for each layer
- Target: ~30% reduction in wasted CPU cycles

---

## 📋 WORKSTREAM BREAKDOWN

### WORKSTREAM A: PHASE 1 PART 1 (COMPLETED ✅)

**Status:** DONE

```
Task A1: Shadow Implementation Removal ✅
├─ Identified: 9 duplicate layer files at root level
├─ Action: Archive to .archive/shadow_implementations_backup/
└─ Result: Removed 9 files, 0 breaking changes

Task A2: Broken Import Fixes ✅
├─ Identified: 5 files with invalid imports
├─ Action: Updated to canonical paths
├─ Files Fixed:
│  ├─ src/auto_tuner.py
│  ├─ src/create_quick_ref.py
│  ├─ src/layers/variants/l8_final.py
│  ├─ tools/audit_performance_metrics.py
│  └─ (+ 1 more)
└─ Result: All imports verified working

Task A3: Deprecated File Cleanup ✅
├─ Identified: 10 files (6 deprecated + 4 tests)
├─ Action: Archive to .archive/deprecated_deletable/ and .archive/test_artifacts/
└─ Result: 81 → 62 root-level files
```

**Deliverables from A:**
- REPOSITORY_AUDIT_REPORT.md (comprehensive analysis)
- IMPLEMENTATION_ROADMAP_PHASE1.md (execution plan)
- PHASE1_CHECKPOINT.md (progress marker)

---

### WORKSTREAM B: FILE CONSOLIDATION (PHASE 1 PART 2)

**Status:** PENDING (48 files to move)  
**Duration Estimate:** 1-2 hours  
**Complexity:** LOW (mostly mv + import fix)

#### B1: Move Pipeline Orchestrators (7 files)

**Target:** `/src/layers/pipelines/`

```
Files to Move:
├─ src/adaptive_pipeline.py
├─ src/dag_pipeline.py
├─ src/engine.py (at root, conflict with canonical)
├─ src/full_pipeline.py
├─ src/fusion_pipeline_optimizer.py
├─ src/l5l8_optimized_pipeline.py
└─ src/dag_compression_pipeline.py

Action:
1. Move each file to /src/layers/pipelines/
2. Create __init__.py imports if needed
3. Fix any cross-imports
4. Update documentation

Risk: MEDIUM
├─ engine.py exists in both locations (need merge/consolidate)
└─ Potential circular imports if not careful

Validation:
├─ Run compression tests after each move
├─ Verify imports resolve
└─ Check no duplicate __all__ exports
```

#### B2: Move GPU/Hardware Accelerators (6 files)

**Target:** `/src/layers/advanced/gpu/` (new directory)

```
Files to Move:
├─ src/fpga_controller.py
├─ src/gpu_acceleration.py
├─ src/gpu_accelerator.py
├─ src/huffman_gpu.py
├─ src/huffman_parallel.py
└─ src/trie_gpu.py

Action:
1. Create /src/layers/advanced/gpu/ directory
2. Move GPU-specific modules there
3. Create gpu/__init__.py with exports
4. Update src/layers/advanced/__init__.py

Risk: LOW
└─ No cross-dependencies detected

Validation:
├─ GPU tests still pass (if present)
├─ Hardware detection still works
└─ Fallback to CPU works correctly
```

#### B3: Move Dictionary Modules (5 files)

**Target:** `/src/layers/dictionaries/`

```
Files to Move:
├─ src/dictionary_manager.py
├─ src/federated_dictionary_learning.py
├─ src/nested_dictionary.py
├─ src/numba_dictionary.py
└─ src/super_dictionary_system.py

Action:
1. Move to /src/layers/dictionaries/
2. Consolidate __init__.py exports
3. Fix cross-module imports
4. Update federated_dictionary_learning to use canonical paths

Risk: MEDIUM-HIGH
├─ federated_dictionary_learning is CRITICAL (security implications)
└─ Import cycles possible if not careful

Validation:
├─ Dictionary tests pass
├─ Federated learning still works
├─ No encryption/privacy changes
└─ Backward compatibility maintained
```

#### B4: Move Distributed/Federation (5 files)

**Target:** `/src/layers/distributed/` (new directory)

```
Files to Move:
├─ src/cluster_orchestrator.py
├─ src/distributed_framework.py
├─ src/federated_learning_framework.py
├─ src/load_balancer_primary.py
└─ src/load_balancer_replica.py

Action:
1. Create /src/layers/distributed/ directory
2. Move federation/clustering modules
3. Create distributed/__init__.py
4. Update src/layers/__init__.py

Risk: MEDIUM
├─ Complex interdependencies
├─ Need to preserve failover logic
└─ Test extensively before production

Validation:
├─ Federated learning tests pass
├─ Load balancing still works
├─ Cluster orchestration functional
└─ No data loss scenarios
```

#### B5: Move Monitoring/Metrics (5 files)

**Target:** `/src/layers/metrics/` OR keep in root (decision needed)

```
Files to Consider:
├─ src/metrics.py
├─ src/metrics_prometheus.py
├─ src/profiler.py
├─ src/profile_cpu.py
└─ src/profile_memory.py

Decision Point:
┌─ Option 1: Move to /src/layers/metrics/
│  ├─ Pro: Keep everything in /src/layers/
│  └─ Con: Metrics are observability, not core logic
|
└─ Option 2: Keep in /src (observability plane)
   ├─ Pro: Separate concerns (metrics ≠ compression)
   └─ Con: Root level still has files

Recommendation: OPTION 2 (keep in root)
Reason: Metrics are post-pipeline observability, not core pipeline

Action:
1. Leave metrics at root (they're observability)
2. Create src/observability/ link if needed
3. Document that metrics are optional
```

#### B6: Consolidate Utilities (6 files)

**Target:** `/src/utilities/` (new directory, OR review individually)

```
Files to Review:
├─ src/validator.py → Could go to /src/layers/core/
├─ src/streaming.py → Could go to /src/layers/advanced/
├─ src/vector_*.py → Could go to /src/layers/advanced/
├─ src/embedding_providers.py → /src/layers/advanced/
└─ src/backward_compatibility_check.py → Keep in root

Action:
1. Review each utility on case-by-case basis
2. Validator → /src/layers/core/validator.py
3. Streaming → /src/layers/advanced/streaming.py
4. Embeddings → /src/layers/advanced/embeddings/
5. Backward compat tools → /src/tools/

Risk: LOW (small files, few dependencies)
```

#### B7: Handle "Unknown" Category (20 files)

**Status:** Needs deeper analysis

```
20 Files Requiring Review:
├─ adaptive_chunk_optimizer.py
├─ advanced_selective_retrieval.py
├─ cobol_v16_integrated.py
├─ dp_optimizer.py
├─ generate_*.py (multiple)
├─ hardware_abstraction_layer.py
├─ hardware_optimized_layers.py
├─ heterogeneous_orchestrator.py
├─ ... (12 more)

Action Plan:
1. Run grep analysis on each file
2. Categorize by functionality
3. Determine if:
   a) Dead code → Archive
   b) Optimization → /src/layers/advanced/
   c) Utility → /src/tools/
   d) Testing → /tests/

Example Decision Tree:
if "optimizer" in filename:
    → /src/layers/advanced/optimizers/
elif "generate" in filename:
    → /src/tools/generators/
elif imports from tests:
    → /tests/
else:
    → Review file manually

Estimated time: 30 minutes for full categorization
```

---

### WORKSTREAM C: SINGLE ENTRY POINT API (PHASE 1 PART 3)

**Status:** PENDING  
**Duration Estimate:** 30 minutes  
**Complexity:** LOW (wrapper pattern)

#### C1: Create `/src/api.py`

```python
"""
Canonical COBOL Protocol Compression API
Single entry point for all compression operations
"""

async def compress(
    data: bytes,
    strategy: str = 'adaptive',  # 'adaptive', 'fast', 'balanced'
    enable_federation: bool = False,
    timeout_ms: int = 5000,
    **kwargs
) -> CompressionResult:
    """
    Compress data using COBOL Protocol L0-L8 pipeline.
    
    This is the ONLY authorized entry point for compression.
    All other entry points deprecated effective v1.5.
    """
    # Pre-pipeline: Strategy selection (wrapper pattern, doesn't modify L1-L8)
    strategy_config = _select_strategy(strategy)
    
    # Core: Legacy pipeline (L1-L8 unchanged)
    from src.layers.pipelines.engine import CobolPipeline
    pipeline = CobolPipeline()
    result = pipeline.compress(data)
    
    # Post-pipeline: Optional federation
    if enable_federation and result.compression_ratio < 0.5:
        result = await _federated_enhance(result)
    
    return result
```

#### C2: Deprecation Warnings

Add to competing entry points:

```python
# In src/engine.py, src/adaptive_pipeline.py, etc.
def compress(data: bytes):
    warnings.warn(
        "This entry point is DEPRECATED as of v1.5. "
        "Use src.api.compress() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Still works, but warns
    return legacy_compress(data)
```

#### C3: Update Documentation

- Update README.md quickstart
- Create MIGRATION_GUIDE.md for users
- Update API docs
- Update examples/tutorials

---

### WORKSTREAM D: FEDERATED LEARNING SECURITY (PHASE 1 PART 4)

**Status:** PENDING  
**Duration Estimate:** 45 minutes - 1 hour  
**Complexity:** MEDIUM-HIGH (security-critical)  
**Constraint:** MUST NOT modify L1-L8 pipeline logic

#### D1: Post-Pipeline Encryption Wrapper

```python
# In src/layers/dictionaries/federated_dictionary_learning.py
# ADD THIS (don't modify existing compress logic)

class FederatedPatternGuard:
    """
    Post-pipeline security wrapper for pattern sharing.
    Runs AFTER L8 compression completes.
    """
    
    def __init__(self, encryption_key: bytes = None):
        self.cipher = AES256GCM(encryption_key)
        self.pattern_ttl = 86400  # 24 hours
    
    def encrypt_pattern(self, pattern: bytes) -> EncryptedPattern:
        """Encrypt sensitive patterns before transmission."""
        nonce = os.urandom(12)
        ciphertext = self.cipher.encrypt(nonce, pattern)
        return EncryptedPattern(
            ciphertext=ciphertext,
            nonce=nonce,
            created_at=time.time(),
            ttl_seconds=self.pattern_ttl,
            checksum=hashlib.sha256(pattern).digest()
        )
    
    def validate_ttl(self, pattern: EncryptedPattern) -> bool:
        """Check if pattern has expired."""
        age = time.time() - pattern.created_at
        return age < pattern.ttl_seconds
    
    def local_only_fallback(self):
        """If federation fails, use only local patterns."""
        logger.warning("Federation unavailable. Using local patterns only.")
        return True
```

#### D2: Privacy Bounds Validation

```python
class PrivacyGuard:
    """
    Validate ε-δ privacy bounds before pattern sharing.
    Runs POST-pipeline only.
    """
    
    def __init__(self, epsilon: float = 1.0, delta: float = 0.01):
        self.epsilon = epsilon
        self.delta = delta
    
    def validate_bounds(self, pattern_stats: dict) -> bool:
        """
        Check if patterns meet differential privacy bounds.
        
        ε (epsilon): Budget for information leakage
        δ (delta): Probability of privacy failure
        """
        entropy_loss = pattern_stats.get('entropy_leakage', 0)
        unique_patterns = pattern_stats.get('unique_patterns', 0)
        
        # Simplified check (real implementation more complex)
        if entropy_loss > self.epsilon:
            return False
        
        if 1.0 / unique_patterns < self.delta:
            return False
        
        return True
```

#### D3: Local-Only Fallback

```python
class FederatedLearnerSafe(FederatedLearner):
    """
    Enhanced federated learner with local-only fallback.
    
    Key safety property:
    - If federation fails → automatically use local patterns
    - No data loss
    - Graceful degradation
    """
    
    async def share_pattern(self, pattern: bytes) -> bool:
        """Share pattern with federation, fallback to local if fails."""
        try:
            # Phase 1: Encrypt
            guard = FederatedPatternGuard()
            encrypted = guard.encrypt_pattern(pattern)
            
            # Phase 2: Validate privacy
            privacy = PrivacyGuard()
            if not privacy.validate_bounds({"entropy_leakage": 0.5}):
                logger.warning("Privacy bounds violated. Keeping local only.")
                return False
            
            # Phase 3: Transmit
            await self.federation_client.send_pattern(encrypted)
            return True
            
        except FederationConnectionError:
            logger.warning("Federation unavailable. Using local patterns.")
            return False  # Graceful fallback
        
        except Exception as e:
            logger.error(f"Federation error: {e}. Local fallback active.")
            return False
```

---

### WORKSTREAM E: ADAPTIVE EXECUTION FOUNDATION (PHASE 1 PART 5)

**Status:** PENDING  
**Duration Estimate:** 1 hour  
**Complexity:** MEDIUM (wrapper pattern, NOT modifying L1-L8)  
**Constraint:** Create PRE-PIPELINE control logic, don't touch L1-L8

#### E1: Pre-Pipeline Entropy Analysis

```python
class AdaptiveExecutor:
    """
    PRE-PIPELINE layer that decides execution mode.
    Does NOT modify L1-L8, only decides whether to invoke it.
    """
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.entropy_threshold = 0.95
    
    def analyze_input(self, data: bytes) -> InputAnalysis:
        """Analyze input BEFORE sending to L1-L8."""
        entropy = self._calculate_entropy(data)
        size = len(data)
        
        return InputAnalysis(
            entropy=entropy,
            size_bytes=size,
            data_type=self._detect_type(data),
            compressibility_score=self._estimate_gain(entropy),
            recommended_mode=self._select_mode(entropy, size)
        )
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy."""
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1
        
        entropy = 0
        for count in freq.values():
            p = count / len(data)
            entropy -= p * math.log2(p)
        
        return entropy / 8.0  # Normalized to [0, 1]
    
    def _estimate_gain(self, entropy: float) -> float:
        """Estimate compression gain potential."""
        # Low entropy (ordered data) → high gain
        # High entropy (random) → low gain
        return 1.0 - entropy
```

#### E2: Conditional Execution (PRE-PIPELINE)

```python
class AdaptiveExecutionControl:
    """
    Decision tree BEFORE L1-L8 executes.
    This wrapper pattern preserves L1-L8 immutability.
    """
    
    def compress_adaptive(self, data: bytes) -> CompressionResult:
        """
        Smart compression:
        - High entropy → return uncompressed
        - Low entropy → run L1-L8
        - Medium → run L1-L8 with monitoring
        """
        analysis = self.executor.analyze_input(data)
        
        # PRE-PIPELINE DECISION (no modification to L1-L8)
        if analysis.entropy > self.executor.entropy_threshold:
            logger.info(f"Entropy {analysis.entropy:.2f} too high. Skipping compression.")
            return CompressionResult(
                compressed_data=data,  # Unchanged
                ratio=1.0,
                skipped=True,
                reason="High entropy",
                checksum=hashlib.sha256(data).digest()
            )
        
        # CORE: Invoke legacy pipeline (L1-L8 unchanged)
        result = self.pipeline.compress(data)
        
        # POST-PIPELINE: Optional optimization
        if result.ratio > 0.95:  # <5% improvement
            logger.info("Compression gain < 5%. Returning original.")
            return CompressionResult(
                compressed_data=data,
                ratio=1.0,
                skipped_postpipeline=True,
                reason="No gain",
                original_result=result  # Keep for audit
            )
        
        return result
```

#### E3: Layer-Specific Revert Logic (POST-PIPELINE analysis only)

```python
class LayerEffectivenessAnalyzer:
    """
    Analyzes which layers actually helped compression (POST-pipeline).
    Used for reporting only, does NOT modify layer execution.
    """
    
    def evaluate_layer_gains(self, per_layer_stats: list) -> dict:
        """
        Calculate each layer's contribution.
        This is ANALYSIS only, not control.
        """
        gains = {}
        prev_size = per_layer_stats[0]['size']
        
        for layer_stat in per_layer_stats[1:]:
            curr_size = layer_stat['size']
            layer_name = layer_stat['name']
            
            gain_pct = (prev_size - curr_size) / prev_size * 100
            gains[layer_name] = {
                'bytes_saved': prev_size - curr_size,
                'percent_gain': gain_pct,
                'was_helpful': gain_pct > 1.0  # >1% threshold
            }
            
            prev_size = curr_size
        
        return gains
```

---

## 🔗 DEPENDENCY GRAPH

```
Phase 1 Part 1: Shadow Removal ✅
    ↓
    ├─→ Phase 1 Part 2: File Consolidation
    │   ├─→ Phase 1 Part 3: Single Entry Point API
    │   │   └─→ Phase 1 Part 4: Fed Learning Security
    │   └─→ Phase 1 Part 5: Adaptive Execution (parallel to 4)
    │
    ├─→ Validation/Testing (runs after each part)
    └─→ Documentation Updates (continuous)
```

**Critical Path:**
```
Part 1 ✅ → Part 2 (1-2h) → Part 3 (30min) → Part 4 (45min) → COMPLETE
```

**Parallel Path:**
```
Part 1 ✅ → [Part 2 & Part 5 can overlap]
```

---

## ⚠️ RISK ASSESSMENT

| Workstream | Risk Level | Mitigation | Rollback Plan |
|-----------|-----------|-----------|---------------|
| **B: File Move** | LOW | Test after each move | `git reset` per file |
| **C: API Entry** | LOW | Wrap old endpoints | Revert api.py |
| **D: Fed Security** | MEDIUM-HIGH | Post-pipeline only, no L1-L8 modification | Keep old stack available |
| **E: Adaptive Exec** | MEDIUM | Pre-pipeline wrapper, L1-L8 untouched | Disable adaptive flag |

### Risk Mitigation by Constraint:

✅ **Constraint 1: Don't modify L1-L8**
- B, C, D, E all following this
- All new logic is PRE- or POST- pipeline
- L1-L8 is a black box we don't touch

✅ **Constraint 2: All tests must pass**
- Running validation tests after each workstream
- New tests are additive only
- Legacy tests unchanged

✅ **Constraint 3: Determinism preserved**
- No conditional inside pipeline
- Same input → same Legacy output always
- New features are optional wrappers

---

## 📊 EFFORT ESTIMATION

| Workstream | Tasks | Time | Complexity |
|-----------|-------|------|-----------|
| **A** | 3 | 2 hours | LOW |
| **B** | 7 | 1-2 hours | LOW |
| **C** | 3 | 30 min | LOW |
| **D** | 3 | 45 min - 1h | MEDIUM-HIGH |
| **E** | 3 | 1 hour | MEDIUM |
| **Testing** | Various | 30 min | MEDIUM |
| **Docs** | Various | 30 min | LOW |
| **TOTAL** | 22+ | 6-7 hours | MEDIUM |

---

## ✅ VALIDATION CHECKLIST

### Per-Workstream:

- [ ] All edits preserve L1-L8 logic
- [ ] All legacy tests pass unchanged
- [ ] New code is removable
- [ ] No data loss scenarios
- [ ] Backward compatibility verified
- [ ] Documentation updated

### Before Production:

- [ ] Full test suite passes
- [ ] Determinism audit (same input test)
- [ ] Performance baseline measured
- [ ] Rollback procedures documented
- [ ] Security review (for Fed Learning)
- [ ] Stakeholder sign-off

---

## 📝 SUCCESS CRITERIA

✅ **Phase 1 Complete When:**

1. Shadow implementations removed (DONE)
2. 48 root files consolidated into /src/layers/
3. Single /src/api.py entry point functional
4. Federated learning has post-pipeline security guards
5. Pre-pipeline adaptive control framework in place
6. All legacy tests pass unchanged
7. All new features are optional & disabled by default
8. "git log" shows clear, atomic commits
9. No L1-L8 pipeline code modified
10. Checksum/determinism audit passed

---

## 🎯 NEXT STEPS

This roadmap is now ready for execution.

**To proceed:**

1. Review and confirm this document
2. Identify any missing dependencies or risks
3. Request start of specific workstream
4. Monitor progress with checkpoint updates

**Current recommendation:**
- **Start with:** Workstream B (file consolidation)
- **Reason:** Smallest risk, highest impact (cleanest codebase)
- **Time:** 1-2 hours for immediate gain

---

**Document Version:** 1.0  
**Status:** Ready for Execution  
**Approval:** Pending user confirmation
