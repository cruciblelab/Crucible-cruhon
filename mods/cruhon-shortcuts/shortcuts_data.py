"""
cruhon-shortcuts — data group
==============================
Shortcuts for @json.*, @csv.*, @store.*, @ctx.*, @log.*, and @config.*.

Global aliases (source rewrites)
─────────────────────────────────
@jload[path]            → @json.load[path]
@jdump[path; obj]       → @json.dump[path; obj]
@json_loads[s]          → @json.load[s]   (treated as string)
@json_dumps[obj]        → @json.dump[obj]
@csv_read[path]         → @csv.read[path]
@csv_write[path; rows]  → @csv.write[path; rows]
@csv_filter[path; fn]   → @csv.filter[path; fn]
@csv_to_json[path]      → @csv.to_json[path]
@store_set[k; v]        → @store.set[k; v]
@store_get[k]           → @store.get[k]
@store_clear[]          → @store.clear[]
@ctx_set[k; v]          → @ctx.set[k; v]
@ctx_get[k]             → @ctx.get[k]
@ctx_push[k; v]         → @ctx.push[k; v]
@ctx_pop[k]             → @ctx.pop[k]
@log_info[msg]          → @log.info[msg]
@log_debug[msg]         → @log.debug[msg]
@log_warn[msg]          → @log.warning[msg]
@log_error[msg]         → @log.error[msg]
@config_load[path]      → @config.load[path]
@config_get[k]          → @config.get[k]
@config_set[k; v]       → @config.set[k; v]
@config_save[path]      → @config.save[path]
@env_config[k]          → @config.env[k]

Namespace method aliases
─────────────────────────
@json.load_file[path]   → @json.load[path]
@json.save_file[p; obj] → @json.dump[p; obj]
@json.loads[s]          → @json.load[s]
@json.dumps[obj]        → @json.dump[obj]
@csv.load[path]         → @csv.read[path]
@csv.save[p; rows]      → @csv.write[p; rows]
@store.save[k; v]       → @store.set[k; v]
@store.load[k]          → @store.get[k]
@store.del[k]           → @store.clear[]  (approximate)
@log.warn[msg]          → @log.warning[msg]

New methods (via api.lib_call)
───────────────────────────────
@json.parse[s]              → parse JSON string (alias for json.loads in Python)
@json.stringify[obj]        → serialize to JSON string
@json.pretty[obj]           → pretty-printed JSON string (indent=2)
@json.minify[obj]           → compact JSON string (no spaces)
@json.keys[obj]             → list of keys from dict or JSON string
@json.values[obj]           → list of values from dict or JSON string
@json.get[obj; key]         → safe nested key access (dot-path support)
@json.merge[a; b]           → merge two dicts deeply
@json.diff[a; b]            → keys that differ between two dicts
@json.is_valid[s]           → True if string is valid JSON
@csv.headers[path]          → first row (column names) of CSV file
@csv.row_count[path]        → number of data rows (excluding header)
@csv.as_dicts[path]         → list of dicts (DictReader)
@csv.column[path; col]      → list of values for one column
@store.all[]                → all key-value pairs as dict
@store.keys[]               → all stored keys
@store.values[]             → all stored values
@store.has[k]               → True if key exists in store
@store.default[k; v]        → get key, set to v if missing, return value
@log.setup_file[path]       → configure log to write to file
@log.format_msg[lvl; msg]   → format a message string without logging
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@jload[":       "@json.load[",
    "@jdump[":       "@json.dump[",
    "@json_loads[":  "@json.load[",
    "@json_dumps[":  "@json.dump[",
    "@csv_read[":    "@csv.read[",
    "@csv_write[":   "@csv.write[",
    "@csv_filter[":  "@csv.filter[",
    "@csv_to_json[": "@csv.to_json[",
    "@store_set[":   "@store.set[",
    "@store_get[":   "@store.get[",
    "@store_clear[": "@store.clear[",
    "@ctx_set[":     "@ctx.set[",
    "@ctx_get[":     "@ctx.get[",
    "@ctx_push[":    "@ctx.push[",
    "@ctx_pop[":     "@ctx.pop[",
    "@log_info[":    "@log.info[",
    "@log_debug[":   "@log.debug[",
    "@log_warn[":    "@log.warning[",
    "@log_error[":   "@log.error[",
    "@config_load[": "@config.load[",
    "@config_get[":  "@config.get[",
    "@config_set[":  "@config.set[",
    "@config_save[": "@config.save[",
    "@env_config[":  "@config.env[",
}

METHOD_ALIASES: dict[str, str] = {
    "@json.load_file[":  "@json.load[",
    "@json.save_file[":  "@json.dump[",
    "@json.loads[":      "@json.load[",
    "@json.dumps[":      "@json.dump[",
    "@csv.load[":        "@csv.read[",
    "@csv.save[":        "@csv.write[",
    "@store.save[":      "@store.set[",
    "@store.load[":      "@store.get[",
    "@log.warn[":        "@log.warning[",
}

_JSON = "__import__('json')"
_CSV  = "__import__('csv')"


def _new_lib_calls(api) -> None:
    # json.parse, json.stringify, json.pretty already exist in core json lib.

    api.lib_call("json", "minify", lambda a: (
        f"{_JSON}.dumps({a[0]}, separators=(',', ':'))"
        if a else
        f"'null'"
    ))

    api.lib_call("json", "keys", lambda a: (
        f"(lambda _o: list(_o.keys()) if isinstance(_o, dict) "
        f"else list({_JSON}.loads(_o).keys()))({a[0]})"
        if a else
        f"[]"
    ))

    api.lib_call("json", "values", lambda a: (
        f"(lambda _o: list(_o.values()) if isinstance(_o, dict) "
        f"else list({_JSON}.loads(_o).values()))({a[0]})"
        if a else
        f"[]"
    ))

    api.lib_call("json", "get", lambda a: (
        f"(lambda _o, _k: "
        f"(lambda _d, _parts: "
        f"(__import__('functools').reduce(lambda _x, _p: _x.get(_p) if isinstance(_x, dict) else None, _parts, _d))"
        f")((_o if isinstance(_o, dict) else {_JSON}.loads(_o)), str({a[1]}).split('.')))"
        f"({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("json", "merge", lambda a: (
        f"(lambda _a, _b: {{**_a, **_b}})({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"dict({a[0]})" if a else f"{{}}"
    ))

    api.lib_call("json", "diff", lambda a: (
        f"{{_k for _k in set(list({a[0]}.keys()) + list({a[1]}.keys())) "
        f"if {a[0]}.get(_k) != {a[1]}.get(_k)}}"
        if len(a) > 1 else
        f"set()"
    ))

    api.lib_call("json", "is_valid", lambda a: (
        f"(lambda _s: (lambda: (__import__('json').loads(_s), True))() "
        f"if True else False)"
        f"({a[0]})"
        if a else
        f"False"
    ))

    api.lib_call("csv", "headers", lambda a: (
        f"next({_CSV}.reader(open({a[0]}, encoding='utf-8')), [])"
        if a else
        f"[]"
    ))

    api.lib_call("csv", "row_count", lambda a: (
        f"sum(1 for _ in open({a[0]}, encoding='utf-8')) - 1"
        if a else
        f"0"
    ))

    api.lib_call("csv", "as_dicts", lambda a: (
        f"list({_CSV}.DictReader(open({a[0]}, encoding='utf-8')))"
        if a else
        f"[]"
    ))

    api.lib_call("csv", "column", lambda a: (
        f"[row[str({a[1]})] for row in {_CSV}.DictReader(open({a[0]}, encoding='utf-8'))]"
        if len(a) > 1 else
        f"[]"
    ))

    # NOTE: @store.* is backed by a JSON file (.cruhon_store.json), read
    # and written via the __cruhon_store_* helpers the transpiler injects
    # (see transpiler.py's _STORE_HELPERS) — there has never been a
    # cruhon.core.libs.store_._STORE in-memory dict. The three handlers
    # below previously referenced that nonexistent attribute directly,
    # raising AttributeError on every call; "all" duplicated (and broke)
    # the already-correct core handler, so it's removed here rather than
    # re-registered.
    api.lib_call("store", "keys", lambda a: (
        "list(__cruhon_store_load().keys())"
    ))

    api.lib_call("store", "values", lambda a: (
        "list(__cruhon_store_load().values())"
    ))

    api.lib_call("store", "has", lambda a: (
        f"({a[0]} in __cruhon_store_load())"
        if a else
        "False"
    ))

    api.lib_call("log", "setup_file", lambda a: (
        f"(lambda _p: __import__('logging').basicConfig("
        f"filename=_p, level=__import__('logging').DEBUG, "
        f"format='%(asctime)s %(levelname)s %(message)s'))({a[0]})"
        if a else
        f"None"
    ))

    api.lib_call("log", "format_msg", lambda a: (
        f"f'[{{str({a[0]}).upper()}}] {{str({a[1]})}}'"
        if len(a) > 1 else
        f"str({a[0]})"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
