"""aero_jmespath: native JMESPath for Python.

A thin wrapper around the Aero-compiled JMESPath kernel. Exposes
``search(expression, json_string)`` which runs the full parse + evaluate +
serialize pipeline in native code and returns a JSON string.

This is the optional accelerator that ``jmespath.search_json()`` uses when it
is installed.
"""
from .kernel import search
from .kernel import parse_json

__all__ = ["search", "parse_json"]
__version__ = "0.1.0"
