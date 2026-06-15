"""
cruhon/core/libs/runpy_.py
==========================
Dynamic module execution for Cruhon — @runpy.*

Run Python modules and script files directly, just like `python -m module`
or `python script.py`, and capture the resulting namespace as a dict.

━━━ RUN MODULE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @runpy.module[name]             → run module as __main__, return namespace
  @runpy.module[name; args]       → run with sys.argv set to args
  @runpy.module_ns[name]          → run in new namespace, return dict
  @runpy.is_module[name]          → True if the module can be found

━━━ RUN PATH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @runpy.path[file]               → run script file, return namespace
  @runpy.path[file; args]         → run with sys.argv set to args
  @runpy.path_ns[file; init]      → run with initial namespace dict

━━━ HELPERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @runpy.find[name]               → find module spec (path, loader, etc.)
  @runpy.result[ns; name]         → get a name from the returned namespace
"""
from ..registry import register_lib, register_lib_call

_RP = "__import__('runpy')"


def register():
    register_lib("runpy", None)

    # ── Run module ────────────────────────────────────────────
    register_lib_call("runpy", "module",
        lambda a: (
            f"(lambda _n, _argv: (lambda _sys: (_sys.argv.__setitem__(slice(None), _argv), "
            f"{_RP}.run_module(_n, run_name='__main__', alter_sys=True))[1])(__import__('sys')))"
            f"({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_RP}.run_module({a[0]}, run_name='__main__', alter_sys=True)"
        ))
    register_lib_call("runpy", "module_ns",
        lambda a: f"{_RP}.run_module({a[0]})")
    register_lib_call("runpy", "is_module",
        lambda a: (
            f"(lambda _n: (lambda: (__import__('importlib').util.find_spec(_n) is not None))())"
            f"({a[0]})"
        ))

    # ── Run path ──────────────────────────────────────────────
    register_lib_call("runpy", "path",
        lambda a: (
            f"(lambda _p, _argv: (lambda _sys: (_sys.argv.__setitem__(slice(None), _argv), "
            f"{_RP}.run_path(_p, run_name='__main__'))[1])(__import__('sys')))"
            f"({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_RP}.run_path({a[0]}, run_name='__main__')"
        ))
    register_lib_call("runpy", "path_ns",
        lambda a: (
            f"{_RP}.run_path({a[0]}, init_globals={a[1]})" if len(a) > 1 else
            f"{_RP}.run_path({a[0]})"
        ))

    # ── Helpers ───────────────────────────────────────────────
    register_lib_call("runpy", "find",
        lambda a: f"__import__('importlib').util.find_spec({a[0]})")
    register_lib_call("runpy", "result",
        lambda a: f"{a[0]}[{a[1]}]")
