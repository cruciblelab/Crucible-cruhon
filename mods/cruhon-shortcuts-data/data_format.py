"""
cruhon-shortcuts-data — format group
======================================
Shortcuts for @xml.*, @toml.*, and @diff.*.

Global aliases (source rewrites)
─────────────────────────────────
@xml_parse[text]        → @xml.from_string[text]
@xml_load[path]         → @xml.parse[path]
@xml_dict[el]           → @xml.to_dict[el]
@xml_find[el; path]     → @xml.find[el; path]
@xml_text[el; path]     → @xml.find_text[el; path]
@toml_load[text]        → @toml.loads[text]
@toml_file[path]        → @toml.load[path]
@toml_get[text; key]    → @toml.get[text; key]
@diff_ratio[a; b]       → @diff.ratio[a; b]
@diff_lines[a; b]       → @diff.lines[a; b]
@similar[a; b]          → @diff.is_similar[a; b]
@closest[word; opts]    → @diff.best_match[word; opts]
@fuzzy[word; opts]      → @diff.close_matches[word; opts]

Namespace method aliases
─────────────────────────
@xml.dict[el]           → @xml.to_dict[el]
@xml.str[el]            → @xml.to_string[el]
@xml.all[el; path]      → @xml.find_all[el; path]
@toml.parse[text]       → @toml.loads[text]
@diff.similar[a; b]     → @diff.is_similar[a; b]
@diff.match[word; opts] → @diff.best_match[word; opts]

New methods (via api.lib_call)
───────────────────────────────
@xml.text_all[el; path] → list of texts for every matching element
@xml.attr_all[el; path] → list of attrib dicts for every matching element
@diff.changed[a; b]     → True if a and b are not identical (ratio < 1.0)
@toml.flatten[text]     → flatten parsed TOML into dotted-key dict
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@xml_parse[":   "@xml.from_string[",
    "@xml_load[":    "@xml.parse[",
    "@xml_dict[":    "@xml.to_dict[",
    "@xml_find[":    "@xml.find[",
    "@xml_text[":    "@xml.find_text[",
    "@toml_load[":   "@toml.loads[",
    "@toml_file[":   "@toml.load[",
    "@toml_get[":    "@toml.get[",
    "@diff_ratio[":  "@diff.ratio[",
    "@diff_lines[":  "@diff.lines[",
    "@similar[":     "@diff.is_similar[",
    "@closest[":     "@diff.best_match[",
    "@fuzzy[":       "@diff.close_matches[",
}

METHOD_ALIASES: dict[str, str] = {
    "@xml.dict[":    "@xml.to_dict[",
    "@xml.str[":     "@xml.to_string[",
    "@xml.all[":     "@xml.find_all[",
    "@toml.parse[":  "@toml.loads[",
    "@diff.similar[":"@diff.is_similar[",
    "@diff.match[":  "@diff.best_match[",
}

_TL = "__import__('tomllib')"


def _new_lib_calls(api) -> None:

    api.lib_call("xml", "text_all", lambda a: (
        f"[(_e.text or '').strip() for _e in {a[0]}.findall({a[1]})]"
        if len(a) > 1 else "[]"
    ))

    api.lib_call("xml", "attr_all", lambda a: (
        f"[dict(_e.attrib) for _e in {a[0]}.findall({a[1]})]"
        if len(a) > 1 else "[]"
    ))

    api.lib_call("diff", "changed", lambda a: (
        f"(__import__('difflib').SequenceMatcher(None, {a[0]}, {a[1]}).ratio() < 1.0)"
        if len(a) > 1 else "False"
    ))

    api.lib_call("toml", "flatten", lambda a: (
        f"(lambda _f: _f(_f, {_TL}.loads({a[0]}), ''))("
        f"lambda _f, _d, _p: {{_k2: _v2 "
        f"for _k, _v in _d.items() "
        f"for _k2, _v2 in (_f(_f, _v, (_p + '.' + _k) if _p else _k).items() "
        f"if isinstance(_v, dict) else [((_p + '.' + _k) if _p else _k, _v)])}})"
        if a else "{}"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
