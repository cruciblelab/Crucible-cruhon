"""
cruhon/core/libs/importlib_.py
==============================
Dynamic import helpers for Cruhon — @importlib.*

Import modules and attributes by name at runtime, reload modules, and
inspect module specs.

━━━ IMPORT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @importlib.load[name]           → import a module by string name
  @importlib.attr[name; attr]     → import module and get an attribute
  @importlib.reload[mod]          → reload an already-imported module

  @importlib.from_path[name; path]→ import a module directly from a .py file
  @importlib.exists[name]         → bool: is the module importable?
  @importlib.invalidate[]         → clear import-system caches

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @importlib.spec[name]           → ModuleSpec for a module name
  @importlib.find[name]           → find a loader for name (or None)
  @importlib.origin[name]         → file path of a module, or None
"""
from ..registry import register_lib, register_lib_call

_IL = "__import__('importlib')"


def register():
    register_lib("importlib", None)

    # ── Import ────────────────────────────────────────────────
    register_lib_call("importlib", "load",
        lambda a: f"{_IL}.import_module({a[0]})")
    register_lib_call("importlib", "attr",
        lambda a: f"getattr({_IL}.import_module({a[0]}), {a[1]})")
    register_lib_call("importlib", "reload",
        lambda a: f"{_IL}.reload({a[0]})")
    register_lib_call("importlib", "from_path",
        lambda a: (
            f"(lambda _n, _p: (lambda _spec: (lambda _m: (_spec.loader.exec_module(_m), _m)[1])"
            f"({_IL}.util.module_from_spec(_spec)))"
            f"({_IL}.util.spec_from_file_location(_n, _p)))({a[0]}, {a[1]})"
        ))
    register_lib_call("importlib", "exists",
        lambda a: f"({_IL}.util.find_spec({a[0]}) is not None)")
    register_lib_call("importlib", "invalidate",
        lambda a: f"{_IL}.invalidate_caches()")

    # ── Inspect ───────────────────────────────────────────────
    register_lib_call("importlib", "spec",
        lambda a: f"{_IL}.util.find_spec({a[0]})")
    register_lib_call("importlib", "find",
        lambda a: f"{_IL}.util.find_spec({a[0]})")
    register_lib_call("importlib", "origin",
        lambda a: (
            f"(lambda _s: _s.origin if _s else None)({_IL}.util.find_spec({a[0]}))"
        ))
