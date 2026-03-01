# Benchmark Methodology

Benchmarks are grouped into three categories and are executed under identical conditions.

## 1. Synthetic Datasets

- **Worst‑case entropy:** randomly generated data with maximal entropy.
- **Best‑case entropy:** repeated patterns (e.g. zero‑filled).
- **Adversarial patterns:** structured data designed to trigger pathological behaviour (e.g. incremental counters).

## 2. Real Enterprise Data

- **Logs:** rotated syslogs, application events.
- **Backups:** full database dumps.
- **Archives:** compressed historical files.

## 3. Comparison vs ZSTD

- Same input data.
- Same IO medium – run tests on HDD, SSD, NVMe, and object storage in separate runs.
- Same CPU constraints; limit to a single core or documented multi‑core scaling.
- ZSTD configured with equivalent compression levels.

### Metadata Requirements (each run)

- CPU model and clock.
- RAM amount.
- IO medium type and state (cold/warm).
- Cache state: explicitly state cache is cold; pre‑warming permitted only if declared.
- Any preprocessing steps.

### Forbidden Practices

- No hidden preprocessing.
- Do not mix IO paths (e.g. nvme read vs network object).
- Do not declare “warm cache” unless the benchmark includes a warm‑up phase.

## Measurements

Report:

- Throughput (MB/s) and latency (ms) for read/write.
- Compression ratio.
- CPU utilisation.
- Entropy gain/loss per dataset.

Each benchmark must include raw logs and scripts to enable reproduction.
