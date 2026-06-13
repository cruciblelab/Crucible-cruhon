"""
cruhon/core/libs/cmath_.py
==========================
Complex-number math for Cruhon — @cmath.*

Everything in @math, but for complex numbers — plus polar/rectangular
conversions and complex-aware predicates.

━━━ CONSTRUCT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @cmath.complex[re; im]          → complex(re, im)
  @cmath.rect[r; phi]             → from polar (modulus, angle) to complex
  @cmath.polar[z]                 → (modulus, phase) tuple
  @cmath.phase[z]                 → phase angle in radians
  @cmath.modulus[z]               → abs(z) — distance from origin
  @cmath.conjugate[z]             → complex conjugate

━━━ POWER / LOG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @cmath.sqrt[z]                  → complex square root
  @cmath.exp[z]                   → e ** z
  @cmath.log[z]                   → natural log
  @cmath.log[z; base]             → log of z to base
  @cmath.log10[z]                 → base-10 log

━━━ TRIG / HYPERBOLIC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @cmath.sin[z] @cmath.cos[z] @cmath.tan[z]
  @cmath.asin[z] @cmath.acos[z] @cmath.atan[z]
  @cmath.sinh[z] @cmath.cosh[z] @cmath.tanh[z]

━━━ PREDICATES / CONSTANTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @cmath.is_nan[z]                → bool
  @cmath.is_inf[z]                → bool
  @cmath.is_finite[z]             → bool
  @cmath.is_close[a; b]           → bool (approximate equality)
  @cmath.pi[]  @cmath.e[]  @cmath.tau[]  @cmath.inf[]  @cmath.nan[]
"""
from ..registry import register_lib, register_lib_call

_CM = "__import__('cmath')"


def register():
    register_lib("cmath", None)

    # ── Construct ─────────────────────────────────────────────
    register_lib_call("cmath", "complex",
        lambda a: f"complex({a[0]}, {a[1]})")

    register_lib_call("cmath", "rect",
        lambda a: f"{_CM}.rect({a[0]}, {a[1]})")

    register_lib_call("cmath", "polar",
        lambda a: f"{_CM}.polar({a[0]})")

    register_lib_call("cmath", "phase",
        lambda a: f"{_CM}.phase({a[0]})")

    register_lib_call("cmath", "modulus",
        lambda a: f"abs({a[0]})")

    register_lib_call("cmath", "conjugate",
        lambda a: f"complex({a[0]}).conjugate()")

    # ── Power / Log ───────────────────────────────────────────
    register_lib_call("cmath", "sqrt",
        lambda a: f"{_CM}.sqrt({a[0]})")

    register_lib_call("cmath", "exp",
        lambda a: f"{_CM}.exp({a[0]})")

    register_lib_call("cmath", "log",
        lambda a: (
            f"{_CM}.log({a[0]}, {a[1]})" if len(a) > 1 else
            f"{_CM}.log({a[0]})"
        ))

    register_lib_call("cmath", "log10",
        lambda a: f"{_CM}.log10({a[0]})")

    # ── Trig / Hyperbolic ─────────────────────────────────────
    for _fn in ("sin", "cos", "tan", "asin", "acos", "atan",
                "sinh", "cosh", "tanh"):
        register_lib_call("cmath", _fn,
            (lambda name: (lambda a: f"{_CM}.{name}({a[0]})"))(_fn))

    # ── Predicates / Constants ────────────────────────────────
    register_lib_call("cmath", "is_nan",
        lambda a: f"{_CM}.isnan({a[0]})")

    register_lib_call("cmath", "is_inf",
        lambda a: f"{_CM}.isinf({a[0]})")

    register_lib_call("cmath", "is_finite",
        lambda a: f"{_CM}.isfinite({a[0]})")

    register_lib_call("cmath", "is_close",
        lambda a: f"{_CM}.isclose({a[0]}, {a[1]})")

    register_lib_call("cmath", "pi", lambda a: f"{_CM}.pi")
    register_lib_call("cmath", "e", lambda a: f"{_CM}.e")
    register_lib_call("cmath", "tau", lambda a: f"{_CM}.tau")
    register_lib_call("cmath", "inf", lambda a: f"{_CM}.inf")
    register_lib_call("cmath", "nan", lambda a: f"{_CM}.nan")
