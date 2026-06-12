"""
cruhon-shortcuts-pro  v1.0.0
==============================
Extended shortcut plugin for Cruhon — higher-level composite operations
that complement the base cruhon-shortcuts plugin.

New @math.* methods:
    @clamp[x; lo; hi]       @lerp[a; b; t]      @sign[x]
    @round_to[x; n]         @percent[p; t]      @frange[s; e; step]
    @log2[x]  @log10[x]     @gcd[a; b]          @lcm[a; b]
    @factorial[n]           @hypot[x; y]        @sin/cos/tan[x]
    @degrees[r]             @radians[d]         @is_close[a; b]
    @math.inf[]             @math.e[]           @math.tau[]

New @collections.* list methods:
    @window[lst; n]         @transpose[matrix]  @unzip[pairs]
    @rotate_list[lst; n]    @head_n[lst; n]     @tail_n[lst; n]
    @interleave[a; b]       @dedupe[lst]        @flat[lst]
    @zip_all[*lists]        @cartesian[a; b]    @chunks[lst; n]
    @sorted_by[lst; key]    @pairs[lst]         @take_while[lst; fn]
    @drop_while[lst; fn]    @sum_of[lst; fn]    @min_by/max_by[lst; key]

New @collections.* dict methods:
    @pick_keys[d; keys]     @omit_keys[d; keys] @map_vals[d; fn]
    @filter_keys[d; fn]     @deep_merge[d1; d2] @dict_diff[d1; d2]
    @flat_dict[d]           @swap_kv[d]         @rename_key[d; k1; k2]
    @key_of[d; value]       @values_where[d;fn] @dict_product[d]

New @collections.* logic methods:
    @coalesce[v1; v2; ...]  @first_true[lst]    @count_if[lst; fn]
    @any_match[lst; fn]     @all_match[lst; fn] @none_match[lst; fn]
    @first_where[lst; fn]   @last_where[lst; fn]@default_if_none[v; d]
    @safe_get[d; k; dfl]    @unless_empty[v; d] @group_by[lst; fn]
    @tally[lst]             @index_of[lst; v]   @find_all[lst; fn]

New @text.* methods:
    @camel_case[s]          @snake_case[s]      @kebab_case[s]
    @pascal_case[s]         @word_freq[s]       @normalize_ws[s]
    @excerpt[s; n]          @initials[s]        @squeeze[s; ch]
    @ordinal[n]             @pluralize[w; n]    @de_accent[s]
    @wrap_lines[s; w]       @sentence_count[s]  @char_freq[s]

Configuration (mod.json)
─────────────────────────
groups      "all"  or  ["math", "lists", "dicts", "text", "logic", "regex", "http", "file"]

disabled    []
            Specific global rewrites to suppress.
            Example: ["@sign[", "@flat["]

custom      {}
            Your own extra rewrites.

This plugin can be loaded alongside cruhon-shortcuts without conflicts.
All global-rewrite names used here are distinct from those in cruhon-shortcuts.
"""
from __future__ import annotations

from .pro_config import ProConfig

_GROUP_MODULES: dict[str, str] = {
    "math":  "pro_math",
    "lists": "pro_lists",
    "dicts": "pro_dicts",
    "text":  "pro_text",
    "logic": "pro_logic",
    "regex": "pro_regex",
    "http":  "pro_http",
    "file":  "pro_file",
}


def _make_rewriter(rewrites: dict[str, str]):
    if not rewrites:
        return None
    sorted_pairs = sorted(rewrites.items(), key=lambda kv: -len(kv[0]))

    def _rewrite(source: str) -> str:
        for old, new in sorted_pairs:
            source = source.replace(old, new)
        return source

    return _rewrite


def register(api) -> None:
    cfg = ProConfig(api)

    all_rewrites: dict[str, str] = {}
    loaded: list[str] = []
    skipped: list[str] = []

    for group_name, module_name in _GROUP_MODULES.items():
        if not cfg.is_group_enabled(group_name):
            skipped.append(group_name)
            continue

        try:
            import importlib
            mod = importlib.import_module(f".{module_name}", package=__name__)
            group_rewrites = mod.register_group(api, cfg)
            all_rewrites.update(group_rewrites)
            loaded.append(group_name)
        except Exception as exc:
            import traceback
            print(
                f"  \033[33m⚠ [cruhon-shortcuts-pro] Failed to load group '{group_name}': "
                f"{type(exc).__name__}: {exc}\033[0m"
            )
            traceback.print_exc()

    cfg.apply_custom(all_rewrites)

    rewriter = _make_rewriter(all_rewrites)
    if rewriter is not None:
        api.hook("before_parse", rewriter)

    _print_summary(loaded, skipped, len(all_rewrites))


def _print_summary(loaded: list[str], skipped: list[str], rewrite_count: int) -> None:
    import os
    if not os.environ.get("CRUHON_DEBUG"):
        return
    parts = [f"[cruhon-shortcuts-pro] Loaded groups: {', '.join(loaded) or 'none'}"]
    if skipped:
        parts.append(f"Skipped: {', '.join(skipped)}")
    parts.append(f"Rewrites: {rewrite_count}")
    print(f"  \033[90m{' | '.join(parts)}\033[0m")
