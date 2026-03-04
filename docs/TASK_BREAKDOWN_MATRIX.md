# 📋 TASK BREAKDOWN & EXECUTION MATRIX

**Document:** Detailed Task List for Phase 1 Consolidation  
**Format:** Actionable task cards with dependencies and acceptance criteria  
**Date:** March 4, 2026

---

## 🎯 WORKSTREAM B: FILE CONSOLIDATION - DETAILED TASKS

### B1.1: Move Pipeline Orchestrators - Task 1

**Task ID:** B1.1  
**Task:** Move `src/adaptive_pipeline.py` to `src/layers/pipelines/`  
**Status:** PENDING  
**Complexity:** LOW  
**Duration:** 10 minutes  

**Acceptance Criteria:**
- [ ] File moved to `/src/layers/pipelines/adaptive_pipeline.py`
- [ ] All imports updated (search for `from src.adaptive_pipeline`)
- [ ] No broken imports after move
- [ ] Compression test passes
- [ ] Git commit created

**Dependencies:**
- None (can start immediately)

**Validation:**
```bash
# Before move:
grep -r "from src.adaptive_pipeline" src/
# Should show imports

# After move:
python -c "from src.layers.pipelines.adaptive_pipeline import *"  # Should work
pytest tests/test_compression_l0_l8.py::test_pipeline  # Should pass
```

**Rollback:** `git revert <commit>`

---

### B1.2: Move Pipeline Orchestrators - Task 2

**Task ID:** B1.2  
**Task:** Move `src/dag_pipeline.py` to `src/layers/pipelines/`  
**Status:** PENDING  
**Complexity:** LOW  
**Duration:** 10 minutes  

**Acceptance Criteria:**
- [ ] File moved to `/src/layers/pipelines/dag_pipeline.py`
- [ ] Update `src/layers/pipelines/__init__.py` with new export
- [ ] All dependent imports verified
- [ ] Tests pass
- [ ] Git commit created

---

### B1.3: Resolve engine.py Conflict

**Task ID:** B1.3  
**Task:** Consolidate duplicate `src/engine.py` (root) with canonical `src/layers/pipelines/engine.py`  
**Status:** PENDING  
**Complexity:** MEDIUM  
**Duration:** 20 minutes  

**Context:**
```
Currently exists:
├─ src/engine.py (root level)
└─ src/layers/pipelines/engine.py (canonical)

Need to:
1. Compare both files (identify differences)
2. Merge if necessary (root might have legacy code)
3. Keep canonical version only
4. Update all imports
```

**Acceptance Criteria:**
- [ ] Analyzed differences between both files
- [ ] Merged any critical logic (if needed)
- [ ] Deleted `src/engine.py`
- [ ] All imports point to canonical location
- [ ] Tests pass
- [ ] Git commit with rationale

**Validation:**
```bash
diff src/engine.py src/layers/pipelines/engine.py
# Identify critical differences

# After consolidation:
python -c "from src.layers.pipelines.engine import CobolPipeline; print('OK')"
pytest tests/ -k "engine" -v
```

---

### B2.1-B2.6: Move GPU Accelerators

**Task ID:** B2.1 - B2.6  
**Task:** Move 6 GPU-related files to `/src/layers/advanced/gpu/`  
**Status:** PENDING  
**Complexity:** LOW  
**Duration:** 30 minutes total  

**Files:**
```
1. src/fpga_controller.py
2. src/gpu_acceleration.py
3. src/gpu_accelerator.py
4. src/huffman_gpu.py
5. src/huffman_parallel.py
6. src/trie_gpu.py
```

**Checklist per file:**
- [ ] File moved to `/src/layers/advanced/gpu/`
- [ ] Search for imports: `from src.{filename}`
- [ ] Update any found imports
- [ ] Run GPU-related tests (if exist)
- [ ] Git commit (one per file or one for all 6)

**New Directory Structure:**
```
src/layers/advanced/
├─ __init__.py (update exports)
├─ gpu/
│  ├─ __init__.py (new)
│  ├─ fpga_controller.py
│  ├─ gpu_acceleration.py
│  ├─ gpu_accelerator.py
│  ├─ huffman_gpu.py
│  ├─ huffman_parallel.py
│  └─ trie_gpu.py
└─ [other advanced modules]
```

**Validation:**
```python
# Advanced __init__.py should have:
from .gpu import (
    FPGAController,
    GPUAcceleration,
    GPUAccelerator,
    HuffmanGPU,
    HuffmanParallel,
    TrieGPU
)

# Test after move:
python -c "from src.layers.advanced.gpu import HuffmanGPU; print('OK')"
```

---

### B3: Move Dictionary Modules

**Task ID:** B3  
**Task:** Move 5 dictionary files to `/src/layers/dictionaries/`  
**Status:** PENDING  
**Complexity:** MEDIUM (federated learning critical)  
**Duration:** 30 minutes  

**Files:**
```
1. src/dictionary_manager.py
2. src/federated_dictionary_learning.py ⚠️ CRITICAL
3. src/nested_dictionary.py
4. src/numba_dictionary.py
5. src/super_dictionary_system.py
```

**Special Handling for federated_dictionary_learning.py:**

```python
# BEFORE MOVE: Analysis
- Verify no security-critical logic modified
- Check for hardcoded paths
- Look for federation connection strings
- Ensure privacy guards are intact

# AFTER MOVE: Validation
- All auth/API keys still functional
- Pattern sharing still works
- TTL/encryption still in place
- Tests pass without modification
```

**Acceptance Criteria:**
- [ ] All 5 files moved to `/src/layers/dictionaries/`
- [ ] Update `/src/layers/dictionaries/__init__.py`
- [ ] Search & fix cross-imports
- [ ] Federated learning still functional
- [ ] Dictionary tests pass
- [ ] Security review passed (federated module)
- [ ] Git commit

---

### B4: Move Distributed/Federation

**Task ID:** B4  
**Task:** Move 5 federation/cluster files to `/src/layers/distributed/`  
**Status:** PENDING  
**Complexity:** MEDIUM  
**Duration:** 30 minutes  

**Files:**
```
1. src/cluster_orchestrator.py
2. src/distributed_framework.py
3. src/federated_learning_framework.py
4. src/load_balancer_primary.py
5. src/load_balancer_replica.py
```

**Create New Directory:**
```
src/layers/distributed/
├─ __init__.py (new)
├─ cluster_orchestrator.py
├─ distributed_framework.py
├─ federated_learning_framework.py
├─ load_balancer_primary.py
└─ load_balancer_replica.py
```

**Acceptance Criteria:**
- [ ] All 5 files moved
- [ ] Create `/src/layers/distributed/__init__.py`
- [ ] Update `/src/layers/__init__.py` with new exports
- [ ] Fix cross-module imports
- [ ] Test failover scenarios
- [ ] Cluster orchestration still works
- [ ] Load balancing logic validated
- [ ] Git commit

---

### B5: Metrics Decision

**Task ID:** B5  
**Task:** DECISION on metrics files (move or keep in root)  
**Status:** PENDING  
**Complexity:** LOW (decision only)  
**Duration:** 5 minutes  

**Files to Decide On:**
```
- src/metrics.py
- src/metrics_prometheus.py
- src/profiler.py
- src/profile_cpu.py
- src/profile_memory.py
```

**Option 1: Move to `/src/layers/metrics/`**
- Pro: Everything in layers
- Con: Metrics aren't part of compression logic

**Option 2: Keep in Root (RECOMMENDED)**
- Pro: Separates concerns (observability ≠ compression)
- Con: Root level still has files
- Mitigated by: Small number, clear purpose

**Acceptance Criteria:**
- [ ] Decision made and documented
- [ ] Rationale recorded
- [ ] No files moved yet (just decision)

**Recommended:** **KEEP IN ROOT** (metrics are post-pipeline observability)

---

### B6: Consolidate Utilities

**Task ID:** B6  
**Task:** Review and consolidate 6 utility files  
**Status:** PENDING  
**Complexity:** MEDIUM (review intensive)  
**Duration:** 30 minutes  

**Files and Recommended Actions:**

```
src/validator.py
├─ Purpose: Validation logic
├─ Recommendation: Move to src/layers/core/validator.py
└─ Risk: LOW

src/streaming.py
├─ Purpose: Streaming compression
├─ Recommendation: Move to src/layers/advanced/streaming.py
└─ Risk: LOW

src/vector_*.py (multiple files)
├─ Purpose: Vector operations
├─ Recommendation: Move to src/layers/advanced/vectors/
└─ Risk: MEDIUM (interdependencies)

src/embedding_providers.py
├─ Purpose: Embedding providers
├─ Recommendation: Move to src/layers/advanced/embeddings.py
└─ Risk: LOW

src/backward_compatibility_check.py
├─ Purpose: Testing backward compat
├─ Recommendation: Keep in src/tools/
└─ Risk: N/A (testing utility)
```

**Detailed Per-File Actions:**

#### B6.a: Validator
```bash
# Action:
mv src/validator.py src/layers/core/validator.py

# Update imports:
grep -r "from src.validator" src/ || echo "No imports found"

# Test:
python -c "from src.layers.core.validator import *; print('OK')"
```

#### B6.b: Streaming
```bash
# Action:
mv src/streaming.py src/layers/advanced/streaming.py

# Update src/layers/advanced/__init__.py:
# from .streaming import StreamingCompressor

# Test:
python -c "from src.layers.advanced.streaming import *; print('OK')"
```

#### B6.c: Vector Operations
```bash
# Create directory:
mkdir -p src/layers/advanced/vectors/

# Move files:
for f in src/vector_*.py; do
  mv "$f" "src/layers/advanced/vectors/$(basename $f)"
done

# Create src/layers/advanced/vectors/__init__.py

# Test imports after move
```

#### B6.d: Embeddings
```bash
# Action:
mv src/embedding_providers.py src/layers/advanced/embeddings.py

# Update imports and tests
```

#### B6.e: Backward Compat
```bash
# Action: Move to tools (testing utility)
mv src/backward_compatibility_check.py src/tools/backward_compatibility_check.py

# Update tools/__init__.py if needed
```

---

### B7: Unknown Files Analysis

**Task ID:** B7  
**Task:** Categorize and place 20 "unknown" files  
**Status:** PENDING  
**Complexity:** HIGH (requires analysis)  
**Duration:** 45 minutes  

**List of Unknown Files:**
```
1. adaptive_chunk_optimizer.py
2. advanced_selective_retrieval.py
3. cobol_v16_integrated.py
4. dp_optimizer.py
5. generate_compression_report.py
6. generate_datasets.py
7. generate_entropy_statistics.py
8. hardware_abstraction_layer.py
9. hardware_optimized_layers.py
10. heterogeneous_orchestrator.py
11. integrated_adaptive_optimizer.py
12. integration_validation_suite.py
13. layer_optimizer.py
14. layers_optimized.py
15. multi_layer_compressor.py
16. production_streaming_integration.py
17. security_trust_layer.py
18. validate_v14.py
19-20. [Additional 2 files]
```

**Analysis Matrix:**

| File | Purpose | Recommendation | Path | Risk |
|------|---------|-----------------|------|------|
| adaptive_chunk_optimizer | Optimization | Move to advanced/optimizers | `/src/layers/advanced/optimizers/` | MEDIUM |
| advanced_selective_retrieval | Advanced feature | Move to advanced | `/src/layers/advanced/` | LOW |
| cobol_v16_integrated | Integration test | Move to tests | `/tests/integration/` | LOW |
| dp_optimizer | Optimizer | Move to advanced/optimizers | `/src/layers/advanced/optimizers/` | MEDIUM |
| generate_* | Utilities/scripts | Move to tools | `/src/tools/generators/` | LOW |
| hardware_abstraction_layer | Hardware logic | Review separately | TBD | MEDIUM |
| heterogeneous_orchestrator | Orchestrator | Move to layers/distributed | `/src/layers/distributed/` | MEDIUM |
| *_optimizer | Optimization | Move to advanced/optimizers | `/src/layers/advanced/optimizers/` | MEDIUM |
| *_validation | Testing | Move to tests | `/tests/` | LOW |
| production_streaming_integration | Integration | Move to advanced | `/src/layers/advanced/` | MEDIUM |
| security_trust_layer | Security | Review separately | TBD | HIGH |

**Process:**
1. Read first 50 lines of each file
2. Look for: imports, class names, docstrings
3. Categorize per matrix above
4. Create corresponding directories if needed
5. Move files
6. Update imports

**Detailed Sub-Tasks:**

```
B7.a: Move optimizers (3 files)
  ├─ adaptive_chunk_optimizer.py
  ├─ dp_optimizer.py
  └─ layer_optimizer.py
  → /src/layers/advanced/optimizers/
  
B7.b: Move tools (4 files)
  ├─ generate_*.py (4 files)
  → /src/tools/generators/
  
B7.c: Move integrations (2 files)
  ├─ production_streaming_integration.py
  └─ cobol_v16_integrated.py
  → /src/layers/advanced/ (or /tests/integration/)
  
B7.d: Review critical (2 files)
  ├─ security_trust_layer.py ⚠️ SECURITY
  └─ hardware_abstraction_layer.py ⚠️ HARDWARE
  → Needs manual review before moving
  
B7.e: Move orchestration (2 files)
  ├─ heterogeneous_orchestrator.py
  → /src/layers/distributed/
  
B7.f: Move remaining (7+ files)
  ├─ Categorize individually
  ├─ Move to appropriate location
  └─ Verify imports
```

---

## 📊 TASK SUMMARY

| Workstream | # Tasks | Total Time | Status | Risk |
|-----------|---------|-----------|--------|------|
| **B1** | 3 | 40 min | PENDING | LOW-MED |
| **B2** | 6 | 30 min | PENDING | LOW |
| **B3** | 1 | 30 min | PENDING | MEDIUM |
| **B4** | 1 | 30 min | PENDING | MEDIUM |
| **B5** | 1 | 5 min | PENDING | N/A |
| **B6** | 1 | 30 min | PENDING | LOW-MEDIUM |
| **B7** | 1 | 45 min | PENDING | HIGH |
| **TOTAL** | 14 | ~3 hours | PENDING | MEDIUM |

---

## ✅ EXECUTION ORDER (Recommended)

**Sequence by Risk & Dependency:**

1. **B5** (5 min) - Make decision on metrics ← START HERE
2. **B2** (30 min) - Move GPU files (low risk, no dependencies)
3. **B1** (40 min) - Move pipeline orchestrators (handle engine.py conflict carefully)
4. **B6** (30 min) - Consolidate utilities (low-medium risk)
5. **B3** (30 min) - Move dictionary modules (medium risk, federated critical)
6. **B4** (30 min) - Move distributed/orchestration (medium risk)
7. **B7** (45 min) - Handle unknown files (high risk, needs analysis)

**Total Sequential:** ~3 hours  
**Can Parallelize:** B2 can run while doing B1, etc.

---

## 📝 GIT COMMIT STRATEGY

**Recommended approach:**

```bash
# Commit strategy: Atomic per logical group
git commit -m "Task B1: Move pipeline orchestrators to canonical location

- Move src/adaptive_pipeline.py → src/layers/pipelines/
- Move src/dag_pipeline.py → src/layers/pipelines/
- Consolidate engine.py conflicts
- Update all imports
- All tests pass"

# NOT: One commit per file (too granular)
# NOT: All 48 files in one commit (too large)
# BEST: Logical groups, 3-5 files per commit
```

---

**Document Version:** 1.0  
**Status:** Ready for Task Execution  
**Next Step:** Confirm B5 decision, then proceed with B2
