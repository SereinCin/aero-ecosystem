#!/usr/bin/env python3
"""Compare `aero_csv` against pure Python and numpy on the aero-bench pipeline.

Same task as the published aero-bench repo: on a 2,000,000-row CSV, filter
`active == 1 && price > 5000`, aggregate `total += price * qty`.

Usage: python bench.py [data.csv]
"""
import os
import statistics
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import aero_csv  # noqa: E402

SAMPLES = 5


def bench(fn, *args):
    times = []
    result = None
    for _ in range(SAMPLES):
        t0 = time.perf_counter()
        result = fn(*args)
        times.append(time.perf_counter() - t0)
    return statistics.median(times), result


def pure_python(path):
    count = total = 0
    with open(path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            _id, price, qty, active = line.split(",")
            price, qty, active = int(price), int(qty), int(active)
            if active == 1 and price > 5000:
                total += price * qty
                count += 1
    return count, total


def numpy_impl(path):
    arr = np.loadtxt(path, delimiter=",", dtype="int64")
    _id, price, qty, active = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
    mask = (active == 1) & (price > 5000)
    return int(mask.sum()), int((price[mask] * qty[mask]).sum())


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data.csv"
    )
    with open(path, "rb") as f:
        raw = f.read()
    rows = raw.count(b"\n")

    t_aero, res_aero = bench(aero_csv.aggregate, raw)
    t_pure, res_pure = bench(pure_python, path)
    t_np, res_np = bench(numpy_impl, path)

    ok = res_aero == res_pure == res_np

    print(f"rows={rows}  samples={SAMPLES}  (median)\n")
    print(f"{'aero_csv':<14} {t_aero * 1000:9.2f} ms   {rows / t_aero / 1e6:6.2f} M rows/s   -> {res_aero}")
    print(f"{'python pure':<14} {t_pure * 1000:9.2f} ms   {rows / t_pure / 1e6:6.2f} M rows/s   -> {res_pure}")
    print(f"{'python+numpy':<14} {t_np * 1000:9.2f} ms   {rows / t_np / 1e6:6.2f} M rows/s   -> {res_np}")
    print(f"\nresults consistent across implementations: {ok}")
    print(f"aero_csv vs python pure : x{t_pure / t_aero:.1f} faster")
    print(f"aero_csv vs python+numpy: x{t_np / t_aero:.1f} faster")


if __name__ == "__main__":
    main()
