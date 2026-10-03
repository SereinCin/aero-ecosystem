# aero-jsonpath

Native JSONPath engine for Python, powered by an [Aero](https://github.com/SereinCin/aero-lang)-compiled kernel.

## Why

`jsonpath-ng` is the standard Python JSONPath library, but its pure-Python evaluator can be slow on large documents with complex queries (filters, descendants). `aero-jsonpath` provides a drop-in native kernel that handles the common JSONPath subset 2–6× faster on filter/descendant workloads.

## Performance

Benchmark: 2000-book document, full pipeline (parse JSON → evaluate JSONPath → serialize result).

| Expression | aero (q/s) | jsonpath-ng (q/s) | Speedup |
|---|---|---|---|
| `$.store.book[*].title` | 323 | 192 | **1.69×** |
| `$..author` | 261 | 44 | **5.98×** |
| `$..book[?(@.isbn)]` | 144 | 37 | **3.90×** |
| `$.store.book[?(@.price < 10)].title` | 282 | 163 | **1.73×** |
| `$.store.book[?(@.price < 15 & @.category == 'fiction')].title` | 278 | 110 | **2.54×** |
| `$..book[0,1,2].title` | 191 | 51 | **3.77×** |

## Install

```bash
pip install aero-jsonpath
```

## Usage

```python
import json
from aero_jsonpath import search

data = {"store": {"book": [{"title": "A", "price": 8.95}, {"title": "B", "price": 12.99}]}}

# search returns a list of matched values
results = search("$.store.book[?(@.price < 10)].title", json.dumps(data))
# → ["A"]
```

## Supported JSONPath subset

- `$` root, `@` current
- `.field`, `['field']`, `[*]`, `.*`
- `[index]`, `[0,1]` multi-index
- `[start:end:step]` slice
- `..` descendant
- `where` / `wherenot`
- `|` union, `&` intersect
- `[?(expr)]` filter with `== != < <= > >=` and existence checks

## License

MIT
