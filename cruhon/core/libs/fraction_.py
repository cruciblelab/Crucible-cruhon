"""
Exact rational arithmetic for Cruhon — @fraction.*

Wraps Python's `fractions.Fraction`: exact numerator/denominator math,
conversion from floats and strings, and reduction. No `@import` needed.

━━━ BUILD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fraction.make[num; den]   → Fraction(num, den)  (e.g. 1, 3 → 1/3)
  @fraction.make[num]        → Fraction(num)
  @fraction.from_float[f]    → exact Fraction, then limit_denominator()
  @fraction.from_str[s]      → Fraction("3/4")

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fraction.numerator[f]     → numerator (int)
  @fraction.denominator[f]   → denominator (int)
  @fraction.to_float[f]      → float(f)
  @fraction.to_str[f]        → "num/den" string
  @fraction.to_tuple[f]      → (numerator, denominator)

━━━ ARITHMETIC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fraction.add[a; b]        → a + b (exact)
  @fraction.sub[a; b]        → a - b
  @fraction.mul[a; b]        → a * b
  @fraction.div[a; b]        → a / b

━━━ REDUCE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @fraction.limit[f; max_den]→ closest fraction with denominator ≤ max_den
"""
from ..registry import register_lib, register_lib_call

_FR = "__import__('fractions').Fraction"


def register():
    register_lib("fraction", "fractions")

    # ── BUILD ─────────────────────────────────────────────────
    register_lib_call("fraction", "make",
        lambda a: (
            f"{_FR}({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"{_FR}({a[0]})" if a else f"{_FR}(0)"
        ))

    register_lib_call("fraction", "from_float",
        lambda a: f"{_FR}(float({a[0]})).limit_denominator()" if a else f"{_FR}(0)")

    register_lib_call("fraction", "from_str",
        lambda a: f"{_FR}({a[0]})" if a else f"{_FR}(0)")

    # ── INSPECT ───────────────────────────────────────────────
    register_lib_call("fraction", "numerator",
        lambda a: f"{a[0]}.numerator" if a else "0")

    register_lib_call("fraction", "denominator",
        lambda a: f"{a[0]}.denominator" if a else "1")

    register_lib_call("fraction", "to_float",
        lambda a: f"float({a[0]})" if a else "0.0")

    register_lib_call("fraction", "to_str",
        lambda a: f"str({a[0]})" if a else "'0'")

    register_lib_call("fraction", "to_tuple",
        lambda a: f"({a[0]}.numerator, {a[0]}.denominator)" if a else "(0, 1)")

    # ── ARITHMETIC ────────────────────────────────────────────
    register_lib_call("fraction", "add",
        lambda a: f"({_FR}({a[0]}) + {_FR}({a[1]}))" if len(a) > 1 else f"{_FR}({a[0]})" if a else f"{_FR}(0)")

    register_lib_call("fraction", "sub",
        lambda a: f"({_FR}({a[0]}) - {_FR}({a[1]}))" if len(a) > 1 else f"{_FR}({a[0]})" if a else f"{_FR}(0)")

    register_lib_call("fraction", "mul",
        lambda a: f"({_FR}({a[0]}) * {_FR}({a[1]}))" if len(a) > 1 else f"{_FR}({a[0]})" if a else f"{_FR}(0)")

    register_lib_call("fraction", "div",
        lambda a: f"({_FR}({a[0]}) / {_FR}({a[1]}))" if len(a) > 1 else f"{_FR}({a[0]})" if a else f"{_FR}(0)")

    # ── REDUCE ────────────────────────────────────────────────
    register_lib_call("fraction", "limit",
        lambda a: f"{_FR}({a[0]}).limit_denominator(int({a[1]}))" if len(a) > 1 else f"{_FR}({a[0]}).limit_denominator()" if a else f"{_FR}(0)")
