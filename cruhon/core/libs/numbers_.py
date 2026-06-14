"""
cruhon/core/libs/numbers_.py
============================
Numeric-tower ABC checks for Cruhon — @numbers.*

Test which abstract level of the numeric hierarchy an object belongs to.

━━━ PREDICATES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @numbers.is_number[x]           → isinstance(x, Number)
  @numbers.is_complex[x]          → isinstance(x, Complex)
  @numbers.is_real[x]             → isinstance(x, Real)
  @numbers.is_rational[x]         → isinstance(x, Rational)
  @numbers.is_integral[x]         → isinstance(x, Integral)
"""
from ..registry import register_lib, register_lib_call

_NM = "__import__('numbers')"


def register():
    register_lib("numbers", None)

    for _name, _cls in [
        ("is_number", "Number"),
        ("is_complex", "Complex"),
        ("is_real", "Real"),
        ("is_rational", "Rational"),
        ("is_integral", "Integral"),
    ]:
        register_lib_call("numbers", _name,
            (lambda c: (lambda a: f"isinstance({a[0]}, {_NM}.{c})"))(_cls))
