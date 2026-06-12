"""
cruhon-shortcuts-pro — logic group
=====================================
Extends @collections.* with functional-style logic and search operations:
coalescing, predicate search, conditional defaults, and safe accessors.

Global aliases (source rewrites)
─────────────────────────────────
@coalesce[v1; v2; ...]     → @collections.coalesce[v1; v2; ...]
@first_true[lst]           → @collections.first_true[lst]
@count_if[lst; fn]         → @collections.count_if[lst; fn]
@any_match[lst; fn]        → @collections.any_match[lst; fn]
@all_match[lst; fn]        → @collections.all_match[lst; fn]
@none_match[lst; fn]       → @collections.none_match[lst; fn]
@first_where[lst; fn]      → @collections.first_where[lst; fn]
@last_where[lst; fn]       → @collections.last_where[lst; fn]
@default_if_none[v; d]     → @collections.default_if_none[v; d]
@safe_get[d; key; default] → @collections.safe_get[d; key; default]
@unless_empty[v; d]        → @collections.unless_empty[v; d]
@one_of[v; choices]        → @collections.one_of[v; choices]
@not_in[v; lst]            → @collections.not_in[v; lst]
@index_of[lst; v]          → @collections.index_of[lst; v]
@find_all[lst; fn]         → @collections.find_all[lst; fn]
@group_by[lst; fn]         → @collections.group_by[lst; fn]
@tally[lst]                → @collections.tally[lst]

Namespace method aliases
─────────────────────────
@collections.coal[...]        → @collections.coalesce[...]
@collections.any_of[lst; fn] → @collections.any_match[lst; fn]
@collections.all_of[lst; fn] → @collections.all_match[lst; fn]
@collections.none_of[lst;fn] → @collections.none_match[lst; fn]
@collections.find[lst; fn]   → @collections.first_where[lst; fn]
@collections.dflt[v; d]      → @collections.default_if_none[v; d]
@collections.get_or[d; k; d2]→ @collections.safe_get[d; k; d2]
@collections.grp[lst; fn]    → @collections.group_by[lst; fn]

New methods (via api.lib_call)
───────────────────────────────
@collections.coalesce[v1; v2; ...] → first non-None value
@collections.first_true[lst]       → first truthy value in list
@collections.count_if[lst; fn]     → count items where fn(item) is True
@collections.any_match[lst; fn]    → any(fn(x) for x in lst)
@collections.all_match[lst; fn]    → all(fn(x) for x in lst)
@collections.none_match[lst; fn]   → not any(fn(x) for x in lst)
@collections.first_where[lst; fn]  → first item where fn(item) is True
@collections.last_where[lst; fn]   → last item where fn(item) is True
@collections.default_if_none[v; d] → d if v is None else v
@collections.safe_get[d; k; dfl]   → d.get(k, dfl) with nested key support
@collections.unless_empty[v; d]    → d if not v else v
@collections.one_of[v; choices]    → True if v in choices
@collections.not_in[v; lst]        → True if v not in lst
@collections.index_of[lst; v]      → index of v in lst (-1 if not found)
@collections.find_all[lst; fn]     → all items matching predicate
@collections.group_by[lst; fn]     → dict grouping items by fn(item) result
@collections.tally[lst]            → {item: count} from list (like Counter)
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@coalesce[":          "@collections.coalesce[",
    "@first_true[":        "@collections.first_true[",
    "@count_if[":          "@collections.count_if[",
    "@any_match[":         "@collections.any_match[",
    "@all_match[":         "@collections.all_match[",
    "@none_match[":        "@collections.none_match[",
    "@first_where[":       "@collections.first_where[",
    "@last_where[":        "@collections.last_where[",
    "@default_if_none[":   "@collections.default_if_none[",
    "@safe_get[":          "@collections.safe_get[",
    "@unless_empty[":      "@collections.unless_empty[",
    "@one_of[":            "@collections.one_of[",
    "@not_in[":            "@collections.not_in[",
    "@index_of[":          "@collections.index_of[",
    "@find_all[":          "@collections.find_all[",
    "@group_by[":          "@collections.group_by[",
    "@tally[":             "@collections.tally[",
}

METHOD_ALIASES: dict[str, str] = {
    "@collections.coal[":     "@collections.coalesce[",
    "@collections.any_of[":   "@collections.any_match[",
    "@collections.all_of[":   "@collections.all_match[",
    "@collections.none_of[":  "@collections.none_match[",
    "@collections.find[":     "@collections.first_where[",
    "@collections.dflt[":     "@collections.default_if_none[",
    "@collections.get_or[":   "@collections.safe_get[",
    "@collections.grp[":      "@collections.group_by[",
}


def _new_lib_calls(api) -> None:

    api.lib_call("collections", "coalesce", lambda a: (
        f"next((_v for _v in [{', '.join(a)}] if _v is not None), None)"
        if a else "None"
    ))

    api.lib_call("collections", "first_true", lambda a: (
        f"next((_v for _v in {a[0]} if _v), None)"
        if a else "None"
    ))

    api.lib_call("collections", "count_if", lambda a: (
        f"sum(1 for _x in {a[0]} if {a[1]}(_x))"
        if len(a) > 1 else
        f"len(list({a[0]}))" if a else "0"
    ))

    api.lib_call("collections", "any_match", lambda a: (
        f"any({a[1]}(_x) for _x in {a[0]})"
        if len(a) > 1 else
        f"any({a[0]})" if a else "False"
    ))

    api.lib_call("collections", "all_match", lambda a: (
        f"all({a[1]}(_x) for _x in {a[0]})"
        if len(a) > 1 else
        f"all({a[0]})" if a else "True"
    ))

    api.lib_call("collections", "none_match", lambda a: (
        f"not any({a[1]}(_x) for _x in {a[0]})"
        if len(a) > 1 else
        f"not any({a[0]})" if a else "True"
    ))

    api.lib_call("collections", "first_where", lambda a: (
        f"next((_x for _x in {a[0]} if {a[1]}(_x)), None)"
        if len(a) > 1 else
        f"next(iter({a[0]}), None)" if a else "None"
    ))

    api.lib_call("collections", "last_where", lambda a: (
        f"next((_x for _x in reversed(list({a[0]})) if {a[1]}(_x)), None)"
        if len(a) > 1 else
        f"(list({a[0]}) or [None])[-1]" if a else "None"
    ))

    api.lib_call("collections", "default_if_none", lambda a: (
        f"({a[1]} if {a[0]} is None else {a[0]})"
        if len(a) > 1 else
        f"{a[0]}" if a else "None"
    ))

    api.lib_call("collections", "safe_get", lambda a: (
        f"({a[0]}.get({a[1]}, {a[2]}) if isinstance({a[0]}, dict) else {a[2]})"
        if len(a) > 2 else
        f"({a[0]}.get({a[1]}) if isinstance({a[0]}, dict) else None)"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("collections", "unless_empty", lambda a: (
        f"({a[1]} if not {a[0]} else {a[0]})"
        if len(a) > 1 else
        f"{a[0]}" if a else "None"
    ))

    api.lib_call("collections", "one_of", lambda a: (
        f"({a[0]} in {a[1]})"
        if len(a) > 1 else "False"
    ))

    api.lib_call("collections", "not_in", lambda a: (
        f"({a[0]} not in {a[1]})"
        if len(a) > 1 else "True"
    ))

    api.lib_call("collections", "index_of", lambda a: (
        f"(list({a[0]}).index({a[1]}) if {a[1]} in list({a[0]}) else -1)"
        if len(a) > 1 else "-1"
    ))

    api.lib_call("collections", "find_all", lambda a: (
        f"[_x for _x in {a[0]} if {a[1]}(_x)]"
        if len(a) > 1 else
        f"list({a[0]})" if a else "[]"
    ))

    api.lib_call("collections", "group_by", lambda a: (
        f"(lambda _lst, _fn: "
        f"(lambda _d: [_d.setdefault(_fn(_x), []).append(_x) for _x in _lst] or _d)({{}})"
        f")({a[0]}, {a[1]})"
        if len(a) > 1 else "{}"
    ))

    api.lib_call("collections", "tally", lambda a: (
        f"dict(__import__('collections').Counter({a[0]}))"
        if a else "{}"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
