"""Lightweight compatibility layer for :mod:`pandas.api`."""

from __future__ import annotations

import importlib
import sys


def _using_stub() -> bool:
    module = sys.modules.get("pandas")
    return bool(getattr(module, "__pandas_stub__", False))


if _using_stub():
    from .types import is_numeric_dtype

    __all__ = ["is_numeric_dtype"]
else:
    real_api = importlib.import_module("pandas.api")
    exported = getattr(real_api, "__all__", None)
    if exported is None:
        exported = [name for name in real_api.__dict__ if not name.startswith("_")]
    globals().update({name: getattr(real_api, name) for name in exported})
    __all__ = exported
