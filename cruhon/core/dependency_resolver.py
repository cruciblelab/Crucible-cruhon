"""
cruhon/core/dependency_resolver.py
====================================
Mod dependency resolution and load order.

Behavior:
  - Check that required mods are loaded before dependents
  - Version-aware constraint checking (>=, ==, <, etc.)
  - Topological load ordering with circular dependency fallback
  - Warn if any dependency is unsatisfied after full load
"""

from __future__ import annotations
from typing import Optional


class DependencyError(Exception):
    pass


class DependencyResolver:
    """
    Resolves mod load order based on api.require() declarations.

    Uses topological ordering: dependencies are loaded before dependents.
    Circular or unresolvable dependencies are placed at the end with a warning.
    """

    def __init__(self):
        self._requirements: dict[str, list[str]] = {}  # mod → [required mods]
        self._loaded: list[str] = []
        self._loaded_versions: dict[str, str] = {}  # mod_name → version string

    def declare(self, mod_name: str, requires: list[str]):
        """Declare that mod_name requires these mods."""
        self._requirements[mod_name] = requires

    def mark_loaded(self, mod_name: str, version: str = "?"):
        """Mark a mod as successfully loaded."""
        if mod_name not in self._loaded:
            self._loaded.append(mod_name)
        self._loaded_versions[mod_name] = version

    def check(self, mod_name: str) -> list[str]:
        """
        Check if all requirements for mod_name are satisfied.
        Returns list of missing or version-mismatched dependencies.
        """
        from .mod_loader import _parse_version, _check_version_compat
        required = self._requirements.get(mod_name, [])
        missing = []
        for req in required:
            parts = req.strip().split(None, 1)
            req_name = parts[0]
            version_constraint = parts[1] if len(parts) > 1 else None

            if req_name not in self._loaded_versions:
                missing.append(req)
            elif version_constraint:
                loaded_ver = self._loaded_versions[req_name]
                if not _check_version_compat(version_constraint, loaded_ver):
                    missing.append(f"{req} (loaded: {loaded_ver})")
        return missing

    def ordered_load(self, mods: list[str]) -> list[str]:
        """
        Return mods in a load order that satisfies dependencies.
        Dependencies are placed before dependents. Circular deps go last.
        """
        result = []
        remaining = list(mods)

        # Simple pass: add mods whose dependencies are already in result
        max_passes = len(mods) + 1
        passes = 0
        while remaining and passes < max_passes:
            passes += 1
            for mod in list(remaining):
                required = self._requirements.get(mod, [])
                req_names = [r.split()[0] if " " in r else r for r in required]
                if all(r in result or r not in mods for r in req_names):
                    result.append(mod)
                    remaining.remove(mod)

        # Any remaining (circular or unresolved) go at end
        result.extend(remaining)
        return result

    def validate_all(self) -> list[str]:
        """
        Check all loaded mods for unsatisfied dependencies.
        Returns list of warning messages.
        """
        warnings = []
        for mod in self._loaded:
            missing = self.check(mod)
            for dep in missing:
                warnings.append(
                    f"⚠ [{mod}] requires '{dep}' but it is not loaded."
                )
        return warnings


# Singleton
_resolver = DependencyResolver()


def get_dependency_resolver() -> DependencyResolver:
    return _resolver


def reset_resolver():
    global _resolver
    _resolver = DependencyResolver()
