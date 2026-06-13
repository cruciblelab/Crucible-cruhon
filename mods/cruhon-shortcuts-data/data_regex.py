"""
cruhon-shortcuts-data — regex group
=======================================
Shortcuts for @re.*.

Names that conflict with cruhon-shortcuts-pro are intentionally omitted
so both plugins load cleanly side by side (all global-rewrite names are
distinct when both plugins are active).

Global aliases (source rewrites)
─────────────────────────────────
@re_findall[pat; text]      → @re.findall[pat; text]
@is_match[pat; text]        → @re.is_match[pat; text]
@first_match[pat; text]     → @re.group1[pat; text]

Shared names below are kept because they map to the same target as the
pro plugin, so there is no actual conflict:
@re_match[pat; text]        → @re.match[pat; text]
@re_sub[pat; repl; text]    → @re.sub[pat; repl; text]
@re_split[pat; text]        → @re.split[pat; text]
@re_groups[m]               → @re.groups[m]
@re_named[m]                → @re.named[m]
@re_count[pat; text]        → @re.count[pat; text]

Namespace method aliases
─────────────────────────
@re.test[pat; text]         → @re.is_match[pat; text]
@re.replace[pat; repl; text]→ @re.sub[pat; repl; text]
@re.first[pat; text]        → @re.group1[pat; text]

New methods (via api.lib_call)
───────────────────────────────
@re.extract[pat; text]      → re.findall with group 1 only (first capture group)
@re.replace_all[pairs; text]→ apply multiple (pat, repl) replacements in sequence
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    # unique to this plugin
    "@re_findall[":  "@re.findall[",
    "@is_match[":    "@re.is_match[",
    "@first_match[": "@re.group1[",
    # same target as pro — harmless to duplicate, but kept for standalone use
    "@re_match[":    "@re.match[",
    "@re_sub[":      "@re.sub[",
    "@re_split[":    "@re.split[",
    "@re_groups[":   "@re.groups[",
    "@re_named[":    "@re.named[",
    "@re_count[":    "@re.count[",
}

METHOD_ALIASES: dict[str, str] = {
    # @re.find and @re.test would conflict with pro's findall mapping, omitted
    "@re.test[":     "@re.is_match[",
    "@re.replace[":  "@re.sub[",
    "@re.first[":    "@re.group1[",
}


def _new_lib_calls(api) -> None:

    api.lib_call("re", "extract", lambda a: (
        f"__import__('re').findall({a[0]}, {a[1]})"
        if len(a) > 1 else "[]"
    ))

    api.lib_call("re", "replace_all", lambda a: (
        f"__import__('functools').reduce("
        f"lambda _t, _pr: __import__('re').sub(_pr[0], _pr[1], _t), "
        f"{a[0]}, {a[1]})"
        if len(a) > 1 else a[1] if len(a) > 1 else "''"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
