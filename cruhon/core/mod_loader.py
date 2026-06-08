"""
cruhon/core/mod_loader.py
=========================
Minecraft-style mod system with deterministic load order.

Load order (always enforced):
  1. core       — built-in (always first)
  2. stdlib     — built-in (always second)
  3. pip mods   — cruhon-* packages, sorted alphabetically by package name
  4. local mods — mods/ subfolders, sorted alphabetically by folder name

Override chain:
  When multiple mods override the same command, they form a middleware
  chain. First loaded = outermost wrapper. Each handler receives
  (transpiler, node, next_fn) and may or may not call next_fn.

Conflict resolution:
  - Namespace conflict: second registrant is skipped (warning printed)
  - Alias conflict:     second registrant is skipped (warning printed)
  - Override:           NOT a conflict — added to chain with warning

Version check:
  mod.json "cruhon" field is checked against the running version.
  Incompatible mods are skipped.
"""

from __future__ import annotations
import importlib
import importlib.metadata
import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Optional

from .registry import register_lib, register_lib_call, register_mod, list_mods
from .lexer import get_lexer
from .parser import get_parser
from .transpiler import get_transpiler


# ─────────────────────────────────────────────────────────────
# CRUHON VERSION (used for compatibility checks)
# ─────────────────────────────────────────────────────────────

CRUHON_VERSION = "0.9.2"


# ─────────────────────────────────────────────────────────────
# LOAD ORDER TRACKING
# ─────────────────────────────────────────────────────────────

_LOAD_ORDER: list[str] = []          # ordered list of mod names as loaded
_LOADED_MODS: dict[str, dict] = {}   # name → {version, source, namespace?, ...}


# ─────────────────────────────────────────────────────────────
# CONFLICT + OVERRIDE TRACKING
# ─────────────────────────────────────────────────────────────

_CLAIMED_NAMESPACES: dict[str, str] = {}   # namespace → first claimant mod name
_CLAIMED_ALIASES: dict[str, str] = {}      # alias    → first claimant mod name
_OVERRIDE_CHAINS: dict[str, list[str]] = {}  # command → [mod names in chain order]
_WARNINGS: list[str] = []                  # collected warnings for `cruhon mods`


# ─────────────────────────────────────────────────────────────
# VERSION COMPATIBILITY
# ─────────────────────────────────────────────────────────────

def _parse_version(v: str) -> tuple[int, ...]:
    """Parse '1.2.3' -> (1, 2, 3). Non-numeric parts become 0."""
    parts = []
    for seg in v.strip().split("."):
        try:
            parts.append(int(seg))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _check_version_compat(constraint: str, installed: str) -> bool:
    """
    Check a single constraint like '>=0.3.0' against installed version.
    Supports: >=, >, ==, <=, <
    """
    constraint = constraint.strip()
    for op in (">=", "<=", "==", ">", "<"):
        if constraint.startswith(op):
            required = _parse_version(constraint[len(op):])
            current = _parse_version(installed)
            if op == ">=": return current >= required
            if op == "<=": return current <= required
            if op == "==": return current == required
            if op == ">":  return current > required
            if op == "<":  return current < required
    # No operator — treat as ==
    return _parse_version(installed) == _parse_version(constraint)


def _is_compatible(cruhon_constraint: str) -> bool:
    """
    Support comma-separated constraints: '>=0.3.0,<1.0.0'
    All must pass.
    """
    for part in cruhon_constraint.split(","):
        if not _check_version_compat(part.strip(), CRUHON_VERSION):
            return False
    return True


# ─────────────────────────────────────────────────────────────
# MOD API — interface given to each mod's register() function
# ─────────────────────────────────────────────────────────────

class ModAPI:
    """
    The API object passed to each mod's register(api) function.
    Mods integrate with the system through this object.

    Usage (inside a mod):

        def register(api):
            # Add new command
            api.command("db.get", parse_db_get, visit_db_get)

            # Override existing command (added to chain)
            api.override("print", my_custom_print_visitor)

            # Hook into lifecycle
            api.hook("before_run", setup_db_connection)

            # Add library
            api.lib("redis", "redis")
            api.lib_call("redis", "get", lambda args: f"redis.get({args[0]})")

            # Register namespace (prevents collision)
            api.namespace("db")

            # Register alias
            api.alias("fetch", "http.get")
    """

    def __init__(self, mod_name: str):
        self.mod_name = mod_name
        self._lexer = get_lexer()
        self._parser = get_parser()
        self._transpiler = get_transpiler()
        self._hooks: dict[str, list] = {}

    # ── Command system ────────────────────────────────────────

    def command(self, name: str, parser_fn, visitor_fn, *, block: bool = False):
        """
        Register a new @command.

        parser_fn(parser) -> Node
        visitor_fn(transpiler, node) -> str
        """
        from .ast_nodes import register_node

        if block:
            self._parser.register_block_command(name, lambda: parser_fn(self._parser))
        else:
            self._parser.register_command(name, lambda: parser_fn(self._parser))

        node_name = f"{name.replace('.', '_').title()}Node"
        self._transpiler._custom_visitors[node_name] = visitor_fn

    def override(self, command: str, fn, warn: bool = True):
        """
        Override an existing core command with a middleware chain.

        fn signature (3-arg, recommended):
            fn(transpiler, node, next_fn) -> str
            next_fn calls the next handler in the chain.
            If fn does not call next_fn, chain stops there.

        fn signature (2-arg, backward compatible):
            fn(transpiler, node) -> str
            Treated as a terminal override (does not call next_fn).

        First mod loaded = outermost wrapper.
        """
        node_class_map = {
            "print":    "PrintNode",
            "var":      "VarNode",
            "if":       "IfNode",
            "for":      "ForNode",
            "while":    "WhileNode",
            "func":     "FuncNode",
            "class":    "ClassNode",
            "return":   "ReturnNode",
            "try":      "TryNode",
            "import":   "ImportNode",
        }
        node_name = node_class_map.get(command, f"{command.title()}Node")

        # Build the current chain entry
        if node_name not in _OVERRIDE_CHAINS:
            _OVERRIDE_CHAINS[node_name] = ["core"]

        _OVERRIDE_CHAINS[node_name].append(self.mod_name)
        chain_display = " → ".join(_OVERRIDE_CHAINS[node_name])

        if warn:
            msg = f"[{self.mod_name}] overrides @{command} (chain: {chain_display})"
            print(f"  \033[33m⚠ {msg}\033[0m")
            _WARNINGS.append(f"⚠ {msg}")

        # Wrap: if fn takes 2 args it's backward compatible (terminal override).
        # If it takes 3, pass next_fn so the chain can continue.
        try:
            sig = inspect.signature(fn)
            n_params = len(sig.parameters)
        except (ValueError, TypeError):
            n_params = 2

        # Get previous handler from transpiler (could be core or a prior override)
        previous_handler = self._transpiler._custom_visitors.get(node_name)
        if previous_handler is None:
            # Fallback to the built-in visit method
            builtin_name = f"visit_{node_name}"
            builtin = getattr(self._transpiler.__class__, builtin_name, None)
            if builtin:
                previous_handler = lambda t, n, _b=builtin: _b(t, n)

        if n_params >= 3:
            # next_fn-aware: wrap so chain is preserved
            _prev = previous_handler
            def _make_chain(user_fn, prev):
                def chained(transpiler, node):
                    def next_fn():
                        if prev:
                            return prev(transpiler, node)
                        return ""
                    return user_fn(transpiler, node, next_fn)
                return chained
            wrapped = _make_chain(fn, _prev)
        else:
            # Backward-compatible: fn(t, n) — terminal, ignores chain
            wrapped = fn

        self._transpiler._custom_visitors[node_name] = wrapped

    def namespace(self, name: str):
        """
        Create and register a mod namespace.

        v0.8: returns a Namespace object for method registration.
        Replaces the old claim_namespace() / bool-returning version.

        Usage in mod's register():
            ns = api.namespace("discord")
            ns.register("send", lambda args: discord_api.send(args[0]))
            ns.hook("init", lambda ns: ns.state.update({"ready": True}))

        Returns the Namespace object.
        """
        from .namespace_runtime import Namespace, get_namespace_registry
        # Still claim the name string for conflict detection
        if name in _CLAIMED_NAMESPACES:
            existing = _CLAIMED_NAMESPACES[name]
            msg = f"[{self.mod_name}] namespace '{name}' already claimed by [{existing}]. Skipping."
            print(f"  \033[33m⚠ {msg}\033[0m")
            _WARNINGS.append(f"⚠ {msg}")
            # Return the existing namespace — do NOT create or overwrite
            existing_ns = get_namespace_registry().get(name)
            if existing_ns:
                return existing_ns
            return Namespace(name)  # orphaned fallback (registry unchanged)

        _CLAIMED_NAMESPACES[name] = self.mod_name
        ns = Namespace(name)
        get_namespace_registry().register(name, ns)
        _log(f"[{self.mod_name}] Namespace registered: {name}")
        return ns

    def require(self, dependency: str):
        """
        Declare a mod dependency.

        Usage:
            api.require("http")
            api.require("cruhon-json >= 1.0")

        dependency: mod name or "mod_name >= version"
        Checked at load time. Warning if not satisfied.
        """
        from .dependency_resolver import get_dependency_resolver
        resolver = get_dependency_resolver()
        existing = resolver._requirements.get(self.mod_name, [])
        existing.append(dependency)
        resolver.declare(self.mod_name, existing)
        _log(f"[{self.mod_name}] Requires: {dependency}")

    def alias(self, alias_name: str, target: str) -> bool:
        """
        Register an alias shortcut.
        Returns True if successfully registered, False if already taken.
        """
        if alias_name in _CLAIMED_ALIASES:
            existing = _CLAIMED_ALIASES[alias_name]
            msg = f"[{self.mod_name}] alias '{alias_name}' already claimed by [{existing}]. Skipping."
            print(f"  \033[33m⚠ {msg}\033[0m")
            _WARNINGS.append(f"⚠ {msg}")
            return False
        _CLAIMED_ALIASES[alias_name] = self.mod_name
        return True

    def hook(self, event: str, fn):
        """
        Hook into lifecycle events.

        Events:
          "before_run"       — before program runs
          "after_run"        — after program runs
          "before_parse"     — before parse (receives source)
          "after_parse"      — after parse (receives AST)
          "before_transpile" — before transpile (receives AST)
          "after_transpile"  — after transpile (receives Python code)
          "on_error"         — when an error occurs
        """
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(fn)

        if event == "before_parse":
            self._lexer.add_pre_hook(fn)
        elif event == "after_parse":
            self._parser.add_post_hook(fn)
        elif event == "before_transpile":
            self._transpiler.add_pre_hook(fn)
        elif event == "after_transpile":
            self._transpiler.add_post_hook(fn)
        elif event in ("before_run", "after_run", "on_error"):
            _RUNTIME_HOOKS.setdefault(event, []).append(fn)

    # ── Library system ────────────────────────────────────────

    def lib(self, name: str, python_module: str):
        """Register a new library."""
        register_lib(name, python_module)
        _log(f"[{self.mod_name}] Lib registered: {name} → {python_module}")

    def lib_call(self, namespace: str, method: str, handler):
        """Register a library method call handler."""
        register_lib_call(namespace, method, handler)

    # ── Syntax extension ─────────────────────────────────────

    def syntax(self, token_type: str):
        """Add a new token type."""
        from .lexer import register_token_type
        register_token_type(token_type)

    def lexer_hook(self, fn):
        """Add a lexer pre-hook — manipulate source code."""
        self._lexer.add_pre_hook(fn)

    def token_hook(self, fn):
        """Add a lexer post-hook — manipulate token list."""
        self._lexer.add_post_hook(fn)


# ─────────────────────────────────────────────────────────────
# RUNTIME HOOKS
# ─────────────────────────────────────────────────────────────

_RUNTIME_HOOKS: dict[str, list] = {}


def fire_hook(event: str, *args, **kwargs):
    """Fire a runtime hook."""
    for fn in _RUNTIME_HOOKS.get(event, []):
        fn(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _log(msg: str):
    if os.environ.get("CRUHON_DEBUG"):
        print(f"  \033[90m{msg}\033[0m")


def _record_loaded(name: str, version: str, source: str, source_path: str = ""):
    """Record a successfully loaded mod in the tracking structures."""
    _LOAD_ORDER.append(name)
    _LOADED_MODS[name] = {
        "version": version,
        "source": source,          # "pip" or "local"
        "source_path": source_path,
    }


# ─────────────────────────────────────────────────────────────
# MOD LOADING
# ─────────────────────────────────────────────────────────────

def load_mod_from_path(mod_path: Path) -> bool:
    """
    Load a mod from a directory.

    Mod structure:
        my-mod/
        ├── mod.json      ← manifest
        └── __init__.py   ← must contain register(api)
    """
    manifest_path = mod_path / "mod.json"
    init_path = mod_path / "__init__.py"

    if not manifest_path.exists():
        print(f"  ⚠ Mod manifest not found: {manifest_path}")
        return False

    if not init_path.exists():
        print(f"  ⚠ Mod __init__.py not found: {init_path}")
        return False

    try:
        with open(manifest_path) as f:
            manifest = json.load(f)

        mod_name = manifest.get("name", mod_path.name)
        mod_version = manifest.get("version", "?")

        if mod_name in _LOADED_MODS:
            _log(f"[ModLoader] Already loaded: {mod_name}")
            return True

        # Version compatibility check
        cruhon_req = manifest.get("cruhon")
        if cruhon_req:
            if not _is_compatible(cruhon_req):
                msg = (f"[{mod_name}] requires cruhon {cruhon_req}, "
                       f"installed is {CRUHON_VERSION}. Skipping.")
                print(f"  \033[31m✗ {msg}\033[0m")
                _WARNINGS.append(f"✗ {msg}")
                return False

        # Load module
        spec = importlib.util.spec_from_file_location(mod_name, init_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)

        if hasattr(module, "register"):
            api = ModAPI(mod_name)
            module.register(api)
            register_mod(manifest)
            _record_loaded(mod_name, mod_version, "local", str(mod_path))
            _log(f"[ModLoader] Local mod loaded: {mod_name} v{mod_version}")
            # Dependency tracking
            from .dependency_resolver import get_dependency_resolver
            get_dependency_resolver().mark_loaded(mod_name)
            missing = get_dependency_resolver().check(mod_name)
            for dep in missing:
                print(f"  \033[33m⚠ [{mod_name}] requires '{dep}' which is not loaded\033[0m")
            return True
        else:
            print(f"  ⚠ Mod has no register() function: {mod_name}")
            return False

    except Exception as e:
        print(f"  ✗ Failed to load mod {mod_path.name}: {e}")
        return False


def load_pip_mods():
    """
    Discover and load pip-installed cruhon-* mods.
    Sorted alphabetically by package name for determinism.
    """
    try:
        candidates = []
        for dist in importlib.metadata.distributions():
            name = dist.metadata.get("Name", "")
            if name.startswith("cruhon-") and name != "cruhon":
                candidates.append((name, dist))

        # Sort alphabetically for determinism
        candidates.sort(key=lambda x: x[0])

        for name, dist in candidates:
            if name in _LOADED_MODS:
                continue
            try:
                module_name = name.replace("-", "_")
                module = importlib.import_module(module_name)
                version = dist.metadata.get("Version", "?")

                # Version compatibility check via dist metadata if present
                # (pip mods may not have a mod.json; skip if no constraint info)
                if hasattr(module, "register"):
                    api = ModAPI(name)
                    module.register(api)
                    register_mod({"name": name, "version": version})
                    _record_loaded(name, version, "pip")
                    _log(f"[ModLoader] pip mod loaded: {name}")
            except Exception as e:
                print(f"  ⚠ Failed to load pip mod {name}: {e}")

    except Exception:
        pass  # importlib.metadata unavailable — silently skip


def load_local_mods(mods_dir: Optional[Path] = None):
    """
    Load mods from the local mods/ directory.
    Sorted alphabetically by folder name for determinism.
    """
    if mods_dir is None:
        mods_dir = Path.cwd() / "mods"

    if not mods_dir.exists():
        return

    # Sorted alphabetically — deterministic
    candidates = sorted(
        (p for p in mods_dir.iterdir() if p.is_dir() and not p.name.startswith("_")),
        key=lambda p: p.name
    )

    for mod_path in candidates:
        load_mod_from_path(mod_path)


def load_all_mods(project_dir: Optional[Path] = None):
    """
    Load all mods in deterministic order:
      1. core    (built-in — already "loaded", recorded below)
      2. stdlib  (built-in — already "loaded", recorded below)
      3. pip mods (cruhon-* packages, sorted alphabetically)
      4. local mods (mods/ subfolders, sorted alphabetically)
    """
    # Record built-ins at the front (only once per process)
    if "core" not in _LOADED_MODS:
        _LOAD_ORDER.insert(0, "core")
        _LOADED_MODS["core"] = {"version": CRUHON_VERSION, "source": "built-in", "source_path": ""}
    if "stdlib" not in _LOADED_MODS:
        idx = _LOAD_ORDER.index("core") + 1 if "core" in _LOAD_ORDER else 0
        _LOAD_ORDER.insert(idx, "stdlib")
        _LOADED_MODS["stdlib"] = {"version": CRUHON_VERSION, "source": "built-in", "source_path": ""}

    load_pip_mods()
    load_local_mods(project_dir / "mods" if project_dir else None)

    if len(_LOAD_ORDER) > 2:
        user_mods = [m for m in _LOAD_ORDER if m not in ("core", "stdlib")]
        _log(f"[ModLoader] Active user mods: {', '.join(user_mods)}")


# ─────────────────────────────────────────────────────────────
# PUBLIC QUERY FUNCTIONS
# ─────────────────────────────────────────────────────────────

def list_loaded_mods() -> list[str]:
    """Return mod names in load order."""
    return list(_LOAD_ORDER)


def get_load_order() -> list[dict]:
    """
    Return full load-order info for display.
    Each entry: {name, version, source, source_path}
    """
    result = []
    for name in _LOAD_ORDER:
        info = _LOADED_MODS.get(name, {})
        result.append({
            "name": name,
            "version": info.get("version", "?"),
            "source": info.get("source", "?"),
            "source_path": info.get("source_path", ""),
        })
    return result


def get_override_chains() -> dict[str, list[str]]:
    """Return active override chains: {node_name: [mod_names]}."""
    return dict(_OVERRIDE_CHAINS)


def get_warnings() -> list[str]:
    """Return collected warnings."""
    return list(_WARNINGS)
