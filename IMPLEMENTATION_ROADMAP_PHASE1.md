# 🎯 IMPLEMENTATION ROADMAP: Phase 1 Consolidation

**Timeline:** Next 4 hours  
**Goal:** Remove duplication, establish single source of truth, prepare for adaptive execution

---

## WORKSTREAM A: Remove Shadow Implementations (30 min)

**Objective:** Delete 9 duplicate layer files from root level

### Files to DELETE (Safe - canonicals exist and are being used)

```
src/layer0_classifier.py          → DELETE (canonical: src/layers/core/classifier.py)
src/layer1_semantic.py            → DELETE (canonical: src/layers/core/semantic.py)
src/layer2_structural.py          → DELETE (canonical: src/layers/core/structural.py)
src/layer3_delta.py               → DELETE (canonical: src/layers/core/delta.py)
src/layer4_binary.py              → DELETE (canonical: src/layers/core/bitpacking.py)
src/layer5_optimized.py           → DELETE (canonical: src/layers/variants/l5_recursive.py)
src/layer6_optimized.py           → DELETE (canonical: src/layers/variants/l6_recursive.py)
src/layer7_optimized.py           → DELETE (canonical: src/layers/variants/l7_bank.py)
src/layer8_ultra_extreme_enhanced.py → DELETE (canonical: src/layers/variants/l8_final.py)
```

### Justification
- Canonical versions exist in both cases
- engine.py imports from layers/ structure
- No root-level code depends on these files
- Tests don't reference these directly

---

## WORKSTREAM B: Categorize Root-Level Cruft (60 min)

**Objective:** Classify remaining 72 root-level files, decide: Keep / Move / Archive / Delete

### Category 1: KEEP (Core Infrastructure) - ~15 files
```
config.py                          ✅ Configuration constants
core_interfaces.py                 ✅ Abstract base classes
main.py                            ✅ CLI entry point
__init__.py                        ✅ Package init
energy_aware_execution.py          ✅ Energy monitoring (imported by engine)
distributed_framework.py           ✅ Distribution mode (defer decision)
metrics.py                         ✅ Monitoring/metrics
protocol_bridge.py                 ✅ Protocol compatibility
validator.py                       ✅ Validation utilities
concurrency/lock_free_queue.py     ✅ From Task 2
hardware/hardware_optimizer.py     ✅ From Task 3
```

### Category 2: MOVE to /src/layers/ (~30 files)
```
adaptive_pipeline.py               → layers/pipelines/adaptive.py (consolidate with existing)
dag_compression_pipeline.py        → layers/pipelines/dag.py (consolidate)
dictionary_manager.py              → layers/dictionaries/manager.py (move)
gpu_acceleration.py                → layers/advanced/gpu.py (move)
huffman_gpu.py                     → layers/advanced/huffman_gpu.py (move)
```

### Category 3: ARCHIVE (~15 files - likely dead)
```
DATACENTER_STABILITY_VALIDATION.py    → Archive (test artifact)
DP_OPTIMIZER_PATCHES.py               → Archive (experimental)
advanced_selective_retrieval.py       → Archive (unclear)
auto_tuner.py                         → Archive (unknown use)
backward_compatibility_check.py       → Archive (test)
... (10 more similar)
```

### Category 4: DELETE (~10 files - confirmed dead)
```
cpu_fallback_test.py               → Test artifact
create_quick_ref.py                → Documentation tool (not code)
compile_kernels.py                 → GPU kernel compile (not maintained)
dashboard_framework.py             → UI framework (out of scope)
embedding_providers.py             → Not part of compression
... (5 more confirmed dead)
```

---

## WORKSTREAM C: Establish Single Entry Point (30 min)

**Objective:** Create one authoritative API for compression

### Current State (Confusing)
```python
import src.engine                          # Which engine class?
import src.adaptive_pipeline               # Or this one?
import src.layers.pipelines.engine         # Or this canonical one?
```

### Target State (Clear)
```python
# src/api.py - Single authoritative compression entry point
from src.layers.pipelines.engine import CobolPipeline
from src.layers.pipelines.adaptive import AdaptiveSelector
from src.layers.core.classifier import Layer0Classifier

async def compress(data: bytes, strategy: str = 'adaptive') -> bytes:
    """
    Main compression entry point.
    
    Args:
        data: Input bytes to compress
        strategy: 'adaptive' (auto-tune), 'fast' (skip L5-L7), 'balanced' (default)
    
    Returns:
        Compressed bytes
    """
    if strategy == 'adaptive':
        # Use entropy-aware selector
        classifier = Layer0Classifier()
        classification = classifier.classify(data)
        selector = AdaptiveSelector()
        pipeline = selector.choose(classification.entropy)
    else:
        # Use fixed pipeline
        pipeline = CobolPipeline()
    
    result = pipeline.compress(data)
    return result.compressed_data
```

### Then Update
- `src/main.py` - Import from src/api.py
- `__init__.py` - Re-export from src/api.py
- Deprecate `src.engine`, `src.adaptive_pipeline`

---

## WORKSTREAM D: Audit Federated Learning (45 min)

**Objective:** Identify and document data leakage risks

### Current Security Posture
```
✅ Has differential privacy (DifferentialPrivacy class)
✅ Adds Laplace noise to frequencies
✅ Anonymizes node_id
⚠️  NO ENCRYPTION of shared patterns/statistics
⚠️  NO TTL enforcement on shared patterns  
⚠️  NO ε-δ validation before sharing
⚠️  NO LOCAL-ONLY FALLBACK if federation fails
⚠️  RAW PATTERN BYTES transmitted (could leak structure)
```

### Gaps to Fix
1. **Add encryption wrapper:**
   ```python
   def encrypt_for_sharing(patterns, public_key):
       """Encrypt pattern hex before network transmission"""
   ```

2. **Add pattern TTL:**
   ```python
   @dataclass
   class PatternInfo:
       created_at: float
       ttl_seconds: int = 86400  # 24h
       
       def is_expired(self):
           return time.time() - self.created_at > self.ttl_seconds
   ```

3. **Add fallback to local-only:**
   ```python
   try:
       aggregated = federated_aggregator.aggregate(local_dicts)
   except FederationError:
       # Fallback: use local dictionary only
       aggregated = local_dicts[self_node_id].patterns
   ```

4. **Add ε-δ bounds check:**
   ```python
   assert epsilon >= 0.01, "Privacy budget too high"
   assert delta < 0.001, "Failure probability too high"
   ```

---

## WORKSTREAM E: Prepare Adaptive Execution (45 min)

**Objective:** Set up layer-skipping infrastructure (not full implementation)

### Current Problem
```python
# engine.py line ~3800
for layer in [L1, L2, L3, L4, L5, L6, L7, L8]:
    data = layer.compress(data)  # Always runs, never skips
```

### Target: Entropy-Aware Gating
```python
def compress_adaptive(self, data: bytes) -> bytes:
    """Compress with entropy-aware layer selection."""
    
    # L0: Classify + measure entropy
    entropy = self.L0.measure_entropy(data)
    
    # If high entropy, skip compression
    if entropy > 0.95:
        return self._wrap_uncompressed(data)
    
    # Core layers (L1-L4) always run
    for layer in [L1, L2, L3, L4]:
        prev_size = len(data)
        data = layer.compress(data)
        
        # L7 Adaptive Passthrough: Skip if <5% gain
        if len(data) >= prev_size * 0.95:
            data = prev_data  # Revert
            break
    
    # Optional layers (L5-L6) only if entropy low
    if entropy < 0.3:
        for layer in [L5, L6]:
            prev_size = len(data)
            data = layer.compress(data)
            if len(data) >= prev_size * 0.95:
                data = prev_data  # Revert
                break
    
    # L8: Final wrap (always)
    data = self.L8.wrap(data)
    return data
```

### Implementation Steps (Deferred to next session)
1. Add `entropy` parameter to each layer
2. Add `min_gain_threshold` parameter
3. Implement layer reversion logic
4. Test with various entropy profiles

---

## EXECUTION PLAN (Next 4 hours)

### Hour 1: Workstreams A + B
- Delete 9 shadow files (5 min)
- List all 72 remaining root-level files (5 min)
- Manually categorize into Keep/Move/Archive/Delete (50 min)
- Get user confirmation (5 min)

### Hour 2: Workstream C
- Create `src/api.py` with single entry point (10 min)
- Update `src/main.py` to use new API (5 min)
- Add deprecation warnings to old entry points (5 min)
- Run smoke tests (10 min)

### Hour 3: Workstream D
- Read full federated learning code (15 min)
- Create `FEDERATED_LEARNING_SECURITY.md` with gaps (15 min)
- Add 4 guard measures (encryption, TTL, fallback, bounds) (15 min)

### Hour 4: Workstream E + Consolidation
- Create `layers/pipelines/adaptive_executor.py` infrastructure (15 min)
- Document layer-skipping design in ADL (10 min)
- Run full test suite (15 min)
- Create commit message & push (10 min)

---

## SUCCESS CRITERIA

After this phase:
- [ ] 0 shadow implementations remain in root
- [ ] All root-level files categorized
- [ ] Single entry point established (src/api.py)
- [ ] Federated learning security gaps documented  
- [ ] Adaptive executor infrastructure in place (not full impl)
- [ ] All tests passing
- [ ] No breaking changes to public API

---

## RISK ASSESSMENT

| Risk | Probability | Mitigation |
|------|------------|-----------|
| Breaking existing imports | Low | Keep old entry points with deprecation warnings |
| Federated learning degradation | Low | Only adding guards, not changing logic |
| Test failures after deletion | Low | All shadow files not imported by tests |
| User confusion on new API | Low | Clear documentation + migration guide |

---

## NEXT QUESTION

**Ready to proceed with execution?** (y/n)

If YES:
1. Confirm category assignments (Keep/Move/Archive/Delete)
2. Proceed with deletion & consolidation
3. Run smoke tests

If NO:
- What changes to the plan?
- Any concerns to address first?
