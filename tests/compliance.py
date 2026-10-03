#!/usr/bin/env python3
"""Compare the Aero JSONPath kernel against jsonpath-ng on a broad case set.

Supported subset (matching kernel.aero's grammar):
  fields, wildcard, index, multi-index, slice, descendants, where/wherenot,
  union, root, this, and [?(...)] filters with == != < <= > >= and existence.

Cases jsonpath-ng supports but the kernel does NOT (path-vs-path filters,
`=~` regex, `in`, `not`, array unions like [1,2,3,4,5]... ) are marked as
'known-unsupported' and reported separately, not as failures.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import kernel  # noqa: E402

from jsonpath_ng.ext import parse as jp_parse  # noqa: E402
from jsonpath_ng.exceptions import JsonPathParserError, JsonPathLexerError  # noqa: E402

STORE = {
    "store": {
        "book": [
            {"category": "reference", "author": "Nigel Rees", "title": "Sayings",
             "price": 8.95},
            {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword",
             "price": 12.99},
            {"category": "fiction", "author": "Herman Melville", "title": "Moby",
             "isbn": "0-553-21311-3", "price": 8.99},
            {"category": "fiction", "author": "J. R. R. Tolkien", "title": "LOTR",
             "isbn": "0-395-19395-8", "price": 22.99},
        ],
        "bicycle": {"color": "red", "price": 19.95},
    }
}

# (expr, data, label)
CASES = [
    ("$", STORE, "root"),
    ("$.store.book[*].author", STORE, "field-wildcard"),
    ("$..author", STORE, "desc-field"),
    ("$.store.*", STORE, "star"),
    ("$.store..price", STORE, "desc-price"),
    ("$..book[2]", STORE, "book-index"),
    ("$..book[-1:]", STORE, "book-negative-slice"),
    ("$..book[0,1]", STORE, "book-multi-index"),
    ("$..book[:2]", STORE, "book-slice-head"),
    ("$..book[1:3]", STORE, "book-slice"),
    ("$..book[?(@.isbn)]", STORE, "filter-exists"),
    ("$.store.book[?(@.price < 10)].title", STORE, "filter-lt-int"),
    ("$.store.book[?(@.price < 9)].title", STORE, "filter-lt-int2"),
    ("$.store.book[?(@.price == 9)].title", STORE, "filter-eq-int"),
    ("$.store.book[?(@.price <= 8.99)].title", STORE, "filter-le"),
    ("$.store.book[?(@.price > 20)].title", STORE, "filter-gt"),
    ("$.store.book[?(@.price >= 12.99)].title", STORE, "filter-ge"),
    ("$.store.book[?(@.price == 8.99)].title", STORE, "filter-eq-float"),
    ("$.store.book[?(@.price != 8.99)].title", STORE, "filter-ne-float"),
    ("$.store.book[?(@.category == 'fiction')].title", STORE, "filter-str-eq"),
    ("$..book[?(@.category == 'fiction')].title", STORE, "filter-desc-str"),
    ("$.store.book[0]", STORE, "single-index"),
    ("$.store.book[0].title", STORE, "index-chain"),
    ("$['store']['book'][0]['title']", STORE, "quoted-bracket-chain"),
    ("$.store.book[?(@.price)].title", STORE, "filter-truthy"),
    ("$.store.book[*].price", STORE, "star-price"),
    ("$.store.book.*", STORE, "book-star"),
    ("$..book[?(@.isbn)].title", STORE, "filter-desc-title"),
    ("$.store.book[?(@.price < 10 & @.category == 'fiction')].title", STORE, "filter-and"),
    ("$..*", {"a": {"b": 1}}, "desc-all"),
    ("$.missing", STORE, "missing-top"),
    ("$.store.bicycle.color", STORE, "color"),
    ("a where b", {"a": {"b": 1}, "c": {"b": 2}}, "where"),
    ("a | b", {"a": 1, "b": 2}, "union"),
    ("[1]", [10, 20, 30], "bare-index"),
    ("[1,2]", [10, 20, 30], "bare-multi-index"),
    ("[::-1]", [1, 2, 3], "bare-rev"),
    ("foo.bar", {"foo": {"bar": 5}}, "nested-bare"),
    ("$..book[?(@.price < 10)]", STORE, "filter-lt-obj"),
]

# jsonpath-ng expressions we deliberately do not support yet.
KNOWN_UNSUPPORTED = [
    ("$.store.book[?(@.author =~ /.*REES/i)].author", STORE, "filter-regex"),
    ("$.store.book[?(@.price in [8.95, 8.99])].title", STORE, "filter-in"),
    ("$.store.book[?(@.price < @.price2)]", STORE, "filter-path-rhs"),
    ("$.store.book[0,1,2,3][0,1]", STORE, "array-union"),
]


def ref_hits(expr, data):
    try:
        m = jp_parse(expr).find(data)
    except (JsonPathParserError, JsonPathLexerError):
        return "PARSE_ERR"
    return [x.value for x in m]


def kernel_hits(expr, data):
    raw = kernel.search(expr, json.dumps(data, separators=(",", ":")))
    if raw.startswith(b"\x1e"):
        return "KERNEL_ERR"
    return json.loads(raw.decode())


def norm(v):
    # jsonpath-ng returns Decimal for some numbers; normalize via round-trip json.
    return json.loads(json.dumps(v, separators=(",", ":")))


def main():
    passed = failed = unsupported = 0
    fails = []
    for expr, data, label in CASES:
        want = norm(ref_hits(expr, data))
        got = norm(kernel_hits(expr, data))
        ok = got == want
        if ok:
            passed += 1
            print(f"OK   {label}")
        else:
            failed += 1
            fails.append((label, expr, got, want))
            print(f"FAIL {label}: expr={expr!r}")
            print(f"     got ={got!r}")
            print(f"     want={want!r}")
    print()
    for expr, data, label in KNOWN_UNSUPPORTED:
        try:
            want = ref_hits(expr, data)
        except Exception:
            want = "EXC"
        try:
            got = kernel_hits(expr, data)
        except Exception:
            got = "EXC"
        unsupported += 1
        print(f"SKIP {label}: expr={expr!r} ref={want!r} kernel={got!r}")
    print()
    print(f"passed={passed} failed={failed} known_unsupported={unsupported}")
    if fails:
        print("FAILED:", ", ".join(f[0] for f in fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
