# Laporan Kebijakan & Refactor Struktur /src — Maret 2026

**Status:** ✅ Perbaikan Otomatis Selesai + Rekomendasi Refactor Terperinci Tersedia

---

## 1. RINGKASAN EKSEKUTIF

Analisis menyeluruh terhadap kode di `/src/` mengungkapkan:
- **Import violations**: 16 file memiliki impor lintas-modul tanpa namespace `src.` yang tepat
- **Class complexity**: 7 kelas melampaui threshold 12 metode (kompleksitas tinggi)
- **Actions taken**: Semua impor internal telah diperbaiki otomatis; refactor plan disiapkan

---

## 2. PERUBAHAN IMPOR INTERNAL (COMPLETED)

### Perbaikan Otomatis Diterapkan
Menggunakan `tools/fix_internal_imports.py`, 16 file di `src/` telah diupdate untuk mengganti:
- `from module_name import X` → `from .module_name import X` (relative import)
- `import module_name` → `from . import module_name`

**File yang diperbarui:**
```
DP_OPTIMIZER_PATCHES.py
adaptive_pipeline.py
backward_compatibility_check.py
core_interfaces.py
dual_mode_engine.py
engine.py
extreme_engine.py
extreme_engine_enhanced.py
gpu_acceleration.py
heterogeneous_orchestrator.py
huffman_parallel.py
integrated_adaptive_optimizer.py
integration_validation_suite.py
layer_optimizer.py
production_streaming_integration.py
validate_v14.py
```

### Verifikasi Policy Checker
Skrip `tools/enforce_src_policies.py` memvalidasi:
- ✅ Semua impor internal sekarang menggunakan namespace relatif atau `src.`
- ✅ Tidak ada cross-folder imports tanpa supervision
- ✅ Siap untuk `src/algorithms/` ketika ada (otomatis akan divalidasi)

---

## 3. ANALISIS KOMPLEKSITAS KELAS

### Metrik Keseluruhan `/src/`
| Metric | Value |
|--------|-------|
| Total classes | 485 |
| Average methods per class | 3.09 (median 3) |
| Average class attributes | 2.52 |
| Average instance attributes | 1.74 |
| Classes with inheritance depth ≤2 | 485 (100%) |

### Kelas yang Memerlukan Refactor (>12 methods)

#### [1] `src/performance_profiles.py::PerformanceProfileManager` 
- **Methods**: 20 ❗
- **Instance attributes**: 6 (moderate state)
- **Recommendation**: Split into **4 focused components**, ~5 methods each
- **Strategy**: 
  - Component A: Profile creation & initialization (5 methods)
  - Component B: Performance tracking & metrics (5 methods)
  - Component C: Profile versioning & history (5 methods)
  - Component D: Profile comparison & analysis (5 methods)

#### [2] `src/profile_versioning.py::ProfileVersionManager`
- **Methods**: 18 ❗
- **Instance attributes**: 5 (low state)
- **Recommendation**: Split into **4 focused components**, ~4-5 methods each
- **Strategy**:
  - Version management (track versions)
  - Change detection (diff logic)
  - Rollback & recovery (state restoration)
  - Versioning UI/API (interface layer)

#### [3] `src/dictionary_manager.py::DictionaryManager`
- **Methods**: 16 ❗
- **Instance attributes**: 11 ⚠️ (high state)
- **Recommendation**: Split into **3 focused components**, ~5-6 methods each
- **Strategy**:
  - Create `DictionaryStorage` class: manage dictionary data structures, persistence
  - Create `DictionaryEncoder` class: encode/decode operations
  - Refactor `DictionaryManager` to orchestrate (facade) — keeps public API stable

#### [4] `src/dual_mode_engine.py::DualModeEngine`
- **Methods**: 15 ❗
- **Instance attributes**: 9 ⚠️ (high state)
- **Recommendation**: Split into **3 focused components**, ~5 methods each
- **Strategy**:
  - `ModeSelector` strategy: decide which compression mode to use
  - `AdaptiveMode` strategy: handle mode 1 logic
  - `FixedMode` strategy: handle mode 2 logic
  - `DualModeEngine` becomes lightweight orchestrator

#### [5] `src/engine.py::DictionaryManager`
- **Methods**: 14 ❗
- **Instance attributes**: 6 (moderate state)
- **Recommendation**: Split into **3 focused components**, ~4-5 methods each
- **Note**: Duplicate of `dictionary_manager.py::DictionaryManager` — consolidate or alias after refactor

#### [6] `src/fpga_controller.py::FPGAController`
- **Methods**: 13 ❗
- **Class attributes**: 5
- **Instance attributes**: 11 ⚠️ (high state)
- **Recommendation**: Split into **3 focused components**, ~4-5 methods each
- **Strategy**:
  - `FPGADeviceManager`: hardware detection, initialization
  - `FPGAComputeKernel`: kernel loading, execution
  - `FPGAMonitor`: performance monitoring, resource tracking
  - `FPGAController`: lightweight wrapper (no state)

#### [7] `src/layer8_final.py::Layer8Final`
- **Methods**: 13 ❗
- **Instance attributes**: 2 (very low state — easiest refactor)
- **Recommendation**: Split into **3 focused components**, ~4-5 methods each
- **Strategy**: Stateless operation separation is cleanest:
  - `Layer8Validation`: verification logic
  - `Layer8Finalization`: finalization steps
  - `Layer8Output`: output formatting
  - `Layer8Final`: compose all three (remains simple)

---

## 4. REFACTOR ROADMAP (PRIORITIZED)

### Phase 1: Low-Risk Refactors (Easy — little state)
1. **`Layer8Final`** (2 instance attrs) — Easiest, safest
   - Timeline: 1-2 hours
   - Risk: Very low (stateless operations)

2. **`ProfileVersionManager`** (5 instance attrs) — Low state
   - Timeline: 2-3 hours
   - Risk: Low

### Phase 2: Medium-Risk Refactors (Moderate state, key logic)
3. **`DualModeEngine`** (9 instance attrs) — Key compression logic
   - Timeline: 4-6 hours
   - Risk: Medium (critical path — requires thorough testing)

4. **`Engine.py::DictionaryManager`** (6 instance attrs) — Consider consolidation first
   - Timeline: 3-4 hours (if consolidating with `dictionary_manager.py`)
   - Risk: Medium

### Phase 3: High-Impact Refactors (Complex state management)
5. **`DictionaryManager`** (11 instance attrs) — Critical data structure
   - Timeline: 6-8 hours
   - Risk: Medium-High (extensive testing required)

6. **`FPGAController`** (11 instance attrs + 5 class attrs) — Hardware control
   - Timeline: 8-10 hours
   - Risk: Medium-High (hardware interaction safety)

7. **`PerformanceProfileManager`** (20 methods, 6 attrs) — Largest, but lower risk
   - Timeline: 6-8 hours
   - Risk: Low-Medium (monitoring code, non-critical path)

---

## 5. TEMPLAT REFACTOR (COPY-PASTE READY)

### Contoh: Bagi Kelas Besar menjadi Strategy Pattern

**Sebelum:**
```python
class LargeClass:
    def __init__(self):
        self.attr_a = ...
        self.attr_b = ...
    
    def method_1(self): ...
    def method_2(self): ...
    def method_3(self): ...
    def method_4(self): ...
    def method_5(self): ...
    def method_6(self): ...
    # 13+ methods total
```

**Sesudah (dengan Composition):**
```python
from abc import ABC, abstractmethod

class ComponentA(ABC):
    @abstractmethod
    def op1(self): pass
    @abstractmethod
    def op2(self): pass
    @abstractmethod
    def op3(self): pass

class ComponentAImpl(ComponentA):
    def __init__(self, attr_a, attr_b):
        self.attr_a = attr_a
        self.attr_b = attr_b
    
    def op1(self): ...
    def op2(self): ...
    def op3(self): ...

class ComponentB(ABC):
    @abstractmethod
    def op4(self): pass
    @abstractmethod
    def op5(self): pass

class ComponentBImpl(ComponentB):
    def __init__(self, attr_c):
        self.attr_c = attr_c
    
    def op4(self): ...
    def op5(self): ...

class LargeClass:
    """Orchestrator — keeps public API compatible."""
    def __init__(self):
        self.comp_a = ComponentAImpl(attr_a=..., attr_b=...)
        self.comp_b = ComponentBImpl(attr_c=...)
    
    def method_1(self): return self.comp_a.op1()
    def method_2(self): return self.comp_a.op2()
    def method_3(self): return self.comp_a.op3()
    def method_4(self): return self.comp_b.op4()
    def method_5(self): return self.comp_b.op5()
    # ... delegation remains clear
```

**Benefits:**
- ✅ Setiap komponen fokus (<6 methods)
- ✅ State terikat dekat dengan logic yang memakai
- ✅ `LargeClass` tetap API-compatible (backward compat)
- ✅ Testable per component (unit testing lebih mudah)

---

## 6. INTEGRASI DENGAN `.github/copilot-instructions.md`

Enforce policies secara otomatis — di setiap PR/commit:

```bash
# Sebelum merge:
python tools/enforce_src_policies.py
# Exit code 0 = pass, 2 = fail
```

Add to CI/CD:
```yaml
- name: Enforce src/ policies
  run: |
    python tools/enforce_src_policies.py || exit 2
```

---

## 7. CHECKLIST ONGOING

- [x] Fix internal imports (16 files updated)
- [x] Identify oversized classes (7 candidates flagged)
- [x] Generate refactor roadmap (prioritized phases)
- [x] Create policy checker (`enforce_src_policies.py`)
- [x] Create import fixer (`fix_internal_imports.py`)
- [ ] **Phase 1 refactor start**: Layer8Final (2-3 hari ke depan)
- [ ] **Phase 2 refactor start**: DualModeEngine + ProfileVersionManager (1-2 minggu)
- [ ] **Phase 3 refactor start**: DictionaryManager + FPGAController (2-3 minggu)
- [ ] Update all tests post-refactor
- [ ] Add type hints & docstrings during refactor
- [ ] Measure performance (regression testing)

---

## 8. NEXT STEPS

1. **Review & Approve** referensi dokumen ini ✓
2. **Merge** import fixes ke main (non-breaking change)
3. **Schedule** Phase 1 refactor (Layer8Final, ProfileVersionManager)
4. **Test thoroughly** post-refactor untuk memastikan backward compat
5. **Iterate** Phase 2-3 sesuai bandwidth tim

---

**Laporan Dibuat:** 2 Maret 2026  
**Oleh:** Senior Software Architect (Automated Analysis)  
**Status:** Ready for Implementation ✅
