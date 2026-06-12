"""
cruhon-shortcuts — collections group
======================================
Shortcuts for @collections.* operations.

Global aliases (source rewrites)
─────────────────────────────────
@counter[iterable]      → @collections.Counter[iterable]
@deque[iterable]        → @collections.deque[iterable]
@odict[]                → @collections.OrderedDict[]
@defaultdict[factory]   → @collections.defaultdict[factory]
@namedtuple[name; flds] → @collections.namedtuple[name; flds]
@chainmap[*maps]        → @collections.ChainMap[*maps]
@userdict[data]         → @collections.UserDict[data]
@userlist[data]         → @collections.UserList[data]

Namespace method aliases
─────────────────────────
@collections.count[it]  → @collections.Counter[it]
@collections.queue[it]  → @collections.deque[it]
@collections.stack[it]  → @collections.deque[it]
@collections.od[]       → @collections.OrderedDict[]
@collections.dd[f]      → @collections.defaultdict[f]
@collections.nt[n; f]   → @collections.namedtuple[n; f]
@collections.cm[*maps]  → @collections.ChainMap[*maps]

New methods (via api.lib_call)
───────────────────────────────
@collections.most_common[it; n]   → top-N most common elements
@collections.least_common[it; n]  → bottom-N least common elements
@collections.count_unique[it]     → number of unique elements
@collections.top[it]              → single most common element
@collections.histogram[it]        → Counter as sorted list of (elem, count) pairs
@collections.deque_rotate[d; n]   → rotate deque by n steps (returns new deque)
@collections.deque_left[d]        → pop left and return element
@collections.deque_right[d]       → pop right and return element
@collections.window[it; n]        → sliding window of size n (list of tuples)
@collections.group_by_count[it]   → dict: element → count (same as Counter)
@collections.freq_table[it]       → sorted list of (value, percent) tuples
@collections.flatten_dict[d; sep] → flatten nested dict with separator
@collections.merge_dicts[*dicts]  → merge multiple dicts (last wins)
@collections.dict_filter[d; fn]   → dict where fn(k, v) is True
@collections.dict_map[d; fn]      → dict with values transformed by fn(v)
@collections.invert_dict[d]       → swap keys and values
@collections.zip_to_dict[ks; vs]  → dict(zip(keys, values))
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@counter[":     "@collections.Counter[",
    "@deque[":       "@collections.deque[",
    "@odict[":       "@collections.OrderedDict[",
    "@defaultdict[": "@collections.defaultdict[",
    "@namedtuple[":  "@collections.namedtuple[",
    "@chainmap[":    "@collections.ChainMap[",
    "@userdict[":    "@collections.UserDict[",
    "@userlist[":    "@collections.UserList[",
}

METHOD_ALIASES: dict[str, str] = {
    "@collections.count[": "@collections.Counter[",
    "@collections.queue[": "@collections.deque[",
    "@collections.stack[": "@collections.deque[",
    "@collections.od[":    "@collections.OrderedDict[",
    "@collections.dd[":    "@collections.defaultdict[",
    "@collections.nt[":    "@collections.namedtuple[",
    "@collections.cm[":    "@collections.ChainMap[",
}

_CO  = "__import__('collections')"


def _new_lib_calls(api) -> None:

    api.lib_call("collections", "most_common", lambda a: (
        f"{_CO}.Counter({a[0]}).most_common({a[1]})"
        if len(a) > 1 else
        f"{_CO}.Counter({a[0]}).most_common()"
    ))

    api.lib_call("collections", "least_common", lambda a: (
        f"list(reversed({_CO}.Counter({a[0]}).most_common()))[:int({a[1]})]"
        if len(a) > 1 else
        f"list(reversed({_CO}.Counter({a[0]}).most_common()))"
    ))

    api.lib_call("collections", "count_unique", lambda a: (
        f"len(set({a[0]}))"
        if a else
        f"0"
    ))

    api.lib_call("collections", "top", lambda a: (
        f"({_CO}.Counter({a[0]}).most_common(1) or [None])[0][0]"
        if a else
        f"None"
    ))

    api.lib_call("collections", "histogram", lambda a: (
        f"sorted({_CO}.Counter({a[0]}).items(), key=lambda _x: -_x[1])"
        if a else
        f"[]"
    ))

    api.lib_call("collections", "deque_rotate", lambda a: (
        f"(lambda _d, _n: (_d.rotate(_n), _d)[1])"
        f"({_CO}.deque({a[0]}), {a[1]})"
        if len(a) > 1 else
        f"{_CO}.deque({a[0]})"
    ))

    api.lib_call("collections", "deque_left", lambda a: (
        f"{a[0]}.popleft()"
        if a else
        f"None"
    ))

    api.lib_call("collections", "deque_right", lambda a: (
        f"{a[0]}.pop()"
        if a else
        f"None"
    ))

    api.lib_call("collections", "window", lambda a: (
        f"[tuple({a[0]}[_i:_i + int({a[1]})]) "
        f"for _i in range(len({a[0]}) - int({a[1]}) + 1)]"
        if len(a) > 1 else
        f"[tuple({a[0]})]"
    ))

    api.lib_call("collections", "group_by_count", lambda a: (
        f"dict({_CO}.Counter({a[0]}))"
        if a else
        f"{{}}"
    ))

    api.lib_call("collections", "freq_table", lambda a: (
        f"(lambda _c, _tot: [(v, round(cnt / _tot * 100, 2)) for v, cnt in "
        f"sorted(_c.items(), key=lambda _x: -_x[1])])"
        f"({_CO}.Counter({a[0]}), max(1, sum({_CO}.Counter({a[0]}).values())))"
        if a else
        f"[]"
    ))

    api.lib_call("collections", "flatten_dict", lambda a: (
        f"(lambda _d, _sep: "
        f"(lambda _f: {{_k: _v for _k, _v in _f(_d, '')}})"
        f"(lambda _d, _p: "
        f"{{(_p + _sep + str(_k)).lstrip(_sep): _v "
        f"for _k, _vv in _d.items() "
        f"for _k2, _v in (_f(_vv, _p + _sep + str(_k)) "
        f"if isinstance(_vv, dict) else {{_k: _vv}}).items() "
        f"for _k in [_k2]}}))"
        f"({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"(lambda _d: "
        f"(lambda _f: dict(_f(_d, [])))"
        f"(lambda _d, _p: "
        f"sum((_f(_v, _p + [str(_k)]) if isinstance(_v, dict) "
        f"else [('.'.join(_p + [str(_k)]), _v)] "
        f"for _k, _v in _d.items()), [])))"
        f"({a[0]})"
    ))

    api.lib_call("collections", "merge_dicts", lambda a: (
        f"{{**{a[0]}, **{a[1]}}}"
        if len(a) == 2 else
        f"(lambda *_ds: {{k: v for _d in _ds for k, v in _d.items()}})"
        f"({', '.join(a)})"
        if a else
        f"{{}}"
    ))

    api.lib_call("collections", "dict_filter", lambda a: (
        f"{{_k: _v for _k, _v in {a[0]}.items() if {a[1]}(_k, _v)}}"
        if len(a) > 1 else
        f"dict({a[0]})"
    ))

    api.lib_call("collections", "dict_map", lambda a: (
        f"{{_k: {a[1]}(_v) for _k, _v in {a[0]}.items()}}"
        if len(a) > 1 else
        f"dict({a[0]})"
    ))

    api.lib_call("collections", "invert_dict", lambda a: (
        f"{{_v: _k for _k, _v in {a[0]}.items()}}"
        if a else
        f"{{}}"
    ))

    api.lib_call("collections", "zip_to_dict", lambda a: (
        f"dict(zip({a[0]}, {a[1]}))"
        if len(a) > 1 else
        f"{{}}"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
