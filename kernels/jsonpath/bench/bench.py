# Benchmark aero-jsonpath kernel vs jsonpath-ng (full pipeline).
#
# Both sides answer "given a JSON document, run a JSONPath query":
#   - aero:      kernel.search(expr, json_str)  (native parse + eval + serialize)
#   - jsonpath-ng:  json.loads(json_str) + parse(expr).find(dict)
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import kernel

from jsonpath_ng.ext import parse as jp_parse

random.seed(7)

# Build a realistic document: 2000 books in a store.
BOOKS = []
for i in range(2000):
    BOOKS.append({
        "category": random.choice(["reference", "fiction", "nonfiction"]),
        "author": "author-%d" % i,
        "title": "title-%d" % i,
        "price": round(random.uniform(5, 30), 2),
        "isbn": "0-553-21311-%d" % i if i % 3 == 0 else None,
    })

DOC = json.dumps({"store": {"book": BOOKS, "bicycle": {"color": "red", "price": 19.95}}})
DOC_SIZE_MB = len(DOC) / 1e6
PARSED = json.loads(DOC)

EXPRESSIONS = [
    ("simple field", "$.store.bicycle.color", 2000),
    ("wildcard", "$.store.book[*].title", 200),
    ("descendant field", "$..author", 200),
    ("filter exists", "$..book[?(@.isbn)]", 100),
    ("filter + proj", "$.store.book[?(@.price < 10)].title", 100),
    ("filter + AND", "$.store.book[?(@.price < 15 & @.category == 'fiction')].title", 100),
    ("slice", "$.store.book[:500].title", 200),
    ("nested chain", "$.store.book[0].author", 2000),
    ("filter str eq", "$.store.book[?(@.category == 'fiction')].title", 100),
    ("multi-index", "$..book[0,1,2].title", 500),
]


def bench_kernel(expr, iters):
    kernel.search(expr, DOC)  # warmup
    t0 = time.perf_counter()
    for _ in range(iters):
        kernel.search(expr, DOC)
    dt = time.perf_counter() - t0
    return iters / dt


def bench_jsonpath_ng(expr, iters, with_dumps=False):
    compiled = jp_parse(expr)
    compiled.find(PARSED)  # warmup
    # load time
    t0 = time.perf_counter()
    for _ in range(5):
        json.loads(DOC)
    load_s = (time.perf_counter() - t0) / 5
    t0 = time.perf_counter()
    for _ in range(iters):
        r = compiled.find(PARSED)
        if with_dumps:
            json.dumps([x.value for x in r])
    eval_s = (time.perf_counter() - t0) / iters
    return 1.0 / (load_s + eval_s)


def main():
    print("document: %d books, %.2f MB JSON" % (len(BOOKS), DOC_SIZE_MB), flush=True)
    print("%-22s %10s %10s %10s %7s" % ("expression", "aero (q/s)", "jpng (q/s)", "jpng+str", "vs jpng+str"), flush=True)
    print("-" * 72, flush=True)
    for name, expr, iters in EXPRESSIONS:
        ka = bench_kernel(expr, iters)
        ja = bench_jsonpath_ng(expr, iters)
        ja_str = bench_jsonpath_ng(expr, iters, with_dumps=True)
        print("%-22s %10.0f %10.0f %10.0f %6.2fx" % (name, ka, ja, ja_str, ka / ja_str), flush=True)


if __name__ == "__main__":
    main()
