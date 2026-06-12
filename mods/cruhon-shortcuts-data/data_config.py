"""
cruhon-shortcuts-data — configuration parser
==============================================
Reads mod.json and exposes a typed view for the group files.

mod.json keys
─────────────
groups      "all"  or  ["format", "numbers", "system"]
disabled    []      — global-rewrite left-hand sides to skip
custom      {}      — user-defined extra rewrites
"""
from __future__ import annotations

ALL_GROUPS: list[str] = ["format", "numbers", "system"]


class DataConfig:
    def __init__(self, api):
        groups_val = api.config("groups", "all")
        if groups_val == "all" or groups_val is None:
            self.groups: set[str] = set(ALL_GROUPS)
        elif isinstance(groups_val, list):
            valid = set(ALL_GROUPS)
            self.groups = {g for g in groups_val if g in valid}
        else:
            self.groups = set(ALL_GROUPS)

        self.disabled: set[str]     = set(api.config("disabled", []))
        raw_custom = api.config("custom", {})
        self.custom: dict[str, str] = raw_custom if isinstance(raw_custom, dict) else {}

    @property
    def method_aliases(self) -> bool:
        return True

    def is_group_enabled(self, name: str) -> bool:
        return name in self.groups

    def is_disabled(self, key: str) -> bool:
        return key in self.disabled

    def filter_rewrites(self, rewrites: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in rewrites.items() if not self.is_disabled(k)}

    def filter_method_aliases(self, rewrites: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in rewrites.items() if not self.is_disabled(k)}

    def apply_custom(self, rewrites: dict[str, str]) -> dict[str, str]:
        rewrites.update(self.custom)
        return rewrites
