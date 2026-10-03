#!/usr/bin/env python3
"""numpy baseline for the Aero batch CSV pipeline.
Vectorized: loadtxt then mask+aggregate. Represents the 'you must go numpy' path.
"""
import sys
import time

PATH = sys.argv[1] if len(sys.argv) > 1 else "data.csv"

t0 = time.perf_counter()
arr = __import__("numpy").loadtxt(PATH, delimiter=",", dtype="int64")
_id, price, qty, active = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
mask = (active == 1) & (price > 5000)
count = int(mask.sum())
total = int((price[mask] * qty[mask]).sum())
t1 = time.perf_counter()
print(f"count={count}")
print(f"total={total}")
print(f"time_s={t1 - t0:.6f}")
