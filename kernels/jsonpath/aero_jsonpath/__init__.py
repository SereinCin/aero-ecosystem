"""aero_jsonpath: native JSONPath for Python.

A thin wrapper around the Aero-compiled JSONPath kernel. Exposes
``search(expression, json_string)`` which runs the full parse + evaluate +
serialize pipeline in native code and returns a JSON string of matches.

This is the optional accelerator for ``jsonpath_ng`` when installed.
"""
import json
from .kernel import search as _search


def search(expr, data):
    """Search a JSON document with a JSONPath expression.

    Args:
        expr: JSONPath expression string (e.g. ``$.store.book[*].title``)
        data: JSON string or Python object

    Returns:
        list of matched values
    """
    if isinstance(data, str):
        json_str = data
    else:
        json_str = json.dumps(data, separators=(",", ":"))
    raw = _search(expr, json_str)
    if isinstance(raw, bytes):
        raw = raw.decode()
    if raw.startswith("\x1e"):
        raise ValueError("JSONPath parse error: %s" % raw[1:])
    return json.loads(raw)


__all__ = ["search"]
__version__ = "0.1.0"
