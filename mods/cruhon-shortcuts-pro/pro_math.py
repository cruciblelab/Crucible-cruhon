"""
cruhon-shortcuts-pro — math group
====================================
Extends @math.* with higher-level operations: clamping, interpolation,
trigonometry, number theory, and float utilities.

Global aliases (source rewrites)
─────────────────────────────────
@clamp[x; lo; hi]       → @math.clamp[x; lo; hi]
@lerp[a; b; t]          → @math.lerp[a; b; t]
@sign[x]                → @math.sign[x]
@round_to[x; digits]    → @math.round_to[x; digits]
@percent[part; total]   → @math.percent[part; total]
@frange[start;stop;step]→ @math.frange[start; stop; step]
@log2[x]                → @math.log2[x]
@log10[x]               → @math.log10[x]
@is_close[a; b]         → @math.is_close[a; b]
@factorial[n]           → @math.factorial[n]
@gcd[a; b]              → @math.gcd[a; b]
@lcm[a; b]              → @math.lcm[a; b]
@hypot[x; y]            → @math.hypot[x; y]
@degrees[r]             → @math.degrees[r]
@radians[d]             → @math.radians[d]
@sin[x]                 → @math.sin[x]
@cos[x]                 → @math.cos[x]
@tan[x]                 → @math.tan[x]

Namespace method aliases
─────────────────────────
@math.clamp[x; lo; hi]  — shorthand already in GLOBAL_REWRITES
@math.pct[part; total]  → @math.percent[part; total]
@math.interp[a; b; t]   → @math.lerp[a; b; t]
@math.l2[x]             → @math.log2[x]
@math.l10[x]            → @math.log10[x]
@math.fact[n]           → @math.factorial[n]

New methods (via api.lib_call)
───────────────────────────────
@math.clamp[x; lo; hi]     → max(lo, min(hi, x))
@math.lerp[a; b; t]        → a + (b - a) * t
@math.sign[x]              → -1 / 0 / 1
@math.round_to[x; n]       → round(x, n)
@math.percent[part; total] → (part / total * 100) if total else 0
@math.ratio[a; b]          → a / b if b else 0
@math.frange[s; e; step]   → list of floats from start to end by step
@math.log2[x]              → math.log2(x)
@math.log10[x]             → math.log10(x)
@math.is_close[a; b]       → math.isclose(a, b)
@math.factorial[n]         → math.factorial(n)
@math.gcd[a; b]            → math.gcd(a, b)
@math.lcm[a; b]            → math.lcm(a, b)
@math.hypot[x; y]          → math.hypot(x, y)
@math.degrees[r]           → math.degrees(r)
@math.radians[d]           → math.radians(d)
@math.sin[x]               → math.sin(x)
@math.cos[x]               → math.cos(x)
@math.tan[x]               → math.tan(x)
@math.inf[]                → math.inf
@math.nan[]                → math.nan
@math.tau[]                → math.tau
@math.e[]                  → math.e
@math.is_nan[x]            → math.isnan(x)
@math.is_inf[x]            → math.isinf(x)
@math.is_finite[x]         → math.isfinite(x)
@math.trunc[x]             → math.trunc(x)
@math.fmod[x; y]           → math.fmod(x, y)
@math.copysign[x; y]       → math.copysign(x, y)
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@clamp[":      "@math.clamp[",
    "@lerp[":       "@math.lerp[",
    "@sign[":       "@math.sign[",
    "@round_to[":   "@math.round_to[",
    "@percent[":    "@math.percent[",
    "@frange[":     "@math.frange[",
    "@log2[":       "@math.log2[",
    "@log10[":      "@math.log10[",
    "@is_close[":   "@math.is_close[",
    "@factorial[":  "@math.factorial[",
    "@gcd[":        "@math.gcd[",
    "@lcm[":        "@math.lcm[",
    "@hypot[":      "@math.hypot[",
    "@degrees[":    "@math.degrees[",
    "@radians[":    "@math.radians[",
    "@sin[":        "@math.sin[",
    "@cos[":        "@math.cos[",
    "@tan[":        "@math.tan[",
}

METHOD_ALIASES: dict[str, str] = {
    "@math.pct[":    "@math.percent[",
    "@math.interp[": "@math.lerp[",
    "@math.l2[":     "@math.log2[",
    "@math.l10[":    "@math.log10[",
    "@math.fact[":   "@math.factorial[",
}

_M = "__import__('math')"


def _new_lib_calls(api) -> None:

    api.lib_call("math", "clamp", lambda a: (
        f"max({a[1]}, min({a[2]}, {a[0]}))"
        if len(a) > 2 else
        f"float({a[0]})" if a else "0"
    ))

    api.lib_call("math", "lerp", lambda a: (
        f"({a[0]} + ({a[1]} - {a[0]}) * {a[2]})"
        if len(a) > 2 else
        f"float({a[0]})" if a else "0.0"
    ))

    api.lib_call("math", "sign", lambda a: (
        f"(1 if {a[0]} > 0 else (-1 if {a[0]} < 0 else 0))"
        if a else "0"
    ))

    api.lib_call("math", "round_to", lambda a: (
        f"round(float({a[0]}), int({a[1]}))"
        if len(a) > 1 else
        f"round(float({a[0]}))" if a else "0"
    ))

    api.lib_call("math", "percent", lambda a: (
        f"(float({a[0]}) / float({a[1]}) * 100 if {a[1]} else 0.0)"
        if len(a) > 1 else "0.0"
    ))

    api.lib_call("math", "ratio", lambda a: (
        f"(float({a[0]}) / float({a[1]}) if {a[1]} else 0.0)"
        if len(a) > 1 else "0.0"
    ))

    api.lib_call("math", "frange", lambda a: (
        f"[{a[0]} + _i * {a[2]} for _i in range(int(({a[1]} - {a[0]}) / {a[2]}))]"
        if len(a) > 2 else
        f"list(range(int({a[0]}), int({a[1]})))" if len(a) > 1 else
        f"[]"
    ))

    api.lib_call("math", "log2",
        lambda a: f"{_M}.log2(float({a[0]}))" if a else "0.0")

    api.lib_call("math", "log10",
        lambda a: f"{_M}.log10(float({a[0]}))" if a else "0.0")

    api.lib_call("math", "is_close", lambda a: (
        f"{_M}.isclose(float({a[0]}), float({a[1]}))"
        if len(a) > 1 else "False"
    ))

    api.lib_call("math", "factorial",
        lambda a: f"{_M}.factorial(int({a[0]}))" if a else "1")

    api.lib_call("math", "gcd", lambda a: (
        f"{_M}.gcd(int({a[0]}), int({a[1]}))"
        if len(a) > 1 else "0"
    ))

    api.lib_call("math", "lcm", lambda a: (
        f"{_M}.lcm(int({a[0]}), int({a[1]}))"
        if len(a) > 1 else "0"
    ))

    api.lib_call("math", "hypot", lambda a: (
        f"{_M}.hypot({', '.join(a)})"
        if a else "0.0"
    ))

    api.lib_call("math", "degrees",
        lambda a: f"{_M}.degrees(float({a[0]}))" if a else "0.0")

    api.lib_call("math", "radians",
        lambda a: f"{_M}.radians(float({a[0]}))" if a else "0.0")

    api.lib_call("math", "sin",
        lambda a: f"{_M}.sin(float({a[0]}))" if a else "0.0")

    api.lib_call("math", "cos",
        lambda a: f"{_M}.cos(float({a[0]}))" if a else "1.0")

    api.lib_call("math", "tan",
        lambda a: f"{_M}.tan(float({a[0]}))" if a else "0.0")

    api.lib_call("math", "inf",
        lambda a: f"{_M}.inf")

    api.lib_call("math", "nan",
        lambda a: f"{_M}.nan")

    api.lib_call("math", "tau",
        lambda a: f"{_M}.tau")

    api.lib_call("math", "e",
        lambda a: f"{_M}.e")

    api.lib_call("math", "is_nan",
        lambda a: f"{_M}.isnan(float({a[0]}))" if a else "False")

    api.lib_call("math", "is_inf",
        lambda a: f"{_M}.isinf(float({a[0]}))" if a else "False")

    api.lib_call("math", "is_finite",
        lambda a: f"{_M}.isfinite(float({a[0]}))" if a else "True")

    api.lib_call("math", "trunc",
        lambda a: f"{_M}.trunc(float({a[0]}))" if a else "0")

    api.lib_call("math", "fmod", lambda a: (
        f"{_M}.fmod(float({a[0]}), float({a[1]}))"
        if len(a) > 1 else "0.0"
    ))

    api.lib_call("math", "copysign", lambda a: (
        f"{_M}.copysign(float({a[0]}), float({a[1]}))"
        if len(a) > 1 else f"float({a[0]})" if a else "0.0"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
