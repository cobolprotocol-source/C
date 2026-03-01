# Design

## 1. L8 Index Tiering – Formal Model

### Responsibilities & Boundaries

| Tier | Responsibility | Primary Medium | Recovery Boundary |
|------|----------------|----------------|-------------------|
| L8‑1 | Negative lookup cache | RAM | Reconstructable from L8‑2 |
| L8‑2 | Source of truth for recent offsets | NVMe/SSD | Replay of append log |
| L8‑3 | Immutable history | Object storage | None (read‑only) |

Define clear invariants per tier:

- **L8‑1**: size ≤ configured maximum; no external dependencies.
- **L8‑2**: log strictly append‑only; on-disk segment hashes must match in‑memory checksums.
- **L8‑3**: snapshots are immutable; each version tagged with hash, timestamp.

Failure boundaries:

- L8‑1 loss → performance degradation only.
- L8‑2 corruption → limited to current segment; other segments intact.
- L8‑3 failure → inability to create new snapshots; existing snapshots unaffected.

## 2. Data Contract Per Layer

For each layer provide:

### L8‑1 Contract
- **Input:** set of recent block references.
- **Output:** membership query answer (true/false).
- **Invariant:** false negatives are allowed only until bloom filter is rebuilt; no false positives.
- **Reversibility:** trivial – any false negative is corrected once data promoted to L8‑2.
- **Entropy:** no entropy change; compressed representation only. Worst‑case entropy identical to input.

### L8‑2 Contract
- **Input:** append record ⟨offset, block‑id, metadata⟩.
- **Output:** deterministic lookup returning block‑id.
- **Invariant:** offset‑to‑block map must be bijective within segment.
- **Reversibility:** full; map entries are not transformed.
- **Entropy:** zero change – pure mapping. Storage overhead bounded by metadata.

### L8‑3 Contract
- **Input:** snapshot of L8‑2 segment.
- **Output:** immutable partition version.
- **Invariant:** snapshot hash matches computed hash; versions strictly increasing.
- **Reversibility:** read‑only; an L8‑3 snapshot can be materialised back to L8‑2 without loss.
- **Entropy:** stable; versioning does not add entropy. Snapshots are exact copies.

These contracts ensure:

- **Silent corruption** is detectable via checksum/hashing at each tier.
- **Non‑reversible transforms** are forbidden.
- **Index drift** prevented by strict append‑only semantics and versioned snapshots.

## 3. Federated Learning (Strictly Bounded)

The federated optimizer exists to harvest repeated patterns across nodes but must be constrained to avoid runaway growth. The following limits are enforced by the protocol and by implementation checks.

### Hard Limits and Metrics

1. **Global pattern cap** – the federation never holds more than **100 000** patterns. When the cap is reached, new candidate patterns are rejected or replace the least‑valuable entry as defined by the cost model below. This cap is a *hard limit*; nodes must not accept more patterns even if local memory remains available.

2. **Pattern TTL / Aging** – every shared pattern is stamped with a creation time. After **N hours** (configurable per deployment), a pattern is marked expired and becomes eligible for eviction. Expiry happens regardless of access count; a retained pattern must be re‑advertised to re‑enter the global set.

3. **Entropy contribution threshold** – a pattern is only shared if the estimated entropy reduction (gain) from using it locally exceeds a minimum δ. The threshold prevents noise or high‑entropy fragments from polluting the model.

4. **Cost model** – each pattern is assigned a cost:

    ```
    cost(pattern) = size(pattern) / compression_gain(pattern)
    ```

    Patterns with cost greater than **C_max** are never admitted to the global set. When eviction is required, the federation removes entries in descending cost order (largest cost first) subject to the cap and TTL constraints.

### Sharing and Eviction Policy

- **Shared data:** only the pattern identifier (hash), its length, frequency and computed entropy gain. No raw data, dedup keys or object contents leave a node.
- **Never shared:** any prefix information that would allow reconstruction of the original block content.
- **Eviction mechanism:** global LRU augmented with TTL and cost. Each eviction cycle sweeps expired patterns first, then high‑cost entries, then least‑recently‑used if the cap is still exceeded.
- **Convergence detection:** track the moving average of entropy gain distributed across federation. If this average falls below ε for **M** successive intervals, the system declares the model converged; further pattern advertisements are throttled.

### Graceful Degradation

Federation lazily defaults to a noop mode when disabled or unreachable:

- Nodes still compute local patterns but never advertise them.
- Shared tables are ignored, TTL/cap enforcement is bypassed in the sense that there are no shared patterns to consider.
- Behaviour of compression routines remains identical to the federated case; only the shared state is empty. There is no performance cliff or failure mode associated with disabling federation.

This document section is designed to support implementation and audit; the enforcement of these rules must be verifiable in logging and telemetry.