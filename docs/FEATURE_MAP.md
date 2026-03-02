# Internal Feature Map

This document lists the public-facing features asserted in README.md along
with the actual code modules that implement them.  Status reflects whether
there is a concrete implementation available in the repository.

| Feature Name | README Reference | Code Module / Path | Status |
|--------------|------------------|--------------------|--------|
| Multi-layer compression L1-L8 | multiple places, e.g. "COBOL Protocol L1-L4 Compression" | `engine.py` classes `Layer1SemanticMapper` through `Layer8FinalHardening` | Implemented |
| Adaptive pipeline & monitoring | README auto-tuning section | `adaptive_pipeline.py` + `hardware_optimized_layers.py` | Implemented |
| Layer-0 data classifier | "Layer 0 AI-Driven Auto-Tuning" | `layer0_classifier.py` | Implemented |
| Auto-Tuner recommendations | same section | `auto_tuner.py` | Implemented |
| Hardware abstraction & GPU detection | README GPU/HPC mention | `hardware_abstraction_layer.py` | Implemented |
| GPU-accelerated layers (CuPy) | GPU support claim | `hardware_optimized_layers.py` | Implemented (optional) |
| Python wrapper & native bindings | v1.5.3 Native Bindings | `src-py/cobol_protocol` and `cobol-core/src/python_bindings.rs` | Implemented (build required) |
| CLI full pipeline | ``full_pipeline.py`` | `full_pipeline.py` | Implemented |
| Streaming compression simulation | "Streaming Compression & Selective Retrieval" | `streaming_compression_simulator.py` | Implemented (simulation) |
| Advanced selective retrieval | same section | `advanced_selective_retrieval.py` | Implemented (demo) |
| L8 index tiering architecture | "Layer 8 Ultra-Extreme" sections | `layer8_ultra_extreme_enhanced.py`, `layer8_final.py` | Implemented |
| Distributed verification (L8) | streaming section | `advanced_selective_retrieval.py` (L8IntegrityVerifier) | Implemented (simulated) |
| Load balancer simulation | "Advanced Load Balancer" | `load_balancer_simulator.py`, `load_balancer_fast_simulation.py` | Implemented (simulation) |
| Federated learning dictionary optimization | Federated Learning Constraints | `federated_dictionary_learning.py`, `layer6_framework.py` | Implemented |
| Security (AES-256, SHA-256) | multiple (security data) | `engine.py` L1, L2 etc; cryptographic wrappers | Implemented |
| Performance metrics & health | README metrics | `adaptive_pipeline.py` (PerformanceMetrics, monitors) | Implemented |
| Benchmarks & tests | README testing, metrics | `tests/` directory containing `test_*` files | Implemented |
| Docker/pip support (deployment claim) | README deployment | Dockerfile, `setup.py`? (not fully provided) | Partial (packaging exists but not validated) |
| Rust core (L1-L3) | README architecture | `cobol-core/` Rust crate | Implemented (need build) |
| Virtual environment setup | README environment | `.venv` folder included | Provided |

_Status definitions:_
- **Implemented**: core functionality present and exercised by tests.
- **Partial**: code exists but packaging, building, or deployment may require
  additional work.
- **Experimental**: not exposed to README or marked as demo/simulation.
- **Internal-only**: non-public; not referenced in README.


> Note: this map is for internal auditing and should not be distributed
> outside the development team.