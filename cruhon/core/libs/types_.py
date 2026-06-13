"""
cruhon/core/libs/types_.py
==========================
Dynamic type helpers for Cruhon — @types.*

Build lightweight namespaces, read-only views, and test object kinds
using the stdlib `types` module.

━━━ CONSTRUCT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @types.namespace[]              → empty SimpleNamespace (attr-style object)
  @types.namespace[mapping]       → SimpleNamespace from a dict
  @types.readonly[mapping]        → MappingProxyType (read-only dict view)
  @types.new_class[name]          → create a new empty class by name

━━━ PREDICATES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @types.is_function[obj]         → bool (plain def function)
  @types.is_lambda[obj]           → bool
  @types.is_method[obj]           → bool (bound method)
  @types.is_module[obj]           → bool
  @types.is_generator[obj]        → bool (generator iterator)
  @types.is_builtin[obj]          → bool (builtin function/method)
"""
from ..registry import register_lib, register_lib_call

_TY = "__import__('types')"


def register():
    register_lib("types", None)

    # ── Construct ─────────────────────────────────────────────
    register_lib_call("types", "namespace",
        lambda a: (
            f"{_TY}.SimpleNamespace(**{a[0]})" if a else
            f"{_TY}.SimpleNamespace()"
        ))
    register_lib_call("types", "readonly",
        lambda a: f"{_TY}.MappingProxyType({a[0]})")
    register_lib_call("types", "new_class",
        lambda a: f"{_TY}.new_class({a[0]})")

    # ── Predicates ────────────────────────────────────────────
    _preds = {
        "is_function": "FunctionType", "is_lambda": "LambdaType",
        "is_method": "MethodType", "is_module": "ModuleType",
        "is_generator": "GeneratorType", "is_builtin": "BuiltinFunctionType",
    }
    for _name, _cls in _preds.items():
        register_lib_call("types", _name,
            (lambda c: (lambda a: f"isinstance({a[0]}, {_TY}.{c})"))(_cls))
