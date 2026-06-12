"""
Exact decimal arithmetic for Cruhon — @decimal.*

Wraps Python's `decimal` module: base-10 fixed/floating point with no
binary rounding error. Values are built from strings to stay exact.
No `@import` needed.

━━━ BUILD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @decimal.make[value]       → Decimal(str(value)) — exact decimal
  @decimal.to_float[d]       → float(d)
  @decimal.to_str[d]         → str(d)
  @decimal.to_int[d]         → int(d)

━━━ ARITHMETIC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @decimal.add[a; b]         → a + b (exact)
  @decimal.sub[a; b]         → a - b
  @decimal.mul[a; b]         → a * b
  @decimal.div[a; b]         → a / b
  @decimal.sum[list]         → exact sum of a numeric list

━━━ ROUNDING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @decimal.round[d; places]  → round to N decimal places (ROUND_HALF_UP)
  @decimal.quantize[d; exp]  → quantize to an exponent Decimal (e.g. "0.01")
  @decimal.floor[d]          → round down to integer
  @decimal.ceil[d]           → round up to integer

━━━ MISC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @decimal.sqrt[d]           → square root (exact context)
  @decimal.abs[d]            → absolute value
  @decimal.compare[a; b]     → -1 / 0 / 1
  @decimal.is_zero[d]        → True if the value is zero
"""
from ..registry import register_lib, register_lib_call

_DC = "__import__('decimal')"


def _d(expr: str) -> str:
    return f"{_DC}.Decimal(str({expr}))"


def register():
    register_lib("decimal", "decimal")

    # ── BUILD ─────────────────────────────────────────────────
    register_lib_call("decimal", "make",
        lambda a: _d(a[0]) if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "to_float",
        lambda a: f"float({a[0]})" if a else "0.0")

    register_lib_call("decimal", "to_str",
        lambda a: f"str({a[0]})" if a else "'0'")

    register_lib_call("decimal", "to_int",
        lambda a: f"int({a[0]})" if a else "0")

    # ── ARITHMETIC ────────────────────────────────────────────
    register_lib_call("decimal", "add",
        lambda a: f"({_d(a[0])} + {_d(a[1])})" if len(a) > 1 else f"{_d(a[0])}" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "sub",
        lambda a: f"({_d(a[0])} - {_d(a[1])})" if len(a) > 1 else f"{_d(a[0])}" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "mul",
        lambda a: f"({_d(a[0])} * {_d(a[1])})" if len(a) > 1 else f"{_d(a[0])}" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "div",
        lambda a: f"({_d(a[0])} / {_d(a[1])})" if len(a) > 1 else f"{_d(a[0])}" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "sum",
        lambda a: f"sum(({_DC}.Decimal(str(_x)) for _x in {a[0]}), {_DC}.Decimal('0'))" if a else f"{_DC}.Decimal('0')")

    # ── ROUNDING ──────────────────────────────────────────────
    register_lib_call("decimal", "round",
        lambda a: (
            f"{_d(a[0])}.quantize({_DC}.Decimal(10) ** -int({a[1]}), rounding={_DC}.ROUND_HALF_UP)"
            if len(a) > 1 else
            f"{_d(a[0])}.quantize({_DC}.Decimal('1'), rounding={_DC}.ROUND_HALF_UP)"
            if a else f"{_DC}.Decimal('0')"
        ))

    register_lib_call("decimal", "quantize",
        lambda a: f"{_d(a[0])}.quantize({_DC}.Decimal(str({a[1]})))" if len(a) > 1 else f"{_d(a[0])}" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "floor",
        lambda a: f"{_d(a[0])}.to_integral_value(rounding={_DC}.ROUND_FLOOR)" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "ceil",
        lambda a: f"{_d(a[0])}.to_integral_value(rounding={_DC}.ROUND_CEILING)" if a else f"{_DC}.Decimal('0')")

    # ── MISC ──────────────────────────────────────────────────
    register_lib_call("decimal", "sqrt",
        lambda a: f"{_d(a[0])}.sqrt()" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "abs",
        lambda a: f"abs({_d(a[0])})" if a else f"{_DC}.Decimal('0')")

    register_lib_call("decimal", "compare",
        lambda a: f"int({_d(a[0])}.compare({_d(a[1])}))" if len(a) > 1 else "0")

    register_lib_call("decimal", "is_zero",
        lambda a: f"{_d(a[0])}.is_zero()" if a else "True")
