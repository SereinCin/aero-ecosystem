import sys
import json

sys.path.insert(0, "src")
import kernel

cases = [
    '{"a": [1, 2.5, -3.14, "hi", true, null]}',
    '{"foo": [{"name": "a"}, {"name": "b"}]}',
    '{"num": 33.3, "neg": -0.5, "int": 5, "zero": 0, "zf": 0.0}',
    '"escaped \\"quotes\\" and \\u00e9 and \\n"',
    '[1, 2, [3, 4, [5]]]',
    '{"unicode": "\\ud83d\\ude00 smile"}',
    '[]',
    '{}',
    'null',
    '42',
    '"simple"',
    '{"e": 2.5e-2, "E": 1e3}',
]

ok = 0
fail = 0
for c in cases:
    got = kernel.parse_json(c)
    try:
        py_parsed = json.loads(c)
    except Exception:
        py_parsed = None
    # compare parsed results structurally
    match = False
    try:
        match = json.loads(got) == py_parsed
    except Exception:
        match = False
    if match:
        ok += 1
        print(f"OK   {c}  ->  {got}")
    else:
        fail += 1
        print(f"FAIL {c}  ->  {got}  (expected {py_parsed})")

print(f"\n{ok} ok, {fail} fail")
