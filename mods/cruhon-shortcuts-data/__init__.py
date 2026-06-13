"""
cruhon-shortcuts-data  v1.0.0
===============================
Data & format shortcut plugin for Cruhon. Adds short aliases and a few
convenience methods for the namespaces introduced in Cruhon v2.4:

    @xml.*  @toml.*  @diff.*  @decimal.*  @fraction.*
    @ip.*   @platform.*  @unicode.*  @binascii.*  @shlex.*

Examples:
    @xml_parse["<a><b>hi</b></a>"]      → @xml.from_string[...]
    @toml_load["port = 8080"]           → @toml.loads[...]
    @similar["color"; "colour"]         → @diff.is_similar[...]
    @dec_add["0.1"; "0.2"]              → @decimal.add[...]
    @frac[1; 3]                         → @fraction.make[...]
    @is_private_ip["10.0.0.1"]          → @ip.is_private[...]
    @os_name[]                          → @platform.system[]
    @char_name["A"]                     → @unicode.name[...]
    @hexlify[b"AB"]                     → @binascii.hexlify[...]
    @sh_split["echo hi"]               → @shlex.split[...]

Loads cleanly alongside cruhon-shortcuts and cruhon-shortcuts-pro — all
global-rewrite names are distinct.

Configuration (mod.json)
─────────────────────────
groups      "all"  or  ["format", "numbers", "system"]
disabled    []      — global-rewrite left-hand sides to skip
custom      {}      — your own extra rewrites
"""
from __future__ import annotations

from .data_config import DataConfig

_GROUP_MODULES: dict[str, str] = {
    "format":  "data_format",
    "numbers": "data_numbers",
    "system":  "data_system",
    "media":   "data_media",
    "regex":   "data_regex",
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
    cfg = DataConfig(api)

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
                f"  \033[33m⚠ [cruhon-shortcuts-data] Failed to load group '{group_name}': "
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
    parts = [f"[cruhon-shortcuts-data] Loaded groups: {', '.join(loaded) or 'none'}"]
    if skipped:
        parts.append(f"Skipped: {', '.join(skipped)}")
    parts.append(f"Rewrites: {rewrite_count}")
    print(f"  \033[90m{' | '.join(parts)}\033[0m")
