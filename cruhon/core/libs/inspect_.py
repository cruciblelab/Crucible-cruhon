"""
cruhon/core/libs/inspect_.py
============================
Live-object introspection for Cruhon — @inspect.*

Look inside functions, classes and modules at runtime — source code,
signatures, docstrings, type predicates.

━━━ SOURCE / DOC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @inspect.source[obj]            → source code as a string
  @inspect.source_lines[obj]      → (lines, starting_line_no)
  @inspect.doc[obj]               → cleaned docstring
  @inspect.comments[obj]          → leading comments above a definition
  @inspect.file[obj]              → file where obj is defined
  @inspect.module[obj]            → the module object containing obj

━━━ SIGNATURE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @inspect.signature[fn]          → "(a, b=1)" signature string
  @inspect.parameters[fn]         → list of parameter names
  @inspect.mro[cls]               → method-resolution-order tuple
  @inspect.members[obj]           → (name, value) pairs of all members

━━━ PREDICATES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @inspect.is_function[obj] @inspect.is_class[obj] @inspect.is_method[obj]
  @inspect.is_module[obj] @inspect.is_generator[obj]
  @inspect.is_coroutine[obj] @inspect.is_builtin[obj]
"""
from ..registry import register_lib, register_lib_call

_IN = "__import__('inspect')"


def register():
    register_lib("inspect", None)

    # ── Source / Doc ──────────────────────────────────────────
    register_lib_call("inspect", "source",
        lambda a: f"{_IN}.getsource({a[0]})")
    register_lib_call("inspect", "source_lines",
        lambda a: f"{_IN}.getsourcelines({a[0]})")
    register_lib_call("inspect", "doc",
        lambda a: f"{_IN}.getdoc({a[0]})")
    register_lib_call("inspect", "comments",
        lambda a: f"{_IN}.getcomments({a[0]})")
    register_lib_call("inspect", "file",
        lambda a: f"{_IN}.getfile({a[0]})")
    register_lib_call("inspect", "module",
        lambda a: f"{_IN}.getmodule({a[0]})")

    # ── Signature ─────────────────────────────────────────────
    register_lib_call("inspect", "signature",
        lambda a: f"str({_IN}.signature({a[0]}))")
    register_lib_call("inspect", "parameters",
        lambda a: f"list({_IN}.signature({a[0]}).parameters)")
    register_lib_call("inspect", "mro",
        lambda a: f"{_IN}.getmro({a[0]})")
    register_lib_call("inspect", "members",
        lambda a: f"{_IN}.getmembers({a[0]})")

    # ── Predicates ────────────────────────────────────────────
    _preds = {
        "is_function": "isfunction", "is_class": "isclass",
        "is_method": "ismethod", "is_module": "ismodule",
        "is_generator": "isgenerator", "is_coroutine": "iscoroutinefunction",
        "is_builtin": "isbuiltin",
    }
    for _name, _impl in _preds.items():
        register_lib_call("inspect", _name,
            (lambda fn: (lambda a: f"{_IN}.{fn}({a[0]})"))(_impl))
