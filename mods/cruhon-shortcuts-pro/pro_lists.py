"""
cruhon-shortcuts-pro — lists group
=====================================
Extends @collections.* with higher-level list/sequence operations:
sliding windows, transposition, partitioning, interleaving, and more.

Global aliases (source rewrites)
─────────────────────────────────
@window[lst; n]          → @collections.window[lst; n]
@transpose[matrix]       → @collections.transpose[matrix]
@unzip[pairs]            → @collections.unzip[pairs]
@rotate_list[lst; n]     → @collections.rotate[lst; n]
@partition_by[lst; fn]   → @collections.partition_list[lst; fn]
@head_n[lst; n]          → @collections.head_n[lst; n]
@tail_n[lst; n]          → @collections.tail_n[lst; n]
@interleave[a; b]        → @collections.interleave[a; b]
@dedupe[lst]             → @collections.dedupe[lst]
@flat[lst]               → @collections.flat[lst]
@zip_all[*lists]         → @collections.zip_all[*lists]
@cartesian[a; b]         → @collections.cartesian[a; b]
@chunks[lst; n]          → @collections.chunks[lst; n]
@sorted_by[lst; key]     → @collections.sorted_by[lst; key]
@take_while[lst; fn]     → @collections.take_while[lst; fn]
@drop_while[lst; fn]     → @collections.drop_while[lst; fn]
@pairs[lst]              → @collections.pairs[lst]
@enumerate_from[lst; n]  → @collections.enumerate_from[lst; n]
@flatten_once[lst]       → @collections.flat[lst]

Namespace method aliases
─────────────────────────
@collections.win[lst; n]   → @collections.window[lst; n]
@collections.trp[m]        → @collections.transpose[m]
@collections.unzip[pairs]  — direct method (no alias needed)
@collections.rot[lst; n]   → @collections.rotate[lst; n]
@collections.part[lst; fn] → @collections.partition_list[lst; fn]
@collections.hd[lst; n]    → @collections.head_n[lst; n]
@collections.tl[lst; n]    → @collections.tail_n[lst; n]
@collections.il[a; b]      → @collections.interleave[a; b]
@collections.uniq[lst]     → @collections.dedupe[lst]
@collections.srt[lst; key] → @collections.sorted_by[lst; key]

New methods (via api.lib_call)
───────────────────────────────
@collections.transpose[matrix]         → transpose a matrix (list of lists)
@collections.unzip[pairs]              → unzip [(a,b), ...] → ([a,...], [b,...])
@collections.rotate[lst; n]            → rotate list n steps right (negative = left)
@collections.partition_list[lst; fn]   → ([true items], [false items])
@collections.head_n[lst; n]            → first n items
@collections.tail_n[lst; n]            → last n items
@collections.interleave[a; b]          → interleave two lists element by element
@collections.dedupe[lst]               → deduplicate while preserving order
@collections.flat[lst]                 → one-level flatten (no deep recursion)
@collections.zip_all[*lists]           → zip multiple lists
@collections.cartesian[a; b]           → cartesian product as list of tuples
@collections.chunks[lst; n]            → split into chunks of size n
@collections.sorted_by[lst; key_fn]    → sorted(lst, key=key_fn)
@collections.take_while[lst; fn]       → items before first fn(x) is False
@collections.drop_while[lst; fn]       → items after first fn(x) is True
@collections.pairs[lst]                → adjacent (a, b) pairs
@collections.enumerate_from[lst; n]    → list(enumerate(lst, start=n))
@collections.sum_of[lst; key]          → sum of key(x) for all x in lst
@collections.min_by[lst; key]          → item with minimum key(x)
@collections.max_by[lst; key]          → item with maximum key(x)
@collections.avg_of[lst]               → arithmetic mean of a numeric list
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@window[":         "@collections.window[",
    "@transpose[":      "@collections.transpose[",
    "@unzip[":          "@collections.unzip[",
    "@rotate_list[":    "@collections.rotate[",
    "@partition_by[":   "@collections.partition_list[",
    "@head_n[":         "@collections.head_n[",
    "@tail_n[":         "@collections.tail_n[",
    "@interleave[":     "@collections.interleave[",
    "@dedupe[":         "@collections.dedupe[",
    "@flat[":           "@collections.flat[",
    "@zip_all[":        "@collections.zip_all[",
    "@cartesian[":      "@collections.cartesian[",
    "@chunks[":         "@collections.chunks[",
    "@sorted_by[":      "@collections.sorted_by[",
    "@take_while[":     "@collections.take_while[",
    "@drop_while[":     "@collections.drop_while[",
    "@pairs[":          "@collections.pairs[",
    "@enumerate_from[": "@collections.enumerate_from[",
    "@flatten_once[":   "@collections.flat[",
}

METHOD_ALIASES: dict[str, str] = {
    "@collections.win[":  "@collections.window[",
    "@collections.trp[":  "@collections.transpose[",
    "@collections.rot[":  "@collections.rotate[",
    "@collections.part[": "@collections.partition_list[",
    "@collections.hd[":   "@collections.head_n[",
    "@collections.tl[":   "@collections.tail_n[",
    "@collections.il[":   "@collections.interleave[",
    "@collections.uniq[": "@collections.dedupe[",
    "@collections.srt[":  "@collections.sorted_by[",
}


def _new_lib_calls(api) -> None:

    api.lib_call("collections", "transpose", lambda a: (
        f"[list(_row) for _row in zip(*{a[0]})]"
        if a else "[]"
    ))

    api.lib_call("collections", "unzip", lambda a: (
        f"(list(_x) for _x in zip(*{a[0]}))"
        if a else "([], [])"
    ))

    api.lib_call("collections", "rotate", lambda a: (
        f"(lambda _lst, _n: (_lst[-_n:] + _lst[:-_n]) if _n and _lst else list(_lst))"
        f"(list({a[0]}), int({a[1]}) % len({a[0]}) if {a[0]} else 0)"
        if len(a) > 1 else
        f"list({a[0]})" if a else "[]"
    ))

    api.lib_call("collections", "partition_list", lambda a: (
        f"(lambda _lst, _fn: "
        f"([_x for _x in _lst if _fn(_x)], [_x for _x in _lst if not _fn(_x)]))"
        f"(list({a[0]}), {a[1]})"
        if len(a) > 1 else "([], [])"
    ))

    api.lib_call("collections", "head_n", lambda a: (
        f"list({a[0]})[:int({a[1]})]"
        if len(a) > 1 else
        f"list({a[0]})[:1]" if a else "[]"
    ))

    api.lib_call("collections", "tail_n", lambda a: (
        f"list({a[0]})[-(int({a[1]})):]"
        if len(a) > 1 else
        f"list({a[0]})[-(1):]" if a else "[]"
    ))

    api.lib_call("collections", "interleave", lambda a: (
        f"[_item for _pair in zip({a[0]}, {a[1]}) for _item in _pair]"
        if len(a) > 1 else
        f"list({a[0]})" if a else "[]"
    ))

    api.lib_call("collections", "dedupe", lambda a: (
        f"list(dict.fromkeys({a[0]}))"
        if a else "[]"
    ))

    api.lib_call("collections", "flat", lambda a: (
        f"[_item for _sub in {a[0]} for _item in "
        f"(_sub if hasattr(_sub, '__iter__') and not isinstance(_sub, str) else [_sub])]"
        if a else "[]"
    ))

    api.lib_call("collections", "zip_all", lambda a: (
        f"list(zip({', '.join(a)}))"
        if a else "[]"
    ))

    api.lib_call("collections", "cartesian", lambda a: (
        f"[(x, y) for x in {a[0]} for y in {a[1]}]"
        if len(a) > 1 else
        f"[(x,) for x in {a[0]}]" if a else "[]"
    ))

    api.lib_call("collections", "chunks", lambda a: (
        f"[list({a[0]})[_i:_i + int({a[1]})] "
        f"for _i in range(0, len(list({a[0]})), int({a[1]}))]"
        if len(a) > 1 else
        f"[list({a[0]})]" if a else "[]"
    ))

    api.lib_call("collections", "sorted_by", lambda a: (
        f"sorted(list({a[0]}), key={a[1]})"
        if len(a) > 1 else
        f"sorted(list({a[0]}))" if a else "[]"
    ))

    api.lib_call("collections", "take_while", lambda a: (
        f"list(__import__('itertools').takewhile({a[1]}, {a[0]}))"
        if len(a) > 1 else
        f"list({a[0]})" if a else "[]"
    ))

    api.lib_call("collections", "drop_while", lambda a: (
        f"list(__import__('itertools').dropwhile({a[1]}, {a[0]}))"
        if len(a) > 1 else
        f"list({a[0]})" if a else "[]"
    ))

    api.lib_call("collections", "pairs", lambda a: (
        f"list(zip(list({a[0]})[:-1], list({a[0]})[1:]))"
        if a else "[]"
    ))

    api.lib_call("collections", "enumerate_from", lambda a: (
        f"list(enumerate({a[0]}, start=int({a[1]})))"
        if len(a) > 1 else
        f"list(enumerate({a[0]}))" if a else "[]"
    ))

    api.lib_call("collections", "sum_of", lambda a: (
        f"sum({a[1]}(_x) for _x in {a[0]})"
        if len(a) > 1 else
        f"sum({a[0]})" if a else "0"
    ))

    api.lib_call("collections", "min_by", lambda a: (
        f"min({a[0]}, key={a[1]})"
        if len(a) > 1 else
        f"min({a[0]})" if a else "None"
    ))

    api.lib_call("collections", "max_by", lambda a: (
        f"max({a[0]}, key={a[1]})"
        if len(a) > 1 else
        f"max({a[0]})" if a else "None"
    ))

    api.lib_call("collections", "avg_of", lambda a: (
        f"(lambda _lst: sum(_lst) / len(_lst) if _lst else 0.0)(list({a[0]}))"
        if a else "0.0"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
