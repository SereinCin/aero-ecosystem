# Smoke test for the aero-jsonpath kernel (source = kernel.pyd)
import sys

sys.path.insert(0, r"e:\Projects\AeroProjects\aero-jsonpath\src")
import kernel


def check(expr, data, expected, label=""):
    got = kernel.search(expr, data)
    want = expected.encode() if isinstance(expected, str) else expected
    status = "OK " if got == want else "FAIL"
    print(f"{status} {label or expr!r}: got={got!r} want={want!r}")
    return got == want


ok = True
ok &= check("$", '{"a": 1}', '[{"a":1}]', "root")
ok &= check("a", '{"a": 1}', '[1]', "field")
ok &= check("a.b", '{"a": {"b": 5}}', '[5]', "nested")
ok &= check("$.*", '{"a": 1, "b": 2}', '[1,2]', "star")
ok &= check("[1]", "[10, 20, 30]", "[20]", "index")
ok &= check("[1,2]", "[10, 20, 30]", "[20,30]", "multi-index")
ok &= check("[1:3]", "[10, 20, 30, 40]", "[20,30]", "slice")
ok &= check("[:2]", "[10, 20, 30, 40]", "[10,20]", "slice-head")
ok &= check("[::-2]", "[1, 2, 3, 4, 5]", "[5,3,1]", "slice-rev")
ok &= check("$..c", '{"a": {"c": 1, "b": {"c": 2}}}', "[1,2]", "descendants")
ok &= check("$..author", '{"store": {"book": [{"author": "a1"}, {"author": "a2"}]}}', '["a1","a2"]', "desc-field")
ok &= check("a where b", '{"a": {"b": 1}, "c": {"b": 2}}', '[{"b":1}]', "where")
ok &= check("[?(x)]", '[{"x": 1}, {"y": 2}]', '[{"x":1}]', "filter-exists")
ok &= check("[?(@.price<10)]", '[{"price": 5}, {"price": 15}]', '[{"price":5}]', "filter-lt")
ok &= check("$..book[?(@.isbn)]", '{"store": {"book": [{"isbn": 1}, {"title": "x"}]}}', '[{"isbn":1}]', "filter-desc")
ok &= check("a | b", '{"a": 1, "b": 2}', "[1,2]", "union")
ok &= check("missing", '{"a": 1}', "[]", "missing-field")
ok &= check("foo.bar-baz", '{"foo": {"bar-baz": 3}}', "[3]", "hyphen")
ok &= check("'a.c'", '{"a.c": "d"}', '["d"]', "quoted")
ok &= check("x[2].y", '{"x": [{"y": 1}, {"y": 2}, {"y": 3}]}', "[3]", "chain")

print("\nALL PASS" if ok else "\nSOME FAILED")
