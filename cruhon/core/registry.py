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

# Special sentinel: library is builtin (don't @import)
_BUILTIN = "__builtin__"

# Supported libraries: clpy name → Python module name
# Use _BUILTIN sentinel for namespaces that don't need @import
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
    "store":       _BUILTIN,     # @import[store] not needed — helpers auto-injected
    "ctx":         _BUILTIN,     # @ctx.* — context variable access, no import needed
    "text":        _BUILTIN,     # @text.* — string operations, no import needed
    "date":        _BUILTIN,     # @date.* — date/time operations, no import needed
    "crypto":      _BUILTIN,     # @crypto.* — crypto operations, no import needed
    "log":         _BUILTIN,     # @log.* — logging, no import needed
    "config":      _BUILTIN,     # @config.* — config file ops, no import needed
    "shell":       _BUILTIN,     # @shell.* — subprocess operations, no import needed
    "archive":     _BUILTIN,     # @archive.* — compression, no import needed
    "mail":        _BUILTIN,     # @mail.* — email operations, no import needed
    "csv":         _BUILTIN,     # @csv.* — CSV operations, no import needed
    # New in v2.1.0
    "collections": "collections",
    "itertools":   "itertools",
    "functools":   "functools",
    "io":          "io",
    "copy":        "copy",
    "base64":      "base64",
    "url":         _BUILTIN,     # @url.* — urllib.parse, no top-level import needed
    "statistics":  "statistics",
    "contextlib":  "contextlib",
    "enum":        "enum",
    "threading":   "threading",
    "queue":       "queue",
    "heapq":       "heapq",
    "bisect":      "bisect",
    "operator":    "operator",
    "pprint":      "pprint",
    # New in v2.2.0 — backing modules for the cruhon-shortcuts plugin
    "string":      "string",
    "struct":      "struct",
    "zlib":        "zlib",
    "calendar":    "calendar",
    "email":       "email",
    # New in v2.4.0 — data & format namespaces
    "xml":         "xml.etree.ElementTree",
    "toml":        "tomllib",
    "diff":        "difflib",
    "decimal":     "decimal",
    "fraction":    "fractions",
    "ip":          "ipaddress",
    "platform":    "platform",
    "unicode":     "unicodedata",
    "binascii":    "binascii",
    "shlex":       "shlex",
    # New in v2.5.0
    "yaml":        _BUILTIN,     # @yaml.* — PyYAML, requires pip install pyyaml
    "image":       _BUILTIN,     # @image.* — Pillow, requires pip install pillow
    "pdf":         _BUILTIN,     # @pdf.* — pdfplumber, requires pip install pdfplumber
}

# Lib method call handlers: (namespace, method) → Python code generator
_LIB_CALLS: dict[tuple, Callable] = {}


def register_lib(name: str, python_module: str):
    """
    Add a new library.

    Example (inside a mod):
        from cruhon.core.registry import register_lib
        register_lib("redis", "redis")

    Passing None is equivalent to _BUILTIN (namespace with no @import needed).
    """
    _LIBS[name] = python_module if python_module is not None else _BUILTIN


def register_lib_call(namespace: str, method: str, handler: Callable):
    """
    Register a handler for @namespace.method[args].

    handler(args: list[str]) -> str  (returns Python code)
    """
    _LIB_CALLS[(namespace, method)] = handler


def get_lib(name: str) -> Optional[str]:
    if name in _LIBS:
        return _LIBS[name]
    import sys
    if name in getattr(sys, "stdlib_module_names", set()):
        return name
    return None


def is_lib_namespace(name: str) -> bool:
    """Return True if name is a registered stdlib namespace (even if import is None)."""
    return name in _LIBS


def get_lib_call(namespace: str, method: str) -> Optional[Callable]:
    return _LIB_CALLS.get((namespace, method))


def list_libs() -> list[str]:
    return sorted(k for k, v in _LIBS.items() if v is not None and v != _BUILTIN)


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


def _setup_ctx_lib_calls():
    """Register @ctx.* handlers — read/write the __ctx__ execution context dict."""
    register_lib_call("ctx", "set",
        lambda args: f'__ctx__[{args[0]}] = {args[1]}' if len(args) >= 2 else '__ctx__')
    register_lib_call("ctx", "get",
        lambda args: f'__ctx__.get({args[0]}, {args[1] if len(args) > 1 else "None"})')
    register_lib_call("ctx", "clear",
        lambda args: '__ctx__.clear()')
    register_lib_call("ctx", "delete",
        lambda args: f'__ctx__.pop({args[0]}, None)')
    # Stack-based scope operations — push/pop a snapshot frame
    register_lib_call("ctx", "push",
        lambda args: '__ctx_stack__.append(dict(__ctx__))')
    register_lib_call("ctx", "pop",
        lambda args: '__ctx__.clear(); __ctx__.update(__ctx_stack__.pop() if __ctx_stack__ else {})')


_setup_core_lib_calls()
_setup_http_lib_calls()
_setup_store_lib_calls()
_setup_ctx_lib_calls()


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
    from .libs.file_        import register as _r_file
    from .libs.time_        import register as _r_time
    from .libs.date_        import register as _r_date
    from .libs.math_        import register as _r_math
    from .libs.json_        import register as _r_json
    from .libs.color_       import register as _r_color
    from .libs.text_        import register as _r_text
    from .libs.csv_         import register as _r_csv
    from .libs.crypto_      import register as _r_crypto
    from .libs.log_         import register as _r_log
    from .libs.config_      import register as _r_config
    from .libs.shell_       import register as _r_shell
    from .libs.archive_     import register as _r_archive
    from .libs.mail_        import register as _r_mail
    from .libs.random_      import register as _r_random
    from .libs.collections_ import register as _r_collections
    from .libs.itertools_   import register as _r_itertools
    from .libs.functools_   import register as _r_functools
    from .libs.sys_         import register as _r_sys
    from .libs.io_          import register as _r_io
    from .libs.copy_        import register as _r_copy
    from .libs.base64_      import register as _r_base64
    from .libs.url_         import register as _r_url
    from .libs.statistics_  import register as _r_statistics
    from .libs.contextlib_  import register as _r_contextlib
    from .libs.enum_        import register as _r_enum
    from .libs.dataclasses_ import register as _r_dataclasses
    from .libs.typing_      import register as _r_typing
    from .libs.threading_   import register as _r_threading
    from .libs.queue_       import register as _r_queue
    from .libs.heapq_       import register as _r_heapq
    from .libs.bisect_      import register as _r_bisect
    from .libs.operator_    import register as _r_operator
    from .libs.pprint_      import register as _r_pprint
    from .libs.string_      import register as _r_string
    from .libs.struct_      import register as _r_struct
    from .libs.zlib_        import register as _r_zlib
    from .libs.calendar_    import register as _r_calendar
    from .libs.email_       import register as _r_email
    from .libs.xml_         import register as _r_xml
    from .libs.toml_        import register as _r_toml
    from .libs.diff_        import register as _r_diff
    from .libs.decimal_     import register as _r_decimal
    from .libs.fraction_    import register as _r_fraction
    from .libs.ip_          import register as _r_ip
    from .libs.platform_    import register as _r_platform
    from .libs.unicode_     import register as _r_unicode
    from .libs.binascii_    import register as _r_binascii
    from .libs.shlex_       import register as _r_shlex
    from .libs.re_          import register as _r_re
    from .libs.yaml_        import register as _r_yaml
    from .libs.image_       import register as _r_image
    from .libs.pdf_         import register as _r_pdf
    _r_file()
    _r_time()
    _r_date()
    _r_math()
    _r_json()
    _r_color()
    _r_text()
    _r_csv()
    _r_crypto()
    _r_log()
    _r_config()
    _r_shell()
    _r_archive()
    _r_mail()
    _r_random()
    _r_collections()
    _r_itertools()
    _r_functools()
    _r_sys()
    _r_io()
    _r_copy()
    _r_base64()
    _r_url()
    _r_statistics()
    _r_contextlib()
    _r_enum()
    _r_dataclasses()
    _r_typing()
    _r_threading()
    _r_queue()
    _r_heapq()
    _r_bisect()
    _r_operator()
    _r_pprint()
    _r_string()
    _r_struct()
    _r_zlib()
    _r_calendar()
    _r_email()
    _r_xml()
    _r_toml()
    _r_diff()
    _r_decimal()
    _r_fraction()
    _r_ip()
    _r_platform()
    _r_unicode()
    _r_binascii()
    _r_shlex()
    _r_re()
    _r_yaml()
    _r_image()
    _r_pdf()

_register_stdlib()
