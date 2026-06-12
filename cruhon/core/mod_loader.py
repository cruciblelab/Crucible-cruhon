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
import traceback as _traceback
from pathlib import Path
from typing import Optional

from .registry import register_lib, register_lib_call, register_mod, list_mods
from .lexer import get_lexer
from .parser import get_parser
from .transpiler import get_transpiler


# ─────────────────────────────────────────────────────────────
# CRUHON VERSION (used for compatibility checks)
# ─────────────────────────────────────────────────────────────

CRUHON_VERSION = "2.4.0"


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

_EXPOSED_APIS: dict[str, dict] = {}              # plugin_name → {key: value}
_REGISTERED_BLOCK_COMMANDS: dict[str, list] = {} # plugin_name → [cmd, ...]
_INJECT_PROVIDERS: dict = {}                      # key → value or factory()
_MISSING = object()  # sentinel for consume() default


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
        self._transpiler._visitor_owners[node_name] = self.mod_name

    def block_command(self, name: str, visitor_fn, *, scoped: bool = False):
        """
        Register a plugin block command.

        scoped=True: __ctx__ is automatically saved before the block body
        runs and restored afterward — changes inside the block don't leak out.

        Usage:
            api.block_command("route", visit_route)
            api.block_command("withuser", visit_withuser, scoped=True)

        visitor_fn(transpiler, node) → str
          node.args   — positional args
          node.kwargs — keyword args
          node.body   — child AST nodes
        """
        _name = name

        def _block_parser():
            return self._parser.parse_plugin_block(_name)

        self._parser.register_block_command(name, _block_parser)
        self._transpiler._block_visitors[name] = visitor_fn
        if scoped:
            self._transpiler._scoped_blocks.add(name)
        if self.mod_name not in _REGISTERED_BLOCK_COMMANDS:
            _REGISTERED_BLOCK_COMMANDS[self.mod_name] = []
        _REGISTERED_BLOCK_COMMANDS[self.mod_name].append(name)
        _log(f"[{self.mod_name}] Block command registered: @{name}" + (" (scoped)" if scoped else ""))

    def transform(self, target: str, fn):
        """
        Register a code transform for another plugin's block output.

        fn(transpiler, node, python_code: str) → str

        Transforms run after the primary visitor and before ctx restore.
        Multiple transforms chain in registration order.

        Usage (e.g. a logging plugin wrapping every @route block):
            def register(api):
                api.transform("route", wrap_with_timing)

            def wrap_with_timing(transpiler, node, code):
                path = node.args[0] if node.args else "unknown"
                before = transpiler._line(f'__t0__ = __import__("time").monotonic()')
                after  = transpiler._line(f'print(f"route {path} took {{__import__(\"time\").monotonic()-__t0__:.3f}}s")')
                return before + "\\n" + code + "\\n" + after
        """
        if target not in self._transpiler._node_transforms:
            self._transpiler._node_transforms[target] = []
        self._transpiler._node_transforms[target].append(fn)
        _log(f"[{self.mod_name}] Transform registered for @{target}")

    def block_hook(self, event: str, fn):
        """
        Register a runtime hook for plugin block enter/exit events.

        event: "enter" | "exit"
        fn(plugin_name: str, args: list) → None

        Fires at runtime when any plugin block starts or ends.
        Only active for blocks that have at least one hook registered.

        Usage:
            def register(api):
                api.block_hook("enter", on_block_enter)
                api.block_hook("exit",  on_block_exit)

            def on_block_enter(plugin_name, args):
                print(f"Block @{plugin_name} starting with args {args}")
        """
        if event not in self._transpiler._block_hooks:
            self._transpiler._block_hooks[event] = []
        self._transpiler._block_hooks[event].append(fn)
        _log(f"[{self.mod_name}] Block hook registered: {event}")

    def ast_hook(self, node_type: str, fn):
        """
        Register a parse-time AST hook.

        Fires on every node of the given type after parsing and before
        transpilation. fn receives the node and must return a node
        (the same or a modified one).

        node_type: class name of the node (e.g. "ForNode", "VarNode")
        fn(node) → node

        Multiple hooks for the same type fire in registration order.
        Hooks can read, modify, or replace nodes entirely.

        Usage:
            def register(api):
                api.ast_hook("ForNode", inject_profiling)

            def inject_profiling(node):
                node.var = node.var  # inspect or mutate
                return node
        """
        if node_type not in self._transpiler._ast_hooks:
            self._transpiler._ast_hooks[node_type] = []
        self._transpiler._ast_hooks[node_type].append(fn)
        _log(f"[{self.mod_name}] AST hook registered for {node_type}")

    def inject(self, key: str, value_or_factory):
        """
        Inject a value into the exec() globals for every script run.

        value_or_factory:
          - A plain value → injected as-is (same object every run, persistent)
          - A callable (no args) → called fresh before EACH exec(), return value injected

        For persistent resources (connection pools, singletons) pass the object directly
        or use inject_once() which evaluates the factory once at registration time.

        Scripts access the injected value by name directly, no __ns__ needed.

        Usage:
            def register(api):
                # Fresh DatabaseConnection on every run:
                api.inject("db", lambda: DatabaseConnection())
                # Persistent pool shared across all runs:
                pool = ConnectionPool(max=10)
                api.inject("pool", pool)
                # Constant:
                api.inject("APP_VERSION", "2.1.0")

        Script:
            @var[rows; db.query("SELECT * FROM users")]
            @print[{APP_VERSION}]
        """
        _INJECT_PROVIDERS[key] = value_or_factory
        _log(f"[{self.mod_name}] Inject registered: {key}")

    def inject_once(self, key: str, factory):
        """
        Inject a value evaluated ONCE at registration time (not per exec).

        Calls factory() immediately, stores the result. All script runs share
        the same object — ideal for connection pools, expensive singletons, etc.

        Usage:
            def register(api):
                api.inject_once("db_pool", lambda: DatabasePool(max_connections=10))
        """
        try:
            value = factory()
        except Exception as e:
            _log(f"[{self.mod_name}] inject_once factory for '{key}' raised {type(e).__name__}: {e}")
            value = None
        _INJECT_PROVIDERS[key] = value
        _log(f"[{self.mod_name}] inject_once registered: {key}")

    def inline_command(self, name: str, handler_fn):
        """
        Register an inline expression command usable inside argument contexts.

        handler_fn(parser) -> str
          Called when @name appears inside @var[x; @name[...]] etc.
          handler_fn must:
            1. Call parser.advance() to consume the @name token
            2. Optionally call parser.parse_args() for arguments
            3. Return a Python expression string

        Usage:
            def register(api):
                api.inline_command("uuid", handle_uuid)
                api.inline_command("now", handle_now)

            def handle_uuid(parser):
                parser.advance()
                parser.parse_args()  # consume [] even if no args
                return "__import__('uuid').uuid4().__str__()"

            def handle_now(parser):
                parser.advance()
                parser.parse_args()
                return "__import__('datetime').datetime.now()"

        Script:
            @var[id; @uuid[]]
            @var[ts; @now[]]
        """
        self._parser.register_inline_command(name, handler_fn)
        _log(f"[{self.mod_name}] Inline command registered: @{name}")

    def eval_hook(self, fn):
        """
        Register a value evaluation hook.

        fn(value: str, context: str) -> str | None

        Fires at transpile-time for every value passed to _eval_value().
        Return a Python expression string to override default evaluation.
        Return None to pass through to the default rules.

        context: "expr" (right-hand side values) or "display" (@print values)

        Hooks run in registration order. First non-None return wins.

        Usage:
            def register(api):
                api.eval_hook(dollar_env_hook)

            def dollar_env_hook(value, context):
                if value.startswith("$"):
                    return f'os.environ.get("{value[1:]}")'
                return None

        Script:
            @var[url; $DATABASE_URL]   → os.environ.get("DATABASE_URL")
            @print[$GREETING]           → print(os.environ.get("GREETING"))
        """
        self._transpiler._eval_hooks.append(fn)
        _log(f"[{self.mod_name}] Eval hook registered")

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
            # Core language
            "print":     "PrintNode",
            "var":       "VarNode",
            "const":     "ConstNode",
            "input":     "InputNode",
            "if":        "IfNode",
            "for":       "ForNode",
            "while":     "WhileNode",
            "repeat":    "RepeatNode",
            "func":      "FuncNode",
            "class":     "ClassNode",
            "return":    "ReturnNode",
            "break":     "BreakNode",
            "continue":  "ContinueNode",
            "pass":      "PassNode",
            "try":       "TryNode",
            "with":      "WithNode",
            "match":     "MatchNode",
            "del":       "DelNode",
            "raise":     "RaiseNode",
            "assert":    "AssertNode",
            "import":    "ImportNode",
            "include":   "IncludeNode",
            "global":    "GlobalNode",
            "nonlocal":  "NonlocalNode",
            "yield":     "YieldNode",
            "await":     "AwaitNode",
            "async_for": "AsyncForNode",
            "async_with":"AsyncWithNode",
            "raw":       "RawNode",
            "expr":      "ExprNode",
            "decorator": "DecorateNode",
            "foreach":   "ForeachNode",
            "inc":       "IncNode",
            "dec":       "DecNode",
            "swap":      "SwapNode",
            "env":       "EnvNode",
            "fetch":     "FetchNode",
            "list":      "ListNode",
            "dict":      "DictNode",
        }
        # Fallback: convert "some_name" or "some.name" → "SomeNameNode" (CamelCase)
        node_name = node_class_map.get(
            command,
            "".join(w.capitalize() for w in command.replace(".", "_").split("_")) + "Node"
        )

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
        self._transpiler._visitor_owners[node_name] = self.mod_name

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
            # Return the existing registered namespace so second mod can still use it
            existing_ns = get_namespace_registry().get(name)
            if existing_ns:
                return existing_ns
            # Registry is out of sync — register a new Namespace so scripts can reach it
            fallback_ns = Namespace(name)
            get_namespace_registry().register(name, fallback_ns)
            return fallback_ns

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

    def expose(self, key: str, value):
        """
        Publish a value or function for other plugins to consume.

        Usage (foundation plugin):
            api.expose("format_date", lambda dt: dt.strftime("%Y-%m-%d"))
            api.expose("slugify", lambda s: s.lower().replace(" ", "-"))
        """
        if self.mod_name not in _EXPOSED_APIS:
            _EXPOSED_APIS[self.mod_name] = {}
        _EXPOSED_APIS[self.mod_name][key] = value
        _log(f"[{self.mod_name}] Exposed: {key}")

    def consume(self, plugin_name: str, key: str, default=_MISSING):
        """
        Consume a value exposed by another plugin.

        Raises RuntimeError if plugin not loaded or key not exposed,
        unless a default is provided.

        Usage (dependent plugin):
            fmt = api.consume("cruhon-utils", "format_date")
            slugify = api.consume("cruhon-utils", "slugify", default=None)
        """
        plugin_apis = _EXPOSED_APIS.get(plugin_name, {})
        if key not in plugin_apis:
            if default is _MISSING:
                raise RuntimeError(
                    f"[{self.mod_name}] Cannot consume '{key}' from '{plugin_name}': "
                    f"not exposed or plugin not loaded. "
                    f"Make sure '{plugin_name}' is loaded before this plugin."
                )
            return default
        return plugin_apis[key]

    def is_loaded(self, name: str) -> bool:
        """
        Check if a plugin is loaded.

        Usage:
            if api.is_loaded("cruhon-redis"):
                api.expose("cache_backend", redis_cache)
            else:
                api.expose("cache_backend", memory_cache)
        """
        return name in _LOADED_MODS

    def config(self, key: str, default=None):
        """
        Read a value from this plugin's mod.json manifest.

        Usage (in register()):
            prefix = api.config("prefix", default="!")
            debug  = api.config("debug", default=False)
        """
        mod_info = _LOADED_MODS.get(self.mod_name, {})
        manifest = mod_info.get("manifest", {})
        return manifest.get(key, default)

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

    # ── Unregister / cleanup ──────────────────────────────────

    def unregister_command(self, name: str):
        """
        Remove a previously registered command or override visitor.

        Useful for testing (tear down between test cases) or conditional
        feature loading/unloading. If the command was never registered, no-op.

        Note: does NOT restore a replaced built-in — to do that, re-register
        the built-in's visitor manually.
        """
        node_name = "".join(w.capitalize() for w in name.replace(".", "_").split("_")) + "Node"
        self._transpiler._custom_visitors.pop(node_name, None)
        self._transpiler._visitor_owners.pop(node_name, None)
        self._transpiler._block_visitors.pop(name, None)
        self._transpiler._scoped_blocks.discard(name)
        self._parser._commands.pop(name, None)
        self._parser._block_commands.pop(name, None)
        _log(f"[{self.mod_name}] Command unregistered: @{name}")

    def remove_hook(self, event: str, fn):
        """
        Remove a previously registered lifecycle hook function.

        Works for all hook events: before_run, after_run, on_error,
        before_parse, after_parse, before_transpile, after_transpile.
        No-op if fn was never registered for that event.
        """
        if event == "before_parse":
            if fn in self._lexer._pre_hooks:
                self._lexer._pre_hooks.remove(fn)
        elif event == "after_parse":
            if fn in self._parser._post_hooks:
                self._parser._post_hooks.remove(fn)
        elif event == "before_transpile":
            if fn in self._transpiler._pre_hooks:
                self._transpiler._pre_hooks.remove(fn)
        elif event == "after_transpile":
            if fn in self._transpiler._post_hooks:
                self._transpiler._post_hooks.remove(fn)
        elif event in _RUNTIME_HOOKS:
            hooks = _RUNTIME_HOOKS[event]
            if fn in hooks:
                hooks.remove(fn)
        # Remove from local tracking too
        if event in self._hooks and fn in self._hooks[event]:
            self._hooks[event].remove(fn)
        _log(f"[{self.mod_name}] Hook removed: {event}")

    def remove_inject(self, key: str):
        """
        Remove a previously injected value from exec() globals.

        No-op if key was never registered.
        """
        _INJECT_PROVIDERS.pop(key, None)
        _log(f"[{self.mod_name}] Inject removed: {key}")

    def remove_eval_hook(self, fn):
        """Remove a previously registered eval hook."""
        if fn in self._transpiler._eval_hooks:
            self._transpiler._eval_hooks.remove(fn)
        _log(f"[{self.mod_name}] Eval hook removed")


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


def _record_loaded(name: str, version: str, source: str, source_path: str = "", manifest: dict = None):
    """Record a successfully loaded mod in the tracking structures."""
    _LOAD_ORDER.append(name)
    _LOADED_MODS[name] = {
        "version": version,
        "source": source,          # "pip" or "local"
        "source_path": source_path,
        "manifest": manifest or {},
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
            _record_loaded(mod_name, mod_version, "local", str(mod_path), manifest=manifest)
            _log(f"[ModLoader] Local mod loaded: {mod_name} v{mod_version}")
            # Dependency tracking
            from .dependency_resolver import get_dependency_resolver
            get_dependency_resolver().mark_loaded(mod_name, mod_version)
            missing = get_dependency_resolver().check(mod_name)
            for dep in missing:
                print(f"  \033[33m⚠ [{mod_name}] requires '{dep}' which is not loaded\033[0m")
            return True
        else:
            print(f"  ⚠ Mod has no register() function: {mod_name}")
            return False

    except Exception as e:
        print(f"  ✗ Failed to load mod {mod_path.name}: {e}")
        _traceback.print_exc()
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

                # Version compatibility check: pip mods declare constraint via
                # module-level CRUHON_REQUIRES = ">=2.0.0" or in dist metadata
                cruhon_req = getattr(module, "CRUHON_REQUIRES", None)
                if cruhon_req is None:
                    # Fall back to PyPI metadata Requires-Dist for cruhon
                    for req in (dist.metadata.get_all("Requires-Dist") or []):
                        if req.startswith("cruhon ") or req.startswith("cruhon>=") or req.startswith("cruhon>"):
                            cruhon_req = req.split("cruhon", 1)[1].strip().lstrip("=").lstrip()
                            break

                if cruhon_req and not _is_compatible(cruhon_req):
                    msg = (f"[{name}] requires cruhon {cruhon_req}, "
                           f"installed is {CRUHON_VERSION}. Skipping.")
                    print(f"  \033[31m✗ {msg}\033[0m")
                    _WARNINGS.append(f"✗ {msg}")
                    continue

                if hasattr(module, "register"):
                    # Read CRUHON_CONFIG dict from module for api.config() support
                    pip_manifest = dict(getattr(module, "CRUHON_CONFIG", {}))
                    pip_manifest.setdefault("name", name)
                    pip_manifest.setdefault("version", version)
                    api = ModAPI(name)
                    module.register(api)
                    register_mod(pip_manifest)
                    _record_loaded(name, version, "pip", manifest=pip_manifest)
                    _log(f"[ModLoader] pip mod loaded: {name}")
            except Exception as e:
                print(f"  ⚠ Failed to load pip mod {name}: {e}")
                _traceback.print_exc()

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


def list_exposed_apis() -> dict[str, list[str]]:
    """Return {plugin_name: [key, ...]} for all exposed plugin APIs."""
    return {name: list(apis.keys()) for name, apis in _EXPOSED_APIS.items()}


def list_block_commands() -> dict[str, list[str]]:
    """Return {plugin_name: [cmd, ...]} for all registered plugin block commands."""
    return {name: list(cmds) for name, cmds in _REGISTERED_BLOCK_COMMANDS.items()}


def get_inject_globals() -> dict:
    """
    Resolve all registered inject providers into a dict suitable for exec() globals.
    Callables are invoked; plain values are used as-is.
    """
    result = {}
    for key, val in _INJECT_PROVIDERS.items():
        try:
            result[key] = val() if callable(val) else val
        except Exception as e:
            _log(f"[inject] Factory for '{key}' raised {type(e).__name__}: {e}")
    return result
