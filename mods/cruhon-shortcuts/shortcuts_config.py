"""
cruhon-shortcuts — configuration parser
========================================
Reads values from mod.json and exposes them in a typed, validated form
for the group registration functions.

mod.json keys
─────────────
groups          "all"  or  ["file", "http", "date", ...]
                Which shortcut groups to activate. "all" enables every group.

global_aliases  true / false
                Whether to install source-level rewrites such as
                @read → @file.read.  When false, only namespace method
                aliases are registered.

method_aliases  true / false
                Whether to install extra methods on existing namespaces
                (@file.cat, @file.ls, @file.head, …).

disabled        []
                List of specific source-rewrite left-hand sides to skip.
                Example: ["@get[", "@post["] to keep those names free.

custom          {}
                User-defined extra rewrites applied after all group rewrites.
                Example: {"@slurp[": "@file.read[", "@spit[": "@file.write["}
"""
from __future__ import annotations

ALL_GROUPS: list[str] = [
    "file",
    "http",
    "date",
    "text",
    "math",
    "crypto",
    "collections",
    "system",
    "data",
    "stdlib",
    "types",
]


class ShortcutsConfig:
    """
    Parsed view of this plugin's mod.json configuration.

    Attributes
    ──────────
    groups          set[str]  — which group names are enabled
    global_aliases  bool      — install source rewrites
    method_aliases  bool      — install namespace method aliases
    disabled        set[str]  — rewrites to skip (left-hand side strings)
    custom          dict      — user extra rewrites {old: new}
    """

    def __init__(self, api):
        groups_val = api.config("groups", "all")
        if groups_val == "all" or groups_val is None:
            self.groups: set[str] = set(ALL_GROUPS)
        elif isinstance(groups_val, list):
            valid = set(ALL_GROUPS)
            self.groups = {g for g in groups_val if g in valid}
        else:
            self.groups = set(ALL_GROUPS)

        self.global_aliases: bool = bool(api.config("global_aliases", True))
        self.method_aliases: bool  = bool(api.config("method_aliases", True))
        self.disabled: set[str]    = set(api.config("disabled", []))
        raw_custom = api.config("custom", {})
        self.custom: dict[str, str] = raw_custom if isinstance(raw_custom, dict) else {}

    # ── helpers ──────────────────────────────────────────────────

    def is_group_enabled(self, name: str) -> bool:
        return name in self.groups

    def is_disabled(self, key: str) -> bool:
        return key in self.disabled

    def filter_rewrites(self, rewrites: dict[str, str]) -> dict[str, str]:
        """
        Return a copy of *rewrites* filtered by current config.

        - If global_aliases is False, returns {}.
        - Individual entries listed in *disabled* are removed.
        """
        if not self.global_aliases:
            return {}
        return {k: v for k, v in rewrites.items() if not self.is_disabled(k)}

    def filter_method_aliases(self, rewrites: dict[str, str]) -> dict[str, str]:
        """
        Return a copy of *rewrites* (namespace method aliases) filtered by
        current config.  Namespace aliases follow the same disabled-list as
        global aliases, and are also skipped when method_aliases is False.
        """
        if not self.method_aliases:
            return {}
        return {k: v for k, v in rewrites.items() if not self.is_disabled(k)}

    def apply_custom(self, rewrites: dict[str, str]) -> dict[str, str]:
        """Merge user-defined custom rewrites into *rewrites* (in place)."""
        rewrites.update(self.custom)
        return rewrites
