"""
cruhon-shortcuts  v1.0.0
=========================
Shortcut plugin for Cruhon — shorter syntax for all 33 built-in namespaces.

Instead of typing the full namespace every time:

    @file.read["data.txt"]
    @date.now[]
    @crypto.uuid[]
    @random.randint[1; 100]
    @http.get["https://api.example.com/data"]

…you can write:

    @read["data.txt"]
    @now[]
    @uuid[]
    @rand[1; 100]
    @get["https://api.example.com/data"]

Also adds extra convenience methods on existing namespaces:

    @file.head["log.txt"; 20]          — first 20 lines
    @file.grep["log.txt"; "ERROR"]     — lines matching a pattern
    @text.truncate["very long text"; 50]
    @random.password[20]               — random 20-char password
    @date.year[]                       — current year as int
    @statistics.summary[scores]        — mean/median/stdev/min/max dict

Configuration (mod.json)
────────────────────────
groups          "all"  or  ["file", "http", "date", "text", "math",
                             "crypto", "collections", "system", "data",
                             "stdlib", "types", "io"]
                Which shortcut groups to activate.

global_aliases  true / false
                Install source-level rewrites (@read → @file.read).
                Default: true.

method_aliases  true / false
                Install extra methods on existing namespaces
                (@file.cat, @file.head, …).
                Default: true.

disabled        []
                List of specific shortcut left-hand sides to skip.
                Example: ["@get[", "@post["]

custom          {}
                Your own extra rewrites.
                Example: {"@slurp[": "@file.read["}

Examples
────────
Minimal (everything on):
    {
        "name": "cruhon-shortcuts",
        "groups": "all",
        "global_aliases": true,
        "method_aliases": true,
        "disabled": [],
        "custom": {}
    }

Only file and HTTP shortcuts, no global aliases:
    {
        "name": "cruhon-shortcuts",
        "groups": ["file", "http"],
        "global_aliases": false,
        "method_aliases": true,
        "disabled": [],
        "custom": {}
    }

All on except @get and @post (keep those for something else):
    {
        "name": "cruhon-shortcuts",
        "groups": "all",
        "global_aliases": true,
        "method_aliases": true,
        "disabled": ["@get[", "@post["],
        "custom": {}
    }

Add your own shortcuts:
    {
        "name": "cruhon-shortcuts",
        "groups": "all",
        "global_aliases": true,
        "method_aliases": true,
        "disabled": [],
        "custom": {
            "@slurp[":  "@file.read[",
            "@spit[":   "@file.write[",
            "@stamp[]": "@date.datetime_str[]"
        }
    }
"""
from __future__ import annotations

from .shortcuts_config import ShortcutsConfig

_GROUP_MODULES: dict[str, str] = {
    "file":        "shortcuts_file",
    "http":        "shortcuts_http",
    "date":        "shortcuts_date",
    "text":        "shortcuts_text",
    "math":        "shortcuts_math",
    "crypto":      "shortcuts_crypto",
    "collections": "shortcuts_collections",
    "system":      "shortcuts_system",
    "data":        "shortcuts_data",
    "stdlib":      "shortcuts_stdlib",
    "types":       "shortcuts_types",
    "io":          "shortcuts_io",
}


def _make_rewriter(rewrites: dict[str, str]):
    """
    Build a before_parse hook that applies all shortcut rewrites.

    Rewrites are sorted by descending key length so that longer patterns
    are replaced first, preventing a shorter pattern from matching inside
    a longer one.

    For example, @file.cat_lines[ is sorted before @file.cat[ so the
    more-specific name wins if both existed.
    """
    if not rewrites:
        return None

    sorted_pairs = sorted(rewrites.items(), key=lambda kv: -len(kv[0]))

    def _rewrite(source: str) -> str:
        for old, new in sorted_pairs:
            source = source.replace(old, new)
        return source

    return _rewrite


def register(api) -> None:
    """Entry point called by the Cruhon mod loader."""
    cfg = ShortcutsConfig(api)

    all_rewrites: dict[str, str] = {}
    loaded_groups: list[str] = []
    skipped_groups: list[str] = []

    for group_name, module_name in _GROUP_MODULES.items():
        if not cfg.is_group_enabled(group_name):
            skipped_groups.append(group_name)
            continue

        try:
            import importlib
            mod = importlib.import_module(f".{module_name}", package=__name__)
            group_rewrites = mod.register_group(api, cfg)
            all_rewrites.update(group_rewrites)
            loaded_groups.append(group_name)
        except Exception as exc:
            import traceback
            print(
                f"  \033[33m⚠ [cruhon-shortcuts] Failed to load group '{group_name}': "
                f"{type(exc).__name__}: {exc}\033[0m"
            )
            traceback.print_exc()

    cfg.apply_custom(all_rewrites)

    rewriter = _make_rewriter(all_rewrites)
    if rewriter is not None:
        api.hook("before_parse", rewriter)

    _print_summary(loaded_groups, skipped_groups, len(all_rewrites), cfg)


def _print_summary(
    loaded: list[str],
    skipped: list[str],
    rewrite_count: int,
    cfg: ShortcutsConfig,
) -> None:
    import os
    if not os.environ.get("CRUHON_DEBUG"):
        return

    parts = [f"[cruhon-shortcuts] Loaded groups: {', '.join(loaded) or 'none'}"]
    if skipped:
        parts.append(f"Skipped: {', '.join(skipped)}")
    parts.append(f"Rewrites: {rewrite_count}")
    parts.append(f"Global aliases: {'on' if cfg.global_aliases else 'off'}")
    parts.append(f"Method aliases: {'on' if cfg.method_aliases else 'off'}")
    if cfg.custom:
        parts.append(f"Custom: {len(cfg.custom)}")
    print(f"  \033[90m{' | '.join(parts)}\033[0m")
