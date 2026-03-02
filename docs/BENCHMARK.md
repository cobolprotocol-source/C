# Benchmark Methodology

Benchmarks are grouped into three distinct categories and are executed under identical conditions:

1. **Synthetic datasets** – exercise algorithm extremes using generated inputs.
2. **Real enterprise datasets** – representative production data such as logs and backups.
3. **Apple‑to‑apple comparison vs ZSTD** – identical data and IO paths with a competing compressor.

## 1. Synthetic Datasets

- **Worst‑case entropy:** randomly generated data with maximal entropy.
- **Best‑case entropy:** repeated patterns (e.g. zero‑filled).
- **Adversarial patterns:** structured data designed to trigger pathological behaviour (e.g. incremental counters).

## 2. Real Enterprise Data

- **Logs:** rotated syslogs, application events.
- **Backups:** full database dumps.
- **Archives:** compressed historical files.

## 3. Apple‑to‑Apple Comparison vs ZSTD

- Same input data across both compressors.
- Same IO medium – run tests on HDD, SSD, NVMe, and object storage in separate runs; document media type.
- Same CPU constraints; limit to a single core or document multi‑core scaling.
- ZSTD configured with equivalent compression levels for a fair comparison.

### Metadata Requirements (each run)

Every benchmark report must capture the following hardware and environment details:

- **CPU model** and clock frequency.
- **RAM amount** available to the process.
- **IO medium** type and state (e.g. HDD, SSD, NVMe, object storage).
- **Cache state:** cold cache by default; if warmed, describe warm‑up procedure and timing.
- **Cold vs warm cache** explicitly noted for each test.
- Any preprocessing steps applied to the data.

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

> **Pro tip:** a small helper is provided in `benchmark_utils.py` which can
> collect hardware metadata programmatically.  Example:
>
> ```python
> from benchmark_utils import collect_environment_info
>
> info = collect_environment_info(io_medium='NVMe SSD', cache_state='cold')
> print(info)
> ```
