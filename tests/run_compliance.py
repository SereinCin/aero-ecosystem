# Run the official JMESPath compliance suite against the Aero kernel.
# Usage: python tests/run_compliance.py [file.json ...]
# A case passes when:
#   - case has "error": kernel returns an ERR marker (parse/invalid-value error)
#   - case has "result": kernel output parsed by json.loads deep-equals the
#     expected result (Python int/float equality makes 1 == 1.0, 0 == 0.0)
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import kernel

COMPLIANCE_DIR = os.path.join(os.path.dirname(__file__), "compliance")


def deep_eq(a, b):
    """Structural equality; Python's == already handles int/float equivalence."""
    return a == b


def run_file(path):
    with open(path, encoding="utf-8") as f:
        cases = json.load(f)
    ok = 0
    fail = 0
    skipped = 0
    failures = []
    for group in cases:
        given = group.get("given", None)
        data = json.dumps(given) if given is not None else "null"
        for case in group.get("cases", []):
            expr = case.get("expression", "")
            got = kernel.search(expr, data)
            if isinstance(got, bytes):
                got_s = got.decode("utf-8", "replace")
            else:
                got_s = got
            is_err = got_s.startswith("\x1eERR")
            if "error" in case:
                if is_err:
                    ok += 1
                else:
                    fail += 1
                    failures.append((expr, "expected error, got " + got_s))
                continue
            if is_err:
                fail += 1
                failures.append((expr, "ERR: " + got_s))
                continue
            expected = case.get("result", None)
            try:
                actual = json.loads(got_s)
            except Exception as e:
                fail += 1
                failures.append((expr, "bad JSON output: %r" % got_s))
                continue
            if deep_eq(actual, expected):
                ok += 1
            else:
                fail += 1
                failures.append((expr, "got %r expected %r" % (actual, expected)))
    name = os.path.basename(path)
    print("%-16s ok=%-4d fail=%-4d" % (name, ok, fail))
    for expr, msg in failures:
        print("    FAIL %-40s %s" % (expr, msg))
    return ok, fail


def main():
    files = sys.argv[1:] or sorted(
        f for f in os.listdir(COMPLIANCE_DIR) if f.endswith(".json")
    )
    total_ok = 0
    total_fail = 0
    for fn in files:
        ok, fail = run_file(os.path.join(COMPLIANCE_DIR, fn))
        total_ok += ok
        total_fail += fail
    print("\nTOTAL ok=%d fail=%d" % (total_ok, total_fail))


if __name__ == "__main__":
    main()
