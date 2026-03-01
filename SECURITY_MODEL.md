# Security Model

## Threat Model

### Threats

- **Rogue node:** client pretending to be part of federation.
- **Tampered block:** data on disk or in transit modified.
- **Replay attack:** old index entries or snapshots resent.
- **Index poisoning:** insertion of malicious patterns into federated model.

### Trust Boundaries

- **Data plane vs control plane:** cryptographically separate; control messages signed.
- **Local node vs federation:** each node trusts its own L8‑1/L8‑2; federation data is untrusted.
- **Operator vs system:** operator has administrative keys; system enforces least privilege.

## Key Management

- **Scope:** per-node keys for control plane; global read‑only keys for snapshots.
- **Rotation:** keys rotate quarterly or on compromise, with a rolling update protocol that ensures at least one valid key at all times.
- **Compromise impact:** limited to node’s own writes; federation models are signed and reject unknown keys.

## Attack Mitigation

- **Detection:** checksums/hashes at every tier; federation patterns signed and validated.
- **Containment:** a rogue node’s patterns are rejected once signature fails; tampered blocks replaced from L8‑3.
- **Recovery:** replay log and snapshots enable rebuilding corrupted layers; operator can revoke keys and re‑bootstrap federation.

## System Protections

- Protects against unauthorized modification of indexes and data corruption.
- **Does not protect**:
  - Malicious reads by an authenticated node.
  - Physical theft of object store snapshots (encryption must be layered separately).
  - Side‑channel leaks within a node’s RAM.
