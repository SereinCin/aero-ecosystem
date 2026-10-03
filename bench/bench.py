# Benchmark aero-jmespath kernel vs jmespath.py (full pipeline).
#
# Both sides answer "given a JSON string, run a JMESPath query":
#   - aero:      kernel.search(expr, json_str)   (native parse + eval + serialize)
#   - jmespath:  json.loads(json_str) + compiled.search(dict)  (the standard usage)
#
# Note: jmespath 1.1.0 no longer json.loads string inputs, so the load is timed
# explicitly. The Aero kernel also re-parses the expression on every call while
# jmespath reuses a compiled AST, so this is a conservative comparison.
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import kernel

import jmespath

random.seed(7)

# Build a realistic document: 2000 servers, each with 3 instances.
SERVERS = []
for i in range(2000):
    server = {
        "name": "server-%d" % i,
        "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
        "status": "active" if i % 3 else "draining",
        "load": round(random.random(), 3),
        "instances": [
            {
                "id": "i-%d-%c" % (i, c),
                "cpu": round(random.random(), 3),
                "mem": random.choice([256, 512, 1024, 2048, 4096]),
                "tags": {"app": "web", "tier": "prod" if i % 2 else "dev"},
            }
            for c in "abc"
        ],
    }
    SERVERS.append(server)

DOC = json.dumps({"servers": SERVERS})
DOC_SIZE_MB = len(DOC) / 1e6
PARSED = json.loads(DOC)  # pre-parsed once; jmespath load time is measured separately

EXPRESSIONS = [
    ("simple field", "servers[0].name", 500),
    ("wildcard projection", "servers[*].name", 200),
    ("filter + projection", "servers[?status=='active'].name", 200),
    ("nested projection", "servers[*].instances[0].id", 200),
    ("multiselect hash", "servers[*].{id: name, load: load}", 100),
    ("comparison filter", "servers[?load > `0.5`].name", 200),
    ("slice", "servers[0:1000].name", 200),
]


def bench_kernel(expr, iters):
    # warmup
    kernel.search(expr, DOC)
    t0 = time.perf_counter()
    for _ in range(iters):
        kernel.search(expr, DOC)
    dt = time.perf_counter() - t0
    return iters / dt


def bench_jmespath(expr, iters, with_dumps=False):
    compiled = jmespath.compile(expr)
    compiled.search(PARSED)  # warmup
    # load time: json.loads is a fixed cost per query
    t0 = time.perf_counter()
    for _ in range(5):
        json.loads(DOC)
    load_s = (time.perf_counter() - t0) / 5
    t0 = time.perf_counter()
    for _ in range(iters):
        r = compiled.search(PARSED)
        if with_dumps:
            json.dumps(r)
    eval_s = (time.perf_counter() - t0) / iters
    return 1.0 / (load_s + eval_s)


def main():
    print("document: %d servers, %.2f MB JSON" % (len(SERVERS), DOC_SIZE_MB), flush=True)
    print("%-22s %10s %10s %10s %7s" % ("expression", "aero (q/s)", "jp (q/s)", "jp+str (q/s)", "vs jp+str"), flush=True)
    print("-" * 72, flush=True)
    for name, expr, iters in EXPRESSIONS:
        ka = bench_kernel(expr, iters)
        ja = bench_jmespath(expr, iters)
        ja_str = bench_jmespath(expr, iters, with_dumps=True)
        print("%-22s %10.0f %10.0f %10.0f %6.2fx" % (name, ka, ja, ja_str, ka / ja_str), flush=True)


if __name__ == "__main__":
    main()

