"""
cruhon-shortcuts-pro — regex group
====================================
Shortcuts for @re.* — pattern matching and text manipulation.

Global aliases (source rewrites)
─────────────────────────────────
@re_match[pattern; s]       → @re.match[pattern; s]
@re_search[pattern; s]      → @re.search[pattern; s]
@re_find[pattern; s]        → @re.findall[pattern; s]
@re_sub[pat; repl; s]       → @re.sub[pat; repl; s]
@re_split[pattern; s]       → @re.split[pattern; s]
@re_is_match[pattern; s]    → @re.is_match[pattern; s]
@re_count[pattern; s]       → @re.count[pattern; s]
@re_groups[pattern; s]      → @re.groups[pattern; s]
@re_group1[pattern; s]      → @re.group1[pattern; s]
@re_named[pattern; s]       → @re.named[pattern; s]
@re_escape[s]               → @re.escape[s]
@re_replace_first[p; r; s]  → @re.replace_first[p; r; s]

Namespace method aliases
─────────────────────────
@re.find[p; s]              → @re.findall[p; s]
@re.test[p; s]              → @re.is_match[p; s]
@re.replace[p; r; s]        → @re.sub[p; r; s]
"""
from __future__ import annotations

_RE = "__import__('re')"

GLOBAL_REWRITES: dict[str, str] = {
    "@re_match[":        "@re.match[",
    "@re_search[":       "@re.search[",
    "@re_find[":         "@re.findall[",
    "@re_sub[":          "@re.sub[",
    "@re_split[":        "@re.split[",
    "@re_is_match[":     "@re.is_match[",
    "@re_count[":        "@re.count[",
    "@re_groups[":       "@re.groups[",
    "@re_group1[":       "@re.group1[",
    "@re_named[":        "@re.named[",
    "@re_escape[":       "@re.escape[",
    "@re_replace_first[": "@re.replace_first[",
    "@re_fullmatch[":    "@re.fullmatch[",
}

METHOD_ALIASES: dict[str, str] = {
    "@re.find[":    "@re.findall[",
    "@re.test[":    "@re.is_match[",
    "@re.replace[": "@re.sub[",
    "@re.first[":   "@re.group1[",
}


def _new_lib_calls(api) -> None:
    api.lib_call("re", "words", lambda a: (
        f"{_RE}.findall(r'\\w+', {a[0]})" if a else "[]"
    ))
    api.lib_call("re", "emails", lambda a: (
        f"{_RE}.findall(r'[\\w.+-]+@[\\w-]+\\.[\\w.]+', {a[0]})" if a else "[]"
    ))
    api.lib_call("re", "urls", lambda a: (
        f"{_RE}.findall(r'https?://[^\\s]+', {a[0]})" if a else "[]"
    ))
    api.lib_call("re", "numbers", lambda a: (
        f"{_RE}.findall(r'[-+]?\\d*\\.?\\d+', {a[0]})" if a else "[]"
    ))
    api.lib_call("re", "remove", lambda a: (
        f"{_RE}.sub({a[0]}, '', {a[1]})" if len(a) > 1 else "''"
    ))
    api.lib_call("re", "between", lambda a: (
        f"(lambda __m: __m.group(1) if __m else None)"
        f"({_RE}.search({a[0]} + r'(.*?)' + {a[1]}, {a[2]}, {_RE}.DOTALL))"
        if len(a) >= 3 else "None"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
