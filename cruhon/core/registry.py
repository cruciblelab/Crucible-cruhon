"""
cruhon/core/registry.py
=======================
Central registry for libraries, lib calls, and mods.
"""

from __future__ import annotations
from typing import Optional, Callable


# ─────────────────────────────────────────────────────────────
# LIB REGISTRY
# ─────────────────────────────────────────────────────────────

# Supported libraries: clpy name → Python module name
_LIBS: dict[str, str] = {
    "requests":    "requests",
    "file":        "builtins",
    "color":       "builtins",
    "json":        "json",
    "os":          "os",
    "sys":         "sys",
    "math":        "math",
    "random":      "random",
    "time":        "time",
    "datetime":    "datetime",
    "re":          "re",
    "pathlib":     "pathlib",
    "asyncio":     "asyncio",
    "typing":      "typing",
    "dataclasses": "dataclasses",
    "http":        "requests",   # @import[http] → import requests
    "httpx":       "httpx",      # async HTTP client
    "store":       None,         # @import[store] not needed — helpers auto-injected
}

# Lib method call handlers: (namespace, method) → Python code generator
_LIB_CALLS: dict[tuple, Callable] = {}


def register_lib(name: str, python_module: str):
    """
    Add a new library.

    Example (inside a mod):
        from cruhon.core.registry import register_lib
        register_lib("redis", "redis")
    """
    _LIBS[name] = python_module


def register_lib_call(namespace: str, method: str, handler: Callable):
    """
    Register a handler for @namespace.method[args].

    handler(args: list[str]) -> str  (returns Python code)
    """
    _LIB_CALLS[(namespace, method)] = handler


def get_lib(name: str) -> Optional[str]:
    return _LIBS.get(name)


def is_lib_namespace(name: str) -> bool:
    """Return True if name is a registered stdlib namespace (even if import is None)."""
    return name in _LIBS


def get_lib_call(namespace: str, method: str) -> Optional[Callable]:
    return _LIB_CALLS.get((namespace, method))


def list_libs() -> list[str]:
    return sorted(k for k, v in _LIBS.items() if v is not None)


# ─────────────────────────────────────────────────────────────
# CORE LIB CALLS — requests, json, os
# ─────────────────────────────────────────────────────────────

def _setup_core_lib_calls():
    # requests
    register_lib_call("requests", "get",
        lambda args: f"requests.get({args[0]})")
    register_lib_call("requests", "post",
        lambda args: f"requests.post({args[0]}, json={args[1]})" if len(args) > 1 else f"requests.post({args[0]})")
    register_lib_call("requests", "put",
        lambda args: f"requests.put({args[0]}, json={args[1]})" if len(args) > 1 else f"requests.put({args[0]})")
    register_lib_call("requests", "delete",
        lambda args: f"requests.delete({args[0]})")

    # json
    register_lib_call("json", "load",
        lambda args: f"json.loads({args[0]})")
    register_lib_call("json", "dump",
        lambda args: f"json.dumps({args[0]})")

    # os
    register_lib_call("os", "env",
        lambda args: f"os.environ.get({args[0]!r})")
    register_lib_call("os", "path",
        lambda args: f"os.path.join({', '.join(args)})")


def _setup_http_lib_calls():
    """Register @http.* handlers from core/libs/http_.py."""
    from .libs.http_ import HTTP_HANDLERS
    for method, handler in HTTP_HANDLERS.items():
        register_lib_call("http", method, handler)


def _setup_store_lib_calls():
    """Register @store.* handlers from core/libs/store_.py."""
    from .libs.store_ import STORE_HANDLERS
    for method, handler in STORE_HANDLERS.items():
        register_lib_call("store", method, handler)


_setup_core_lib_calls()
_setup_http_lib_calls()
_setup_store_lib_calls()


# ─────────────────────────────────────────────────────────────
# MOD REGISTRY
# ─────────────────────────────────────────────────────────────

_MODS: dict[str, dict] = {}


def register_mod(manifest: dict):
    """
    Register a mod.

    manifest = {
        "name": "cruhon-db",
        "version": "1.0.0",
        "namespace": "db",
        "author": "...",
    }
    """
    name = manifest.get("name", "unknown")
    _MODS[name] = manifest


def get_mod(name: str) -> Optional[dict]:
    return _MODS.get(name)


def list_mods() -> list[str]:
    return sorted(_MODS.keys())


# ─── Stdlib registration ──────────────────────────────────────
def _register_stdlib():
    from .libs.file_  import register as _r_file
    from .libs.time_  import register as _r_time
    from .libs.math_  import register as _r_math
    from .libs.json_  import register as _r_json
    from .libs.color_ import register as _r_color
    _r_file()
    _r_time()
    _r_math()
    _r_json()
    _r_color()

_register_stdlib()
