#!/usr/bin/env python3
"""Pure-Python baseline for the Aero batch CSV pipeline (no numpy).
Same task as src/bench.aero: filter active==1 && price>5000, sum price*qty.
"""
import sys
import time

PATH = sys.argv[1] if len(sys.argv) > 1 else "data.csv"

t0 = time.perf_counter()
count = 0
total = 0
with open(PATH, "r") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        _id, price, qty, active = line.split(",")
        price = int(price)
        qty = int(qty)
        active = int(active)
        if active == 1 and price > 5000:
            total += price * qty
            count += 1
t1 = time.perf_counter()
print(f"count={count}")
print(f"total={total}")
print(f"time_s={t1 - t0:.6f}")
