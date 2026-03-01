"""Formatted text display for PyArrow tables.

Provides a show() function for printing PyArrow tables with aligned columns
and optional row truncation. No matplotlib dependency — pure PyArrow + print.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pyarrow as pa


def show(table: pa.Table, n: int = 10) -> None:
    """Display a PyArrow table as formatted text with aligned columns.

    Args:
        table: PyArrow table to display.
        n: Maximum number of rows to show. Defaults to 10. Must be positive.
    """
    if n < 1:
        n = 1
    sliced = table.slice(0, n) if table.num_rows > n else table
    cols = sliced.column_names
    rows = [
        [str(sliced.column(c)[i].as_py()) for c in cols]
        for i in range(sliced.num_rows)
    ]
    widths = [
        max(len(c), *(len(r[j]) for r in rows)) if rows else len(c)
        for j, c in enumerate(cols)
    ]
    header = "  ".join(c.ljust(w) for c, w in zip(cols, widths))
    sep = "  ".join("-" * w for w in widths)
    print(header)
    print(sep)
    for row in rows:
        print("  ".join(v.ljust(w) for v, w in zip(row, widths)))
    if table.num_rows > n:
        print(f"  ... ({table.num_rows - n} more rows)")
