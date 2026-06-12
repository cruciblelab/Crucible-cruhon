"""
cruhon-shortcuts — stdlib group
=================================
Shortcuts for the Python stdlib wrappers:
  @itertools.*  @functools.*  @statistics.*  @io.*  @copy.*
  @url.*  @contextlib.*  @threading.*  @queue.*
  @heapq.*  @bisect.*  @operator.*  @pprint.*

Global aliases (source rewrites)
─────────────────────────────────

itertools:
@chain[a; b]            → @itertools.chain[a; b]
@flatten[it]            → @itertools.flatten[it]
@cycle[it]              → @itertools.cycle[it]
@repeat[x; n]           → @itertools.repeat[x; n]
@count_from[n]          → @itertools.count[n]
@product[a; b]          → @itertools.product[a; b]
@permutations[it; n]    → @itertools.permutations[it; n]
@combinations[it; n]    → @itertools.combinations[it; n]
@combos_wr[it; n]       → @itertools.combinations_with_replacement[it; n]
@zip_long[a; b]         → @itertools.zip_longest[a; b]
@groupby[it; key]       → @itertools.groupby[it; key]
@accumulate[it]         → @itertools.accumulate[it]
@takewhile[fn; it]      → @itertools.takewhile[fn; it]
@dropwhile[fn; it]      → @itertools.dropwhile[fn; it]
@islice[it; n]          → @itertools.islice[it; n]
@starmap[fn; it]        → @itertools.starmap[fn; it]
@pairwise[it]           → @itertools.pairwise[it]
@tee[it; n]             → @itertools.tee[it; n]

functools:
@reduce[fn; it]         → @functools.reduce[fn; it]
@partial[fn; ...]       → @functools.partial[fn; ...]
@lru_cache[fn]          → @functools.lru_cache[fn]
@memoize[fn]            → @functools.cache[fn]
@total_ordering[cls]    → @functools.total_ordering[cls]
@singledispatch[fn]     → @functools.singledispatch[fn]

statistics:
@mean[data]             → @statistics.mean[data]
@fmean[data]            → @statistics.fmean[data]
@median[data]           → @statistics.median[data]
@mode[data]             → @statistics.mode[data]
@stdev[data]            → @statistics.stdev[data]
@variance[data]         → @statistics.variance[data]
@pstdev[data]           → @statistics.pstdev[data]
@pvariance[data]        → @statistics.pvariance[data]
@quantiles[data]        → @statistics.quantiles[data]
@correlation[x; y]      → @statistics.correlation[x; y]
@covariance[x; y]       → @statistics.covariance[x; y]
@geo_mean[data]         → @statistics.geometric_mean[data]
@harmonic_mean[data]    → @statistics.harmonic_mean[data]
@linear_reg[x; y]       → @statistics.linear_regression[x; y]

io:
@string_io[s]           → @io.StringIO[s]
@bytes_io[b]            → @io.BytesIO[b]

copy:
@shallow_copy[obj]      → @copy.copy[obj]
@deep_copy[obj]         → @copy.deepcopy[obj]

url:
@url_parse[url]         → @url.parse[url]
@url_join[base; path]   → @url.join[base; path]
@url_quote[s]           → @url.quote[s]
@url_unquote[s]         → @url.unquote[s]
@url_encode[params]     → @url.encode[params]
@url_decode[qs]         → @url.parse_qs[qs]
@url_build[...]         → @url.build[...]

Namespace method aliases
─────────────────────────
@itertools.flat[it]     → @itertools.flatten[it]
@itertools.take[it; n]  → @itertools.islice[it; n]
@itertools.pairs[it]    → @itertools.pairwise[it]
@itertools.window2[it]  → @itertools.pairwise[it]
@functools.memo[fn]     → @functools.lru_cache[fn]
@functools.call[fn; a]  → @functools.partial[fn; a]
@statistics.avg[d]      → @statistics.mean[d]
@statistics.sd[d]       → @statistics.stdev[d]
@statistics.var[d]      → @statistics.variance[d]
@io.sio[s]              → @io.StringIO[s]
@io.bio[b]              → @io.BytesIO[b]
@copy.clone[obj]        → @copy.deepcopy[obj]
@url.join_path[b; p]    → @url.join[b; p]
@heapq.push[h; x]       → @heapq.heappush[h; x]
@heapq.pop[h]           → @heapq.heappop[h]
@heapq.min[h]           → @heapq.heappop[h]
@heapq.build[it]        → @heapq.heapify[it]
@heapq.top_n[it; n]     → @heapq.nlargest[n; it]
@heapq.bot_n[it; n]     → @heapq.nsmallest[n; it]
@bisect.find[a; x]      → @bisect.bisect_left[a; x]
@bisect.insert[a; x]    → @bisect.insort[a; x]
@operator.get[obj; k]   → @operator.itemgetter[k]
@operator.attr[obj; a]  → @operator.attrgetter[a]

New methods (via api.lib_call)
───────────────────────────────
@itertools.chunk[it; n]         → split iterable into chunks of n
@itertools.unique[it]           → deduplicate while preserving order
@itertools.flatten_deep[nested] → recursively flatten nested lists
@itertools.zip_dicts[*dicts]    → zip dict values by shared keys
@statistics.summary[data]       → dict with mean/median/stdev/min/max
@statistics.normalize[data]     → normalize to [0, 1]
@statistics.zscore[data]        → z-scores list
@functools.compose[f; g]        → compose two functions f(g(x))
@functools.flip[fn]             → flip argument order
@heapq.peek[h]                  → view top without removing
@pprint.to_str[obj]             → pprint.pformat as string
@pprint.sorted_str[obj]         → pformat with sorted dicts
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    # itertools
    "@chain[":               "@itertools.chain[",
    "@flatten[":             "@itertools.flatten[",
    "@cycle[":               "@itertools.cycle[",
    # @repeat is a core Cruhon loop command — do not rewrite
    "@iter_repeat[":         "@itertools.repeat[",
    "@count_from[":          "@itertools.count[",
    "@product[":             "@itertools.product[",
    "@permutations[":        "@itertools.permutations[",
    "@combinations[":        "@itertools.combinations[",
    "@combos_wr[":           "@itertools.combinations_with_replacement[",
    "@zip_long[":            "@itertools.zip_longest[",
    "@groupby[":             "@itertools.groupby[",
    "@accumulate[":          "@itertools.accumulate[",
    "@takewhile[":           "@itertools.takewhile[",
    "@dropwhile[":           "@itertools.dropwhile[",
    "@islice[":              "@itertools.islice[",
    "@starmap[":             "@itertools.starmap[",
    "@pairwise[":            "@itertools.pairwise[",
    "@tee[":                 "@itertools.tee[",
    # functools
    "@reduce[":              "@functools.reduce[",
    "@partial[":             "@functools.partial[",
    "@lru_cache[":           "@functools.lru_cache[",
    "@memoize[":             "@functools.cache[",
    "@total_ordering[":      "@functools.total_ordering[",
    "@singledispatch[":      "@functools.singledispatch[",
    # statistics
    "@mean[":                "@statistics.mean[",
    "@fmean[":               "@statistics.fmean[",
    "@median[":              "@statistics.median[",
    "@mode[":                "@statistics.mode[",
    "@stdev[":               "@statistics.stdev[",
    "@variance[":            "@statistics.variance[",
    "@pstdev[":              "@statistics.pstdev[",
    "@pvariance[":           "@statistics.pvariance[",
    "@quantiles[":           "@statistics.quantiles[",
    "@correlation[":         "@statistics.correlation[",
    "@covariance[":          "@statistics.covariance[",
    "@geo_mean[":            "@statistics.geometric_mean[",
    "@harmonic_mean[":       "@statistics.harmonic_mean[",
    "@linear_reg[":          "@statistics.linear_regression[",
    # io
    "@string_io[":           "@io.StringIO[",
    "@bytes_io[":            "@io.BytesIO[",
    # copy
    "@shallow_copy[":        "@copy.copy[",
    "@deep_copy[":           "@copy.deepcopy[",
    # url
    "@url_parse[":           "@url.parse[",
    "@url_join[":            "@url.join[",
    "@url_quote[":           "@url.quote[",
    "@url_unquote[":         "@url.unquote[",
    "@url_encode[":          "@url.encode[",
    "@url_decode[":          "@url.parse_qs[",
    "@url_build[":           "@url.build[",
}

METHOD_ALIASES: dict[str, str] = {
    "@itertools.flat[":    "@itertools.flatten[",
    "@itertools.take[":    "@itertools.islice[",
    "@itertools.pairs[":   "@itertools.pairwise[",
    "@itertools.window2[": "@itertools.pairwise[",
    "@functools.memo[":    "@functools.lru_cache[",
    "@functools.call[":    "@functools.partial[",
    "@statistics.avg[":    "@statistics.mean[",
    "@statistics.sd[":     "@statistics.stdev[",
    "@statistics.var[":    "@statistics.variance[",
    "@io.sio[":            "@io.StringIO[",
    "@io.bio[":            "@io.BytesIO[",
    "@copy.clone[":        "@copy.deepcopy[",
    "@url.join_path[":     "@url.join[",
    "@heapq.push[":        "@heapq.heappush[",
    "@heapq.pop[":         "@heapq.heappop[",
    "@heapq.min[":         "@heapq.heappop[",
    "@heapq.build[":       "@heapq.heapify[",
    "@heapq.top_n[":       "@heapq.nlargest[",
    "@heapq.bot_n[":       "@heapq.nsmallest[",
    "@bisect.find[":       "@bisect.bisect_left[",
    "@bisect.insert[":     "@bisect.insort[",
}

_IT  = "__import__('itertools')"
_FN  = "__import__('functools')"
_ST  = "__import__('statistics')"
_HQ  = "__import__('heapq')"
_PP  = "__import__('pprint')"


def _new_lib_calls(api) -> None:

    api.lib_call("itertools", "chunk", lambda a: (
        f"[list({a[0]}[_i:_i + int({a[1]})]) "
        f"for _i in range(0, len({a[0]}), int({a[1]})) ]"
        if len(a) > 1 else
        f"[list({a[0]})]"
    ))

    api.lib_call("itertools", "unique", lambda a: (
        f"list(dict.fromkeys({a[0]}))"
        if a else
        f"[]"
    ))

    api.lib_call("itertools", "flatten_deep", lambda a: (
        f"(lambda _f, _it: list(_f(_f, _it)))"
        f"(lambda _f, _x: "
        f"(item for sub in _x for item in "
        f"(_f(_f, sub) if hasattr(sub, '__iter__') and not isinstance(sub, str) "
        f"else [sub])), {a[0]})"
        if a else
        f"[]"
    ))

    api.lib_call("itertools", "zip_dicts", lambda a: (
        f"{{_k: [_d[_k] for _d in [{', '.join(a)}] if _k in _d] "
        f"for _k in set().union(*[_d.keys() for _d in [{', '.join(a)}]])}}"
        if a else
        f"{{}}"
    ))

    api.lib_call("statistics", "summary", lambda a: (
        f"(lambda _d: {{'mean': {_ST}.mean(_d), 'median': {_ST}.median(_d), "
        f"'stdev': {_ST}.stdev(_d) if len(_d) > 1 else 0, "
        f"'min': min(_d), 'max': max(_d), 'count': len(_d)}})({a[0]})"
        if a else
        f"{{}}"
    ))

    api.lib_call("statistics", "normalize", lambda a: (
        f"(lambda _d: (lambda _mn, _mx: "
        f"[(_x - _mn) / (_mx - _mn) if _mx != _mn else 0.0 for _x in _d])"
        f"(min(_d), max(_d)))({a[0]})"
        if a else
        f"[]"
    ))

    api.lib_call("statistics", "zscore", lambda a: (
        f"(lambda _d: (lambda _m, _s: "
        f"[(_x - _m) / _s if _s > 0 else 0.0 for _x in _d])"
        f"({_ST}.mean(_d), {_ST}.stdev(_d) if len(_d) > 1 else 1))({a[0]})"
        if a else
        f"[]"
    ))

    api.lib_call("functools", "compose", lambda a: (
        f"(lambda _f, _g: lambda *_args, **_kw: _f(_g(*_args, **_kw)))({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"{a[0]}"
    ))

    api.lib_call("functools", "flip", lambda a: (
        f"(lambda _fn: lambda *_a, **_kw: _fn(*reversed(_a), **_kw))({a[0]})"
        if a else
        f"(lambda *_a: _a)"
    ))

    api.lib_call("heapq", "peek", lambda a: (
        f"({a[0]}[0] if {a[0]} else None)"
        if a else
        f"None"
    ))

    api.lib_call("pprint", "to_str", lambda a: (
        f"{_PP}.pformat({a[0]})"
        if a else
        f"''"
    ))

    api.lib_call("pprint", "sorted_str", lambda a: (
        f"{_PP}.pformat({a[0]}, sort_dicts=True)"
        if a else
        f"''"
    ))

    api.lib_call("operator", "get", lambda a: (
        f"__import__('operator').itemgetter({a[1]})({a[0]})"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("operator", "attr", lambda a: (
        f"__import__('operator').attrgetter({a[1]})({a[0]})"
        if len(a) > 1 else
        f"None"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
