# LAYER TYPE GUARD IMPLEMENTATION ROADMAP
## Memperbaiki Komunikasi Inter-Layer (L1-L8 Pipeline)

**Status:** 🔴 CRITICAL — 5/8 layers broken, pipeline non-functional  
**Timeline:** 3-5 hari untuk fix + testing  
**Owner:** Senior Lead Architect  
**Approval Gate:** `tools/enforce_src_policies.py + audit_performance_metrics.py`

---

## 1. OVERVIEW & SCOPE

### Current State
- ✅ Layer 2, 5, 8: Functionally correct
- ❌ Layer 1, 3, 4, 6, 7: Type incompatibility breaks chain
- 📊 Health Score: D+ (37% working)
- 🔗 Pipeline Status: **INOPERABLE** end-to-end

### Desired State
- ✅ All 8 layers handle mixed input types
- ✅ Standardized NumPy array output
- ✅ Full L1→L8 pipeline functional
- 📊 Health Score: A (100% working)
- 🔗 Pipeline Status: **FULLY OPERATIONAL**

---

## 2. DETAILED PATCH PLAN

### Phase 1: Layer 1 (Semantic) — High Priority

**File:** `src/layer1_semantic.py`

**Current Problem:**
```python
def encode(self, buffer: TypedBuffer):
    tokens = np.array([ord(c) % 256 for c in buffer.data])  # ← FAILS if NumPy array
```

**Issue:** `ord()` expects char, not int

**Fix (12 lines):**
```python
def encode(self, buffer: TypedBuffer) -> TypedBuffer:
    """Encode: Text → Semantic tokens (NumPy uint8 array)"""
    # FIX: Add type guard for input
    data = buffer.data
    if isinstance(data, np.ndarray):
        # Convert array to string if needed
        try:
            data = data.tobytes().decode('utf-8')
        except:
            data = ''.join(chr(int(x) % 256) for x in data)
    
    tokens = np.array([ord(c) % 256 for c in str(data)], dtype=np.uint8)
    return TypedBuffer.create(tokens, ProtocolLanguage.L1_SEM, np.ndarray)
```

**Validation:**
```python
def test_layer1():
    # Test string input
    buffer_str = TypedBuffer.create("hello", ProtocolLanguage.RAW, str)
    result = layer1.encode(buffer_str)
    assert isinstance(result.data, np.ndarray)
    
    # Test array input
    buffer_arr = TypedBuffer.create(np.array([72, 101, 108, 108, 111]), ProtocolLanguage.RAW, np.ndarray)
    result = layer1.encode(buffer_arr)
    assert isinstance(result.data, np.ndarray)
```

**Effort:** 15 minutes

---

### Phase 2: Layer 3 (Delta) — High Priority

**File:** `src/layer3_delta.py`

**Current Problem:**
```python
def encode(self, buffer):
    diff_result = np.diff(buffer.data)  # ← FAILS if buffer.data is not ndarray
```

**Issue:** `np.diff()` strict about input type

**Fix (15 lines):**
```python
def encode(self, buffer: TypedBuffer) -> TypedBuffer:
    """Encode: Convert to delta encoding"""
    # FIX: Ensure input is ndarray before np.diff()
    data = buffer.data
    if isinstance(data, bytes):
        data = np.frombuffer(data, dtype=np.uint8)
    elif isinstance(data, str):
        data = np.array([ord(c) % 256 for c in data], dtype=np.uint8)
    elif not isinstance(data, np.ndarray):
        data = np.asarray(data, dtype=np.uint8)
    
    if data.ndim > 1:
        data = data.flatten()
    
    diff_result = np.diff(data)
    delta_array = np.concatenate([[data[0]], diff_result])
    
    return TypedBuffer.create(delta_array, ProtocolLanguage.L3_DELTA, np.ndarray)
```

**Validation:**
```python
def test_layer3():
    # Test with ndarray
    buffer_arr = TypedBuffer.create(np.array([100, 102, 104, 106]), ProtocolLanguage.L2_STRUCT, np.ndarray)
    result = layer3.encode(buffer_arr)
    assert isinstance(result.data, np.ndarray)
    
    # Test with bytes
    buffer_bytes = TypedBuffer.create(b"\x64\x66\x68\x6a", ProtocolLanguage.L2_STRUCT, bytes)
    result = layer3.encode(buffer_bytes)
    assert isinstance(result.data, np.ndarray)
```

**Effort:** 20 minutes

---

### Phase 3: Layer 4 (Binary) — High Priority

**File:** `src/layer4_binary.py`

**Current Problem:**
```python
def encode(self, buffer):
    binary_form = buffer.data.tobytes()  # ← FAILS if buffer.data is bytes
```

**Issue:** bytes object has no `.tobytes()` method

**Fix (18 lines):**
```python
def encode(self, buffer: TypedBuffer) -> TypedBuffer:
    """Encode: Binary representation"""
    # FIX: Check if .tobytes() exists before calling
    data = buffer.data
    
    if isinstance(data, bytes):
        binary_form = data
    elif isinstance(data, str):
        binary_form = data.encode('utf-8')
    elif isinstance(data, np.ndarray):
        binary_form = data.tobytes()
    else:
        binary_form = np.asarray(data, dtype=np.uint8).tobytes()
    
    # Convert to bit array
    bit_array = np.unpackbits(np.frombuffer(binary_form, dtype=np.uint8))
    
    return TypedBuffer.create(bit_array, ProtocolLanguage.L4_BINARY, np.ndarray)
```

**Validation:**
```python
def test_layer4():
    # Test with array
    buffer_arr = TypedBuffer.create(np.array([0xFF, 0xAA]), ProtocolLanguage.L3_DELTA, np.ndarray)
    result = layer4.encode(buffer_arr)
    assert isinstance(result.data, np.ndarray)
    
    # Test with bytes
    buffer_bytes = TypedBuffer.create(b"\xff\xaa", ProtocolLanguage.L3_DELTA, bytes)
    result = layer4.encode(buffer_bytes)
    assert isinstance(result.data, np.ndarray)
```

**Effort:** 20 minutes

---

### Phase 4: Layer 6 (Recursive) — Medium Priority

**File:** `src/layer6_recursive.py`

**Current Problem:**
```python
# Type mismatch in operations
result = int_value + bytes_object  # ← Type error!
```

**Issue:** Mixing incompatible types without conversion

**Fix (25 lines, requires refactoring):**
```python
def encode(self, buffer: TypedBuffer) -> TypedBuffer:
    """Encode: Recursive compression"""
    # FIX: Normalize input type first
    data = buffer.data
    
    if isinstance(data, bytes):
        result = self._compress_bytes(data)
    elif isinstance(data, str):
        result = self._compress_string(data)
    else:
        # Convert to array
        data = np.asarray(data)
        result = self._compress_array(data)
    
    return TypedBuffer.create(result, ProtocolLanguage.L6_RECURSIVE, type(result))

def decode(self, buffer: TypedBuffer) -> TypedBuffer:
    """Decode: Reverse recursive compression"""
    data = buffer.data
    
    if isinstance(data, bytes):
        result = self._decompress_bytes(data)
    elif isinstance(data, str):
        result = self._decompress_string(data)
    else:
        result = self._decompress_array(np.asarray(data))
    
    return TypedBuffer.create(result, ProtocolLanguage.L6_RECURSIVE, type(result))

# Helper methods (type-safe)
def _compress_bytes(self, data: bytes) -> bytes:
    # Implementation that returns bytes
    return data

def _compress_string(self, data: str) -> str:
    # Implementation that returns string
    return data

def _compress_array(self, data: np.ndarray) -> np.ndarray:
    # Implementation that returns array
    return data
    
# ... similar for decompress methods ...
```

**Validation:**
```python
def test_layer6():
    # Test type consistency (no mixing)
    for test_data, test_type in [
        (b"data", bytes),
        ("data", str),
        (np.array([1, 2, 3]), np.ndarray)
    ]:
        buffer = TypedBuffer.create(test_data, ProtocolLanguage.L5_RECURSIVE, test_type)
        result = layer6.encode(buffer)
        assert type(result.data) == test_type, f"Type mismatch for {test_type}"
```

**Effort:** 30 minutes

---

### Phase 5: Layer 7 (Bank) — High Priority

**File:** `src/layer7_bank.py`

**Current Problem:**
```python
def encode(self, buffer):
    binary_form = buffer.data.tobytes()  # ← FAILS if buffer.data is bytes
```

**Issue:** Same as Layer 4

**Fix (identical to Layer 4):**
```python
def encode(self, buffer: TypedBuffer) -> TypedBuffer:
    """Encode: Bank compression"""
    # FIX: Check if .tobytes() exists before calling
    data = buffer.data
    
    if isinstance(data, bytes):
        binary_form = data
    elif isinstance(data, str):
        binary_form = data.encode('utf-8')
    elif isinstance(data, np.ndarray):
        binary_form = data.tobytes()
    else:
        binary_form = np.asarray(data, dtype=np.uint8).tobytes()
    
    compressed = self._apply_bank_compression(binary_form)
    return TypedBuffer.create(compressed, ProtocolLanguage.L7_BANK, type(compressed))
```

**Effort:** 15 minutes

---

## 3. IMPLEMENTATION CHECKLIST

### Pre-Patching
- [ ] Read INTER_LAYER_COMMUNICATION_AUDIT.md (reference)
- [ ] Identify all affected layer files (src/layer1-7.py)
- [ ] Review current implementation for each broken layer

### Patching Phase (Per Layer)
- [ ] Edit layer1_semantic.py → add type guards in encode/decode
- [ ] Edit layer3_delta.py → add type guards
- [ ] Edit layer4_binary.py → add type guards
- [ ] Edit layer6_recursive.py → add type normalization + helper methods
- [ ] Edit layer7_bank.py → add type guards
- [ ] Verify each file has correct syntax (no indent errors)

### Validation Phase
- [ ] Create test_layer_*.py for each patched layer
- [ ] Test with mixed input types (bytes, str, ndarray)
- [ ] Verify output is always TypedBuffer with expected data type
- [ ] Run: `python -m pytest tests/test_layer_*.py -v`

### Integration Testing
- [ ] Create test_layer_chain.py
- [ ] Test L1 → L2 → L3 → ... → L8 pipeline
- [ ] Verify zero type errors during chaining
- [ ] Run: `python tools/audit_performance_metrics.py` (all 8 layers should pass)

### Compliance Gates
- [ ] Run: `python tools/enforce_src_policies.py` (must exit 0)
- [ ] Run: `python tools/audit_performance_metrics.py` (all 8 layers functional)
- [ ] No performance regression (>10% throughput drop)

---

## 4. DEPLOYMENT STRATEGY

### Day 1-2: Layer 1, 3, 4, 7 (Similar Fixes)
All 4 layers have straightforward type guard additions. Can batch fix.

```bash
# Make changes to 4 files
# Test each independently
# Commit: "Fix: Add type guards to L1, L3, L4, L7"
```

### Day 2-3: Layer 6 (Refactoring)
Requires helper method extraction. More complex.

```bash
# Refactor Layer 6 with helper methods
# Test extensively with mixed types
# Commit: "Refactor: Normalize type handling in L6"
```

### Day 3-4: Integration Testing
Full pipeline validation.

```bash
# Create comprehensive chain tests
# Run audit script
# Create regression test baseline
# Commit: "Test: Verify L1-L8 pipeline functionality"
```

### Day 4-5: Documentation & Cutover
Final cleanup and activation.

```bash
# Update documentation
# Configure CI/CD gates
# Activate regression testing
# Commit: "Deploy: Activate L1-L8 pipeline with regression tests"
```

---

## 5. ROLLBACK PLAN

If testing fails after patching:

1. **Git Recovery:** `git checkout src/layer*.py` (restore originals)
2. **Partial Rollback:** If only 1-2 layers broken, revert just those files
3. **Root Cause:** Re-analyze via `tools/fix_layer_type_guards.py --check`

---

## 6. SUCCESS METRICS

### Before Patching
- ✅ Layer 2, 5, 8 working (3/8 = 37%)
- ❌ Layer 1, 3, 4, 6, 7 broken (5/8 = 62%)
- 🏆 Grade: D+ (Critical)

### After Patching (Expected)
- ✅ All 8 layers working (8/8 = 100%)
- 📊 Grade: A (Excellent)
- 🔗 Full pipeline: **OPERATIONAL**
- 🚀 Performance baseline re-established

### Regression Testing (Ongoing)
- [ ] CI/CD pipeline runs `audit_performance_metrics.py` on every commit
- [ ] Alert if any layer falls below baseline throughput (>10% drop)
- [ ] Enforce type guard checks in code review

---

## 7. RESPONSIBLE AUDIT & SIGN-OFF

**Who:** Senior Lead Architect (Enforcement Authority)

**Must Verify:**
1. ✅ All type guards properly implemented
2. ✅ No method signatures changed (interface contract maintained)
3. ✅ Performance baseline preserved
4. ✅ Compliance checker passes: `exit 0`
5. ✅ Full L1-L8 integration test passes

**Sign-Off Criteria:**
```
[✅] Type guards added to L1, L3, L4, 6, 7
[✅] All layers accept mixed input types (bytes, str, ndarray)
[✅] All layers return TypedBuffer with standardized data format
[✅] audit_performance_metrics.py shows all 8 layers functional
[✅] Zero regression in throughput (baseline maintained)
[✅] Full integration test: L1→L8 pipeline works start-to-finish
[✅] enforce_src_policies.py passes (exit code 0)
```

---

## 8. NEXT STEPS

1. **Immediate (Today):** Review this roadmap + INTER_LAYER_COMMUNICATION_AUDIT.md
2. **Tomorrow:** Start with Layer 1, 3, 4, 7 (parallel fixes)
3. **Day 3:** Layer 6 refactoring + integration testing
4. **Day 4-5:** Final validation + deployment

**Resources Needed:**
- Reference: `docs/INTER_LAYER_COMMUNICATION_AUDIT.md`
- Tool: `tools/fix_layer_type_guards.py`
- Audit: `tools/audit_performance_metrics.py`
- Validation: `tools/enforce_src_policies.py`

---

Apakah roadmap implementasi ini sudah sesuai dengan visi jangka panjang repositori Anda?

Siap untuk mulai patching hari ini? 🚀
