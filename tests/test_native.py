# Verify the native accelerator path inside jmespath.search_json().
#
# Runs from the aero-jmespath repo root:  python tests/test_native.py
# Both repos are on sys.path so the test exercises the real integration:
#   - jmespath.search_json() must pick up the aero_jmespath accelerator
#   - the accelerated result must equal the pure-Python result
#   - error behaviour must be identical to pure Python (ValueError for bad
#     JSON, jmespath.exceptions.ParseError for a bad expression)
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMESPATH_REPO = os.path.join(os.path.dirname(REPO), "jmespath.py")
for p in (REPO, JMESPATH_REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

import aero_jmespath  # noqa: E402
import jmespath  # noqa: E402
from jmespath import exceptions  # noqa: E402

PASS = 0
FAIL = 0


def check(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print("ok   %s" % name)
    except Exception as e:
        FAIL += 1
        print("FAIL %s: %r" % (name, e))


def test_accelerator_present():
    assert jmespath._NATIVE_ACCELERATOR is not None, \
        "aero_jmespath not picked up by jmespath"
    assert jmespath._NATIVE_ACCELERATOR is aero_jmespath.search


def test_results_match():
    doc = '{"servers": [{"name": "x", "up": true}, {"name": "y", "up": false}]}'
    for expr in ("servers[*].name", "servers[?up == `true`].name", "servers[0]",
                 "servers[*].{n: name, u: up}", "@"):
        native = jmespath.search_json(expr, doc)
        pure = jmespath.search(expr, json.loads(doc))
        assert native == pure, "%s: %r != %r" % (expr, native, pure)


def test_number_types():
    # jmespath.py returns int/float depending on the literal; search_json must
    # match search() after json.loads of the serialized native result.
    doc = '{"a": 1, "b": 1.5, "c": -3}'
    assert jmespath.search_json("a", doc) == jmespath.search("a", json.loads(doc))
    assert jmespath.search_json("b", doc) == jmespath.search("b", json.loads(doc))
    assert jmespath.search_json("c", doc) == jmespath.search("c", json.loads(doc))


def test_invalid_json_raises_valueerror():
    try:
        jmespath.search_json("a", "{not json}")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_bad_expression_raises_parseerror():
    try:
        jmespath.search_json("foo[", "{}")
        raise AssertionError("expected ParseError")
    except exceptions.ParseError:
        pass


def test_unquoted_field_missing():
    assert jmespath.search_json("missing", '{"a": 1}') is None


check("accelerator is aero_jmespath.search", test_accelerator_present)
check("native results match pure python", test_results_match)
check("number types survive round-trip", test_number_types)
check("invalid JSON raises ValueError", test_invalid_json_raises_valueerror)
check("bad expression raises ParseError", test_bad_expression_raises_parseerror)
check("missing field -> None", test_unquoted_field_missing)

print("\nPASS=%d FAIL=%d" % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
