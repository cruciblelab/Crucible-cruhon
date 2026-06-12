"""
cruhon-shortcuts — math group
==============================
Shortcuts for @random.* (and @math.* where applicable).

Global aliases (source rewrites)
─────────────────────────────────
@rand[lo; hi]           → @random.randint[lo; hi]
@randf[lo; hi]          → @random.uniform[lo; hi]
@pick[seq]              → @random.choice[seq]
@picks[seq; k]          → @random.choices[seq; k]
@sample[seq; n]         → @random.sample[seq; n]
@shuffle[seq]           → @random.shuffle[seq]
@seed[n]                → @random.seed[n]
@gauss[mu; sigma]       → @random.gauss[mu; sigma]
@triangular[lo; hi; m]  → @random.triangular[lo; hi; m]
@betavariate[a; b]      → @random.betavariate[a; b]
@expovariate[lam]       → @random.expovariate[lam]
@rand_state[]           → @random.getstate[]
@set_rand_state[s]      → @random.setstate[s]

Namespace method aliases
─────────────────────────
@random.int[lo; hi]     → @random.randint[lo; hi]
@random.float[lo; hi]   → @random.uniform[lo; hi]
@random.pick[seq]       → @random.choice[seq]
@random.picks[seq; k]   → @random.choices[seq; k]
@random.seq[s; n]       → @random.sample[s; n]

New methods (via api.lib_call)
───────────────────────────────
@random.roll[sides]         → randint(1, sides) — dice roll
@random.flip[]              → random.choice([True, False])
@random.percent[]           → uniform(0.0, 100.0)
@random.sign[]              → random.choice([-1, 1])
@random.index[seq]          → random index into seq
@random.bool[]              → random True/False
@random.hex[n]              → n random hex bytes as string
@random.lower_str[n]        → random lowercase string of length n
@random.upper_str[n]        → random uppercase string of length n
@random.alphanumeric[n]     → random alphanumeric string of length n
@random.password[n]         → random password (letters + digits + symbols)
@random.weighted[items; ws] → weighted random pick
@random.normal[mu; sigma]   → gauss alias
@random.uniform_int[lo; hi] → randint alias
@random.between[lo; hi]     → randint(lo, hi) inclusive
@random.fraction[]          → random() — float in [0.0, 1.0)
@random.non_zero[]          → non-zero random float in (0.0, 1.0)
@random.range[lo; hi; step] → randrange(lo, hi, step)
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@rand[":            "@random.randint[",
    "@randf[":           "@random.uniform[",
    "@pick[":            "@random.choice[",
    "@picks[":           "@random.choices[",
    "@sample[":          "@random.sample[",
    "@shuffle[":         "@random.shuffle[",
    "@seed[":            "@random.seed[",
    "@gauss[":           "@random.gauss[",
    "@triangular[":      "@random.triangular[",
    "@betavariate[":     "@random.betavariate[",
    "@expovariate[":     "@random.expovariate[",
    "@rand_state[":      "@random.getstate[",
    "@set_rand_state[":  "@random.setstate[",
}

METHOD_ALIASES: dict[str, str] = {
    "@random.int[":    "@random.randint[",
    "@random.float[":  "@random.uniform[",
    "@random.pick[":   "@random.choice[",
    "@random.picks[":  "@random.choices[",
    "@random.seq[":    "@random.sample[",
}

_RN = "__import__('random')"
_SC = "__import__('secrets')"
_ST = "__import__('string')"


def _new_lib_calls(api) -> None:

    api.lib_call("random", "roll", lambda a: (
        f"{_RN}.randint(1, {a[0]})"
        if a else
        f"{_RN}.randint(1, 6)"
    ))

    api.lib_call("random", "flip", lambda a: (
        f"{_RN}.choice([True, False])"
    ))

    api.lib_call("random", "percent", lambda a: (
        f"{_RN}.uniform(0.0, 100.0)"
    ))

    api.lib_call("random", "sign", lambda a: (
        f"{_RN}.choice([-1, 1])"
    ))

    api.lib_call("random", "index", lambda a: (
        f"{_RN}.randrange(len({a[0]}))"
        if a else
        f"0"
    ))

    api.lib_call("random", "bool", lambda a: (
        f"{_RN}.choice([True, False])"
    ))

    api.lib_call("random", "hex", lambda a: (
        f"{_SC}.token_hex({a[0]})"
        if a else
        f"{_SC}.token_hex(16)"
    ))

    api.lib_call("random", "lower_str", lambda a: (
        f"''.join({_RN}.choices({_ST}.ascii_lowercase, k={a[0]}))"
        if a else
        f"''.join({_RN}.choices({_ST}.ascii_lowercase, k=8))"
    ))

    api.lib_call("random", "upper_str", lambda a: (
        f"''.join({_RN}.choices({_ST}.ascii_uppercase, k={a[0]}))"
        if a else
        f"''.join({_RN}.choices({_ST}.ascii_uppercase, k=8))"
    ))

    api.lib_call("random", "alphanumeric", lambda a: (
        f"''.join({_RN}.choices({_ST}.ascii_letters + {_ST}.digits, k={a[0]}))"
        if a else
        f"''.join({_RN}.choices({_ST}.ascii_letters + {_ST}.digits, k=12))"
    ))

    api.lib_call("random", "password", lambda a: (
        f"''.join({_RN}.choices({_ST}.ascii_letters + {_ST}.digits + {_ST}.punctuation, k={a[0]}))"
        if a else
        f"''.join({_RN}.choices({_ST}.ascii_letters + {_ST}.digits + {_ST}.punctuation, k=16))"
    ))

    api.lib_call("random", "weighted", lambda a: (
        f"{_RN}.choices({a[0]}, weights={a[1]}, k=1)[0]"
        if len(a) > 1 else
        f"{_RN}.choice({a[0]})"
    ))

    api.lib_call("random", "normal", lambda a: (
        f"{_RN}.gauss({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"{_RN}.gauss(0, 1)"
    ))

    api.lib_call("random", "uniform_int", lambda a: (
        f"{_RN}.randint({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"{_RN}.randint(0, 100)"
    ))

    api.lib_call("random", "between", lambda a: (
        f"{_RN}.randint({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"{_RN}.randint(0, 1)"
    ))

    api.lib_call("random", "fraction", lambda a: (
        f"{_RN}.random()"
    ))

    api.lib_call("random", "non_zero", lambda a: (
        f"(lambda: (lambda _v: _v if _v > 0 else 1e-10)({_RN}.random()))()"
    ))

    api.lib_call("random", "range", lambda a: (
        f"{_RN}.randrange({a[0]}, {a[1]}, {a[2]})"
        if len(a) > 2 else
        f"{_RN}.randrange({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"{_RN}.randrange({a[0]})"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
