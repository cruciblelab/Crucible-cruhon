"""
cruhon-shortcuts-data — numbers group
=======================================
Shortcuts for @decimal.* and @fraction.* — exact arithmetic.

Global aliases (source rewrites)
─────────────────────────────────
@dec_of[value]          → @decimal.make[value]   (note: @dec is a core command)
@dec_add[a; b]          → @decimal.add[a; b]
@dec_sub[a; b]          → @decimal.sub[a; b]
@dec_mul[a; b]          → @decimal.mul[a; b]
@dec_div[a; b]          → @decimal.div[a; b]
@dec_round[d; n]        → @decimal.round[d; n]
@dec_sum[list]          → @decimal.sum[list]
@money[value]           → @decimal.money[value]
@frac[num; den]         → @fraction.make[num; den]
@frac_str[f]            → @fraction.to_str[f]
@frac_float[f]          → @fraction.to_float[f]
@frac_add[a; b]         → @fraction.add[a; b]

Namespace method aliases
─────────────────────────
@decimal.of[v]          → @decimal.make[v]
@decimal.plus[a; b]     → @decimal.add[a; b]
@decimal.times[a; b]    → @decimal.mul[a; b]
@fraction.of[n; d]      → @fraction.make[n; d]
@fraction.str[f]        → @fraction.to_str[f]
@fraction.float[f]      → @fraction.to_float[f]

New methods (via api.lib_call)
───────────────────────────────
@decimal.money[v]         → round v to 2 decimal places (currency)
@decimal.percent[p; t]    → exact percentage (p / t * 100), 2 dp
@decimal.average[list]    → exact mean of a numeric list
@fraction.as_percent[f]   → float percentage of a fraction
@fraction.reciprocal[f]   → 1 / f as a Fraction
"""
from __future__ import annotations

_DC = "__import__('decimal')"
_FR = "__import__('fractions').Fraction"


GLOBAL_REWRITES: dict[str, str] = {
    "@dec_of[":      "@decimal.make[",
    "@dec_add[":     "@decimal.add[",
    "@dec_sub[":     "@decimal.sub[",
    "@dec_mul[":     "@decimal.mul[",
    "@dec_div[":     "@decimal.div[",
    "@dec_round[":   "@decimal.round[",
    "@dec_sum[":     "@decimal.sum[",
    "@money[":       "@decimal.money[",
    "@frac[":        "@fraction.make[",
    "@frac_str[":    "@fraction.to_str[",
    "@frac_float[":  "@fraction.to_float[",
    "@frac_add[":    "@fraction.add[",
}

METHOD_ALIASES: dict[str, str] = {
    "@decimal.of[":     "@decimal.make[",
    "@decimal.plus[":   "@decimal.add[",
    "@decimal.times[":  "@decimal.mul[",
    "@fraction.of[":    "@fraction.make[",
    "@fraction.str[":   "@fraction.to_str[",
    "@fraction.float[": "@fraction.to_float[",
}


def _new_lib_calls(api) -> None:

    api.lib_call("decimal", "money", lambda a: (
        f"{_DC}.Decimal(str({a[0]})).quantize({_DC}.Decimal('0.01'), "
        f"rounding={_DC}.ROUND_HALF_UP)"
        if a else f"{_DC}.Decimal('0.00')"
    ))

    api.lib_call("decimal", "percent", lambda a: (
        f"((({_DC}.Decimal(str({a[0]})) / {_DC}.Decimal(str({a[1]}))) * 100)"
        f".quantize({_DC}.Decimal('0.01'), rounding={_DC}.ROUND_HALF_UP) "
        f"if {a[1]} else {_DC}.Decimal('0.00'))"
        if len(a) > 1 else f"{_DC}.Decimal('0.00')"
    ))

    api.lib_call("decimal", "average", lambda a: (
        f"(lambda _lst: (sum(({_DC}.Decimal(str(_x)) for _x in _lst), {_DC}.Decimal('0')) "
        f"/ len(_lst)) if _lst else {_DC}.Decimal('0'))(list({a[0]}))"
        if a else f"{_DC}.Decimal('0')"
    ))

    api.lib_call("fraction", "as_percent", lambda a: (
        f"float({_FR}({a[0]}) * 100)"
        if a else "0.0"
    ))

    api.lib_call("fraction", "reciprocal", lambda a: (
        f"(1 / {_FR}({a[0]}))"
        if a else f"{_FR}(0)"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
