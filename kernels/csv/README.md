# aero-csv

**C-speed CSV batch aggregation for your Python data pipeline.** A tiny CPython
extension whose hot loop is written in [Aero](https://github.com/SereinCin/aero-lang)
and compiled to a standalone `.pyd` / `.so` — no interpreter in the loop, no
per-row Python objects, zero runtime dependencies.

```python
import aero_csv

data = open("data.csv", "rb").read()      # 2,000,000 rows
count, total = aero_csv.aggregate(data)   # one pass, ~51 ms
# -> (950396, 2496544296331)
```

## Why

Python is great at orchestrating data pipelines and terrible at the hot loop.
numpy helps when the data is already numeric arrays, but ingesting and
filtering raw text still runs through the interpreter row by row. `aero-csv`
moves that step into a compiled kernel: the same task, one function call, no
interpreter in the loop.

The input is plain text (a `str` or `bytes` of comma-separated integer rows),
columns addressed by 0-based index. The kernel parses it with the same code
that ships in the [aero-bench](https://github.com/SereinCin/aero-bench)
reproducible benchmark.

## Install

Requires the [Aero toolchain](https://github.com/SereinCin/aero-lang) to
compile the kernel (this is the whole point — the kernel is your Aero code):

```sh
pip install git+https://github.com/SereinCin/aero-csv
# or locally:
pip install .
```

## API

```python
aero_csv.aggregate(data, price_col=1, qty_col=2, active_col=3,
                   min_price=5000, active_val=1) -> (count, total)
```
Single-pass batch aggregation: for every row where
`active_col == active_val` and `price_col > min_price`,
`total += price_col * qty_col`.

```python
aero_csv.count_if(data, filter_col, filter_val, value_col, min_value) -> int
aero_csv.sum_mul_if(data, value_col, qty_col, filter_col, filter_val, min_value) -> int
```
General single-pass reducers (count / sum of `value_col * qty_col`) over any
integer-column CSV.

## Benchmark

Same task as the published
[aero-bench](https://github.com/SereinCin/aero-bench) pipeline: 2,000,000-row
CSV, filter `active == 1 && price > 5000`, aggregate `total += price * qty`.
5 samples, median wall time.

| Implementation | Time | Throughput | vs aero_csv |
| --- | --- | --- | --- |
| **aero-csv** | **51 ms** | 39.0 M rows/s | — |
| Python pure | 569 ms | 3.52 M rows/s | **11× faster** |
| Python + numpy | 475 ms | 4.21 M rows/s | **9× faster** |

Machine: AMD Ryzen 9 9950X3D, Windows 11, Python 3.12.10, numpy 2.5.2, Aero 1.2.0.

Reproduce it:

```sh
python bench/gen_data.py 2000000 bench/data.csv   # deterministic dataset
python bench/bench.py                             # prints the comparison
```

All implementations must return the identical `(count, total)`; the script
asserts this on every run.

## How it works

```
src/kernel.aero  ── aero build --pyext ──►  aero_csv/kernel.pyd
                                              (compiled Aero → CPython glue)
```

`#[py_export]` functions get auto-generated CPython glue (argument parsing,
return conversion, `PyInit_kernel`), so the Aero kernel is a normal importable
extension module. The wrapper in `aero_csv/__init__.py` is just ergonomics.

## Build from source

```sh
python build.py        # aero build src/kernel.aero --pyext → aero_csv/kernel.pyd
python bench/bench.py  # run the comparison
```

## License

MIT
