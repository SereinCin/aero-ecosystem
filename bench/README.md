# Aero Batch Pipeline Benchmark

Reproducible performance benchmark: **Aero standalone EXE vs pure Python vs Python + numpy**, on a realistic batch data-pipeline task.

This is the reproducible evidence base for Aero's positioning — **"write the performance kernel for your Python data pipeline"** — with full scripts, a fixed dataset, and the exact machine configuration so anyone can verify the numbers.

## The task

Process a 2,000,000-row CSV file (`data.csv`), one real-world batch job:

1. Parse each row: `id, price_cents, qty, active`
2. Filter: `active == 1 && price_cents > 5000`
3. Aggregate: `total += price_cents * qty`, `count += 1`

Every implementation must return the **same** `count` / `total`. The harness verifies cross-implementation consistency on every run.

## Results (this machine)

| Implementation | Median | Throughput | CPU (1 core) | Peak RSS |
| --- | --- | --- | --- | --- |
| **Aero (standalone EXE)** | **55 ms** | **36.5 M rows/s** | ~60–86% * | **40.4 MB** |
| Python pure | 822 ms | 2.43 M rows/s | 97.0% | 10.4 MB |
| Python + numpy | 500 ms | 4.00 M rows/s | 95.3% | 114.9 MB |

**Aero is ~15× faster than pure Python and ~9× faster than the vectorized numpy path** — while using 3× less memory than numpy. It also runs as a zero-dependency standalone EXE (no interpreter, no runtime, no environment to install).

The CPU column is single-core utilization = process CPU time / wall time. Python's higher % is simply because a 500–800 ms run is dominated by compute; Aero finishes the whole job in 55 ms, so fixed process startup is a larger share of its wall time. \* Aero's % varies between runs because Windows' default 15.6 ms timer granularity is coarse relative to the 55 ms runtime — the number is approximate.

## Reproduce it

### 1. Prerequisites

- Aero toolchain (`aero build`), see [aero-lang](https://github.com/aero-lang)
- Python 3.10+ with `numpy` and `psutil` installed

```sh
python -m pip install numpy psutil
```

### 2. Generate the fixed dataset

The data is deterministic (seeded RNG), so every machine gets identical input:

```sh
python gen_data.py 2000000 data.csv   # 2,000,000 rows, ~38 MB
```

### 3. Compile the Aero binary

```sh
aero build src/bench.aero              # produces src/bench.exe (Windows) / bench (Linux/macOS)
```

### 4. Run the harness

```sh
python run_bench.py
```

The harness runs each target 5× (median reported), measures wall time, single-core CPU, peak RSS, and cross-checks that all three implementations return the identical `count`/`total`.

## Files

| File | Purpose |
| --- | --- |
| `src/bench.aero` | The benchmark kernel, written in Aero |
| `bench_py_pure.py` | Equivalent pure-Python baseline |
| `bench_py_np.py` | Equivalent vectorized numpy baseline |
| `gen_data.py` | Deterministic dataset generator |
| `run_bench.py` | Measurement harness (median, CPU, RSS, consistency check) |

## Reference output

```
count=950396
total=2496544296331
```

## Machine configuration (as measured)

| | |
| --- | --- |
| CPU | AMD Ryzen 9 9950X3D 16-Core (32 threads) |
| OS | Windows 11 Pro 10.0.26200 |
| Python | 3.12.10 |
| numpy | 2.5.2 |
| Aero | 1.2.0 |

## Fairness notes

- All three targets read the same file and do the same work; wall time includes process startup for each.
- The Aero kernel is single-threaded, like the baselines — no multi-core tricks.
- Numbers are honest and reproducible; regenerate `data.csv` and re-run `run_bench.py` to confirm on your own hardware.

## License

MIT
