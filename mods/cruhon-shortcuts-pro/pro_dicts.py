"""
cruhon-shortcuts-pro — dicts group
=====================================
Extends @collections.* with higher-level dict operations: picking,
omitting, deep merging, diffing, and key/value transformation.

Global aliases (source rewrites)
─────────────────────────────────
@pick_keys[d; keys]      → @collections.pick_keys[d; keys]
@omit_keys[d; keys]      → @collections.omit_keys[d; keys]
@map_vals[d; fn]         → @collections.map_values[d; fn]
@filter_keys[d; fn]      → @collections.filter_items[d; fn]
@deep_merge[d1; d2]      → @collections.deep_merge[d1; d2]
@dict_diff[d1; d2]       → @collections.dict_diff[d1; d2]
@flat_dict[d]            → @collections.flatten_nested[d]
@unflatten_dict[d]       → @collections.unflatten_nested[d]
@swap_kv[d]              → @collections.swap_keys_values[d]
@rename_key[d; old; new] → @collections.rename_key[d; old; new]
@default_dict[fn]        → @collections.default_factory[fn]
@dict_product[d]         → @collections.dict_product[d]
@key_of[d; v]            → @collections.key_of[d; v]
@values_where[d; fn]     → @collections.values_where[d; fn]

Namespace method aliases
─────────────────────────
@collections.pick[d; ks]     → @collections.pick_keys[d; ks]
@collections.omit[d; ks]     → @collections.omit_keys[d; ks]
@collections.mapv[d; fn]     → @collections.map_values[d; fn]
@collections.filtk[d; fn]    → @collections.filter_items[d; fn]
@collections.dmerge[d1; d2]  → @collections.deep_merge[d1; d2]
@collections.diff[d1; d2]    → @collections.dict_diff[d1; d2]
@collections.flat_keys[d]    → @collections.flatten_nested[d]
@collections.swap[d]         → @collections.swap_keys_values[d]

New methods (via api.lib_call)
───────────────────────────────
@collections.pick_keys[d; keys]      → {k: d[k] for k in keys if k in d}
@collections.omit_keys[d; keys]      → {k: v for k, v in d.items() if k not in keys}
@collections.map_values[d; fn]       → {k: fn(v) for k, v in d.items()}
@collections.filter_items[d; fn]     → {k: v for k, v in d.items() if fn(k, v)}
@collections.deep_merge[d1; d2]      → recursive merge (d2 wins on conflict)
@collections.dict_diff[d1; d2]       → keys/values that differ between two dicts
@collections.flatten_nested[d]       → flatten nested dict with "." separator
@collections.flatten_nested[d; sep]  → flatten with custom separator
@collections.unflatten_nested[d]     → rebuild nested dict from dotted keys
@collections.swap_keys_values[d]     → {v: k for k, v in d.items()}
@collections.rename_key[d; old; new] → copy dict with one key renamed
@collections.key_of[d; value]        → first key whose value matches
@collections.values_where[d; fn]     → list of values where fn(k, v) is True
@collections.dict_product[d]         → cartesian product of dict values (list of dicts)
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@pick_keys[":      "@collections.pick_keys[",
    "@omit_keys[":      "@collections.omit_keys[",
    "@map_vals[":       "@collections.map_values[",
    "@filter_keys[":    "@collections.filter_items[",
    "@deep_merge[":     "@collections.deep_merge[",
    "@dict_diff[":      "@collections.dict_diff[",
    "@flat_dict[":      "@collections.flatten_nested[",
    "@unflatten_dict[": "@collections.unflatten_nested[",
    "@swap_kv[":        "@collections.swap_keys_values[",
    "@rename_key[":     "@collections.rename_key[",
    "@key_of[":         "@collections.key_of[",
    "@values_where[":   "@collections.values_where[",
    "@dict_product[":   "@collections.dict_product[",
}

METHOD_ALIASES: dict[str, str] = {
    "@collections.pick[":     "@collections.pick_keys[",
    "@collections.omit[":     "@collections.omit_keys[",
    "@collections.mapv[":     "@collections.map_values[",
    "@collections.filtk[":    "@collections.filter_items[",
    "@collections.dmerge[":   "@collections.deep_merge[",
    "@collections.diff[":     "@collections.dict_diff[",
    "@collections.flat_keys[":"@collections.flatten_nested[",
    "@collections.swap[":     "@collections.swap_keys_values[",
}


def _new_lib_calls(api) -> None:

    api.lib_call("collections", "pick_keys", lambda a: (
        f"{{_k: {a[0]}[_k] for _k in {a[1]} if _k in {a[0]}}}"
        if len(a) > 1 else f"dict({a[0]})" if a else "{}"
    ))

    api.lib_call("collections", "omit_keys", lambda a: (
        f"{{_k: _v for _k, _v in {a[0]}.items() if _k not in {a[1]}}}"
        if len(a) > 1 else f"dict({a[0]})" if a else "{}"
    ))

    api.lib_call("collections", "map_values", lambda a: (
        f"{{_k: {a[1]}(_v) for _k, _v in {a[0]}.items()}}"
        if len(a) > 1 else f"dict({a[0]})" if a else "{}"
    ))

    api.lib_call("collections", "filter_items", lambda a: (
        f"{{_k: _v for _k, _v in {a[0]}.items() if {a[1]}(_k, _v)}}"
        if len(a) > 1 else f"dict({a[0]})" if a else "{}"
    ))

    api.lib_call("collections", "deep_merge", lambda a: (
        f"(lambda _a, _b: (lambda _m: [_m.update({{_k: "
        f"(lambda _av, _bv: __import__('collections').ChainMap(_bv, _av) "
        f"if isinstance(_av, dict) and isinstance(_bv, dict) else _bv)"
        f"(_m.get(_k), _bv) for _k, _bv in _b.items()}}) or _m)(dict(_a)))"
        f"({a[0]}, {a[1]})"
        if len(a) > 1 else f"dict({a[0]})" if a else "{}"
    ))

    api.lib_call("collections", "dict_diff", lambda a: (
        f"{{_k: ({a[0]}.get(_k), {a[1]}.get(_k)) "
        f"for _k in set({a[0]}) | set({a[1]}) "
        f"if {a[0]}.get(_k) != {a[1]}.get(_k)}}"
        if len(a) > 1 else "{}"
    ))

    api.lib_call("collections", "flatten_nested", lambda a: (
        f"(lambda _d, _sep='.': "
        f"(lambda _fn: _fn(_fn, _d, ''))(_fn := "
        f"(lambda _fn, _d, _prefix: "
        f"{{**(_fn(_fn, _v, (_prefix + _sep + str(_k)) if _prefix else str(_k)) "
        f"if isinstance(_v, dict) else {{(_prefix + _sep + str(_k)) if _prefix else str(_k): _v}} "
        f"for _k, _v in _d.items())}}"
        f")))({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"(lambda _d: (lambda _fn: _fn(_fn, _d, ''))("
        f"lambda _fn, _d, _prefix: "
        f"{{**(_fn(_fn, _v, (_prefix + '.' + str(_k)) if _prefix else str(_k)) "
        f"if isinstance(_v, dict) else {{(_prefix + '.' + str(_k)) if _prefix else str(_k): _v}} "
        f"for _k, _v in _d.items())}}"
        f"))({a[0]})"
        if a else "{}"
    ))

    api.lib_call("collections", "unflatten_nested", lambda a: (
        f"(lambda _d, _sep='.': "
        f"(lambda _out: [(_out.setdefault(_parts[0], {{}}), "
        f"_out[_parts[0]].update({{_parts[-1]: _v}}) "
        f"if len(_parts) == 2 else None) "
        f"for _k, _v in _d.items() for _parts in [_k.split(_sep)]] or _out)({{}})"
        f")({a[0]})"
        if a else "{}"
    ))

    api.lib_call("collections", "swap_keys_values", lambda a: (
        f"{{_v: _k for _k, _v in {a[0]}.items()}}"
        if a else "{}"
    ))

    api.lib_call("collections", "rename_key", lambda a: (
        f"(lambda _d, _o, _n: {{_n if _k == _o else _k: _v for _k, _v in _d.items()}})"
        f"({a[0]}, {a[1]}, {a[2]})"
        if len(a) > 2 else f"dict({a[0]})" if a else "{}"
    ))

    api.lib_call("collections", "key_of", lambda a: (
        f"next((_k for _k, _v in {a[0]}.items() if _v == {a[1]}), None)"
        if len(a) > 1 else "None"
    ))

    api.lib_call("collections", "values_where", lambda a: (
        f"[_v for _k, _v in {a[0]}.items() if {a[1]}(_k, _v)]"
        if len(a) > 1 else f"list({a[0]}.values())" if a else "[]"
    ))

    api.lib_call("collections", "dict_product", lambda a: (
        f"(lambda _d: [dict(zip(_d.keys(), _combo)) "
        f"for _combo in __import__('itertools').product(*_d.values())])({a[0]})"
        if a else "[]"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
