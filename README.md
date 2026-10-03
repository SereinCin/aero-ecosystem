# aero-jmespath

A native [JMESPath](https://jmespath.org/) kernel written in [Aero](https://github.com/aero-lang/aero),
compiled to a Python C-extension. It parses JSON, evaluates a JMESPath expression, and
serializes the result entirely in native code — no Python objects are built in between.

## What it is

`jmespath.py` is a pure-Python implementation. Its standard usage is:

```python
import jmespath
result = jmespath.search("servers[?status == `active`].name", data_dict)
```

`aero-jmespath` provides a drop-in equivalent that takes the **raw JSON string** and
returns a **JSON string**, skipping the Python-object round-trip:

```python
import kernel
result = kernel.search("servers[?status == `active`].name", json_str)
```

The Aero kernel runs the full pipeline — JSON parse, expression parse, evaluation and
serialization — in one native pass over the input.

## Build

Requires the [Aero toolchain](https://github.com/aero-lang/aero) (64-bit Windows / macOS /
Linux). From the repo root:

```
aero build src/kernel.aero --pyext     # produces src/kernel.pyd / kernel.so
```

## Usage

```python
import sys
sys.path.insert(0, "src")
import kernel

kernel.search("@", '{"a": 1}')                       # '{"a":1}'
kernel.search("a.b", '{"a": {"b": "x"}}')            # '"x"'
kernel.search("servers[*].name", open("d.json").read())
```

`search(expr, json_str)` returns the serialized result as a JSON string, or
`"\x1eERR1"` (syntax error) / `"\x1eERR2"` (invalid-value error).

## Compliance

Passes all **578** official [jmespath compliance tests](https://github.com/jmespath/jmespath.test/tree/master/compliance)
(identifiers, indices, slices, filters, projections, multiselect, literals, escapes, wildcards, booleans).

```
tests/run_compliance.py

basic.json       ok=18   fail=0
boolean.json     ok=60   fail=0
...
TOTAL ok=578 fail=0
```

## Integration with jmespath.py

`aero-jmespath` is designed to be the optional native accelerator for
[jmespath.py](https://github.com/jmespath/jmespath.py). Once installed
(`pip install aero-jmespath`), `jmespath.search_json(expr, json_string)` runs the
whole parse + eval + serialize pipeline in native code and falls back to pure
Python when the package is absent, so behaviour never changes:

```python
import jmespath
result = jmespath.search_json("servers[?status == `active`].name", json_str)
```

`aero_jmespath.search(expression, json_string)` itself returns a JSON string, so
it can also be used directly.

## Performance

For **one-shot queries** — parse + eval + serialize per call, the typical CLI /
stream / per-request workload where the input is a JSON string — the native
kernel is **1.6–2.2× faster** than `jmespath.py` (`json.loads` + compiled
search), and the advantage grows with document size:

| document | aero-jmespath | jmespath.py | speedup |
|----------|--------------|-------------|---------|
| 0.71 MB  | 5.6 ms       | 9.1 ms      | 1.63×   |
| 3.57 MB  | 30.2 ms      | 56.9 ms     | 1.88×   |
| 7.19 MB  | 61.7 ms      | 133.8 ms    | 2.17×   |

Query: `servers[?status == `active`].instances[0].id` on a synthetic server fleet.
See `bench/` for the scripts.

In a **batch** workload (many queries on a document that is already parsed once,
e.g. `compiled.search(dict)` on a reused dict), `jmespath.py` wins because it
reuses the compiled AST and the already-parsed object; the native kernel
re-parses the expression and document on every call. The speedup is specific to
the one-shot string-input workload.

JSON parsing alone beats CPython's `json.loads`:

```
aero parse_only  4.37 ms   (0.71 MB doc)
json.loads       4.70 ms
```

Expression-level comparison on a 0.71 MB / 2000-server document (queries/sec,
higher is better; `jp+str` = jmespath including result `json.dumps`):

```
expression             aero (q/s)   jp+str (q/s)   vs jp+str
------------------------------------------------------------
simple field                  153           153      1.00x
wildcard projection           132           130      1.01x
filter + projection           121            96      1.27x
nested projection             111           113      0.98x
multiselect hash               89            87      1.02x
comparison filter             107            98      1.10x
slice                         102           152      0.67x
```

## Architecture

- **Flat value arena** — every JSON value lives in one `Vec<Jv>`; arrays and objects
  store value indices, objects keep `[key_index, value_index, ...]` pairs so key names
  survive serialization.
- **Fixed-point numbers** — Aero has no i64→f64 conversion and `extern "C"` cannot
  return `f64`, so numbers are stored as i64 in micro-units (value × 1e6); all
  compliance numbers are short decimals well within range.
- **Index-based serializer** — serialization recurses over value indices rather than
  passing the 32-byte enum by value, so flat arrays of 1M+ elements serialize without
  exhausting the ~1 MB Python thread stack.
- **Expression layer** — a Pratt parser mirrors `jmespath.py`'s binding-power table,
  producing an AST arena that the tree-walking evaluator consumes.

## Files

```
src/kernel.aero          the Aero kernel (parser + evaluator + serializer)
tests/run_compliance.py  runs the official compliance suite
tests/test_parse.py      JSON parser smoke tests
tests/test_native.py     integration test: search_json() accelerated path vs pure Python
bench/bench.py           expression-level benchmark vs jmespath.py
bench/batch.py           batch vs one-shot benchmark
bench/scale.py           speedup vs document size
```

The compiled extension is built locally (`aero build src/kernel.aero --pyext`) and is
not committed to the repository.

## License

MIT
