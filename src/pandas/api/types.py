from __future__ import annotations

from .. import Series


def is_numeric_dtype(series: Series) -> bool:
    """Return ``True`` if all non-null values in *series* look numeric."""

    for value in series:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            continue
        if isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            else:
                continue
        return False
    return True
