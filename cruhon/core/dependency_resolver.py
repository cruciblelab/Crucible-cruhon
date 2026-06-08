"""
cruhon/core/dependency_resolver.py
====================================
Mod dependency checking for v0.8.
Full topological sort planned for v0.9.

v0.8 behavior:
  - Check that required mods are loaded
  - Warn if dependency not satisfied
  - Determine load order (alphabetical + requirements first)
"""

from __future__ import annotations
from typing import Optional


class DependencyError(Exception):
    pass


class DependencyResolver:
    """
    Resolves mod load order based on api.require() declarations.

    v0.8: simple check — required mod must be loaded first.
    v0.9: full topological sort with conflict resolution.
    """

    def __init__(self):
        self._requirements: dict[str, list[str]] = {}  # mod → [required mods]
        self._loaded: list[str] = []

    def declare(self, mod_name: str, requires: list[str]):
        """Declare that mod_name requires these mods."""
        self._requirements[mod_name] = requires

    def mark_loaded(self, mod_name: str):
        """Mark a mod as successfully loaded."""
        if mod_name not in self._loaded:
            self._loaded.append(mod_name)

    def check(self, mod_name: str) -> list[str]:
        """
        Check if all requirements for mod_name are satisfied.
        Returns list of missing dependencies.
        """
        required = self._requirements.get(mod_name, [])
        missing = []
        for req in required:
            # Support "mod >= version" format (v0.8: ignore version, just check name)
            req_name = req.split()[0] if " " in req else req
            if req_name not in self._loaded:
                missing.append(req)
        return missing

    def ordered_load(self, mods: list[str]) -> list[str]:
        """
        Return mods in a load order that satisfies dependencies.
        v0.8: requirements first, then rest alphabetically.
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
