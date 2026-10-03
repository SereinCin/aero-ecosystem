#!/usr/bin/env python3
"""Benchmark harness for the Aero batch CSV pipeline.
Runs each target N times, reports median wall time + throughput, and verifies
that every implementation returns the same count/total.
"""
import os
import statistics
import subprocess
import sys
import time

import psutil

ROWS = 2_000_000
SAMPLES = 5

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH_EXE = os.path.join(HERE, "src", "bench" + (".exe" if os.name == "nt" else ""))

TARGETS = [
    ("aero (standalone exe)", [BENCH_EXE, ], HERE),
    ("python pure", [sys.executable, "bench_py_pure.py", "data.csv"], HERE),
    ("python + numpy", [sys.executable, "bench_py_np.py", "data.csv"], HERE),
]


def run_once(cmd, cwd):
    t0 = time.perf_counter()
    r = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd
    )
    proc = psutil.Process(r.pid)
    peak_rss = 0.0
    cpu_time = 0.0
    prev = None
    last = time.perf_counter()
    while r.poll() is None:
        try:
            now = proc.cpu_times()  # (user, system) seconds across all threads
            if prev is not None:
                cpu_time += (now.user - prev.user) + (now.system - prev.system)
            prev = now
            rss = proc.memory_info().rss / (1024 * 1024)  # MB
            if rss > peak_rss:
                peak_rss = rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        now = time.perf_counter()
        if now - last < 0.01:
            time.sleep(0.01)
        last = now
    out, err = r.communicate()
    wall = time.perf_counter() - t0
    # single-core saturation: fraction of one logical CPU the task actually used
    cpu_pct = cpu_time / wall * 100.0 if wall > 0 else 0.0
    return wall, out, r.returncode, cpu_pct, peak_rss


def parse_result(stdout):
    """Extract (count, total) from an implementation's stdout."""
    cnt = tot = None
    for line in stdout.splitlines():
        if line.startswith("count="):
            cnt = line[6:]
        if line.startswith("total="):
            tot = line[6:]
    return cnt, tot


def main():
    print(f"rows={ROWS}  samples={SAMPLES}  (median)\n")
    expected = None
    results = []
    for name, cmd, cwd in TARGETS:
        times, counts, cpus, rsss = [], [], [], []
        for _ in range(SAMPLES):
            w, out, rc, cpu_pct, peak_rss = run_once(cmd, cwd)
            times.append(w)
            counts.append(parse_result(out))
            cpus.append(cpu_pct)
            rsss.append(peak_rss)
        med = statistics.median(times)
        best = min(times)
        med_cpu = statistics.median(cpus)
        med_rss = statistics.median(rsss)
        # correctness = every sample produced the same count/total
        consistent = all(c == counts[0] for c in counts)
        results.append((name, med))
        print(f"{name:<22} median={med * 1000:8.2f} ms   best={best * 1000:8.2f} ms   "
              f"cpu_1core={med_cpu:5.1f}%   peak_rss={med_rss:7.1f} MB")
        print(f"{'':<22} throughput={ROWS / med / 1e6:6.2f} M rows/s   result_consistent={consistent}")

        if expected is None:
            expected = counts[0]
        status = "OK" if counts[0] == expected else "MISMATCH"
        print(f"           -> count={counts[0][0]} total={counts[0][1]}  vs baseline: {status}")
        print()

    fastest_name, fastest_t = min(results, key=lambda x: x[1])
    print(f"fastest: {fastest_name} ({fastest_t * 1000:.2f} ms)")
    for name, t in results:
        if t == fastest_t:
            continue
        print(f"  {fastest_name} is x{t / fastest_t:.1f} faster than {name}")
    print("\nreference output: count/total from baseline =", expected)


if __name__ == "__main__":
    main()
