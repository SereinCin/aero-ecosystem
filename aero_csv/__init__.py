"""aero_csv — Aero-powered CSV batch aggregation kernel.

A tiny CPython extension whose hot loop is compiled from Aero into a standalone
.pyd/.so: no interpreter in the loop, no per-row Python objects, zero runtime
dependencies.

The input is a string (or bytes) of comma-separated integer rows. Columns are
addressed by 0-based index.
"""

from . import kernel as _kernel

__all__ = [
    "count_if",
    "sum_mul_if",
    "aggregate",
]

__version__ = "0.1.0"


def _coerce(data):
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data).decode("ascii")
    return data


def count_if(data, filter_col, filter_val, value_col, min_value):
    """Number of rows where ``filter_col == filter_val`` and ``value_col > min_value``."""
    return _kernel.count_if(_coerce(data), filter_col, filter_val, value_col, min_value)


def sum_mul_if(data, value_col, qty_col, filter_col, filter_val, min_value):
    """Sum of ``value_col * qty_col`` over rows matching the filter."""
    return _kernel.sum_mul_if(_coerce(data), value_col, qty_col, filter_col, filter_val, min_value)


def aggregate(data, price_col=1, qty_col=2, active_col=3, min_price=5000, active_val=1):
    """One-shot batch aggregation in a single pass: returns ``(count, total)``.

    Reproduces the published aero-bench pipeline: for every row where
    ``active_col == active_val`` and ``price_col > min_price``,
    ``total += price_col * qty_col``.
    """
    data = _coerce(data)
    out = _kernel.aggregate(data, price_col, qty_col, active_col, min_price, active_val)
    # The kernel returns bytes like b"count=950396\ntotal=2496544296331\n".
    lines = out.split(b"\n")
    return int(lines[0][6:]), int(lines[1][6:])
