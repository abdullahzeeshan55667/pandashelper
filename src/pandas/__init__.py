"""Compatibility shim that prefers a real pandas installation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

__all__: list[str]


def _load_real_pandas() -> ModuleType | None:
    """Attempt to import the system pandas module.

    The project ships with a very small stub implementation that enables unit
    tests to run in offline environments.  When a genuine pandas installation is
    available (for example because the user installed the project with
    ``pip install pandas``), we want to use that instead.  To do so we
    temporarily remove the package's ``src`` directory from ``sys.path`` and ask
    ``importlib`` to resolve the real module.
    """

    package_root = Path(__file__).resolve().parents[1]
    src_path = str(package_root)
    removed_index: int | None = None
    removed_module: ModuleType | None = None

    try:
        current_module = sys.modules.get("pandas")
        if current_module is not None and current_module is sys.modules.get(__name__):
            removed_module = current_module
            sys.modules.pop("pandas", None)

        if src_path in sys.path:
            removed_index = sys.path.index(src_path)
            sys.path.pop(removed_index)

        spec = importlib.util.find_spec("pandas")
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:  # pragma: no cover - defensive fallback
        return None
    finally:
        if removed_index is not None:
            sys.path.insert(removed_index, src_path)
        if removed_module is not None:
            sys.modules["pandas"] = removed_module


_real_module = _load_real_pandas()

if _real_module is not None:
    setattr(_real_module, "__pandas_stub__", False)
    globals().update(_real_module.__dict__)
    exported = getattr(_real_module, "__all__", None)
    if exported is None:
        exported = [name for name in vars(_real_module) if not name.startswith("_")]
    __all__ = list(exported)
    sys.modules[__name__] = _real_module
else:
    from . import _stub as _stub_module

    globals().update({name: getattr(_stub_module, name) for name in _stub_module.__all__})
    __all__ = list(_stub_module.__all__)

