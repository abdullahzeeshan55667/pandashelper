from __future__ import annotations

"""Compatibility helpers for :mod:`pandas.api.types`."""

import importlib
import sys


def _using_stub() -> bool:
    module = sys.modules.get("pandas")
    return bool(getattr(module, "__pandas_stub__", False))


if _using_stub():
    from .. import Series

    __all__ = ["is_numeric_dtype"]

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
else:
    real_types = importlib.import_module("pandas.api.types")
    exported = getattr(real_types, "__all__", None)
    if exported is None:
        exported = [name for name in real_types.__dict__ if not name.startswith("_")]
    globals().update({name: getattr(real_types, name) for name in exported})
    __all__ = exported
