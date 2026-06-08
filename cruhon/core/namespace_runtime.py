"""
cruhon/core/namespace_runtime.py
=================================
Runtime namespace system for Cruhon mods.

Namespace = mini runtime environment for a mod.
__ns__    = global namespace registry injected into exec().

Lifecycle:
  1. Namespace created via api.namespace()
  2. Methods registered via ns.register()
  3. Hooks attached via ns.hook()
  4. State stored via ns.state
  5. At exec: __ns__["name"].call("method", *args)
"""

from __future__ import annotations
from typing import Any, Callable, Optional


class Namespace:
    """
    Mini runtime environment for a single mod namespace.

    Usage (inside a mod's register function):
        ns = api.namespace("discord")
        ns.register("send", lambda args: ...)
        ns.hook("init", setup_fn)
        ns.state["token"] = os.environ.get("TOKEN")
    """

    def __init__(self, name: str):
        self.name = name
        self.state: dict[str, Any] = {}
        self._methods: dict[str, Callable] = {}
        self._hooks: dict[str, list[Callable]] = {
            "init":    [],
            "destroy": [],
        }
        self._initialized = False
        self.allowed_peers: set[str] = set()
        # Namespaces explicitly allowed to read this namespace's state.
        # Empty by default = fully isolated.

    def register(self, method: str, fn: Callable):
        """
        Register a method handler.
        fn(args: list) → any
        """
        self._methods[method] = fn

    def hook(self, event: str, fn: Callable):
        """Attach lifecycle hook: 'init' or 'destroy'."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(fn)

    def init(self):
        """Called by runner before exec(). Fires 'init' hooks."""
        if self._initialized:
            return
        for fn in self._hooks.get("init", []):
            fn(self)
        self._initialized = True

    def call(self, method: str, *args):
        """
        Called at runtime by generated code:
          __ns__["discord"].call("send", "hello")
        """
        if not self._initialized:
            self.init()
        if method not in self._methods:
            raise RuntimeError(
                f"[Cruhon] Namespace '{self.name}' has no method '{method}'. "
                f"Available: {sorted(self._methods.keys())}"
            )
        return self._methods[method](list(args))

    def destroy(self):
        """Called by runner after exec(). Fires 'destroy' hooks."""
        for fn in self._hooks.get("destroy", []):
            fn(self)
        self._initialized = False

    def access_state(self, key: str, caller_namespace: str) -> Any:
        """
        Read state with isolation enforcement.
        Only the owning namespace (or allowed peers) can access state.

        Usage:
            # From within discord namespace:
            ns.access_state("token", "discord")  # OK

            # From another namespace:
            ns.access_state("token", "http")  # RuntimeError
        """
        if caller_namespace != self.name and caller_namespace not in self.allowed_peers:
            raise RuntimeError(
                f"[Cruhon] Cross-namespace state access blocked: "
                f"'{caller_namespace}' cannot access state of '{self.name}'. "
                f"Use api.namespace('{self.name}').allow_peer('{caller_namespace}') "
                f"to explicitly allow this."
            )
        return self.state.get(key)

    def allow_peer(self, peer_namespace: str):
        """
        Explicitly allow another namespace to read this namespace's state.
        Must be called by the owning namespace's mod.

        Usage:
            ns = api.namespace("discord")
            ns.allow_peer("discord-voice")  # allow discord-voice to read discord state
        """
        self.allowed_peers.add(peer_namespace)

    def write_state(self, key: str, value: Any, caller_namespace: str):
        """
        Write state with isolation enforcement.
        Only the owning namespace can write its own state.
        No exceptions — peers cannot write, only read.
        """
        if caller_namespace != self.name:
            raise RuntimeError(
                f"[Cruhon] Cross-namespace state write blocked: "
                f"'{caller_namespace}' cannot write state of '{self.name}'."
            )
        self.state[key] = value

    def __repr__(self):
        return f"Namespace({self.name!r}, methods={sorted(self._methods.keys())})"


class NamespaceRegistry:
    """
    Global registry of all active namespaces.
    Injected into exec() as __ns__.
    """

    def __init__(self):
        self._namespaces: dict[str, Namespace] = {}

    def register(self, name: str, ns: Namespace):
        self._namespaces[name] = ns

    def get(self, name: str) -> Optional[Namespace]:
        return self._namespaces.get(name)

    def __getitem__(self, name: str) -> Namespace:
        if name not in self._namespaces:
            raise RuntimeError(
                f"[Cruhon] Namespace '{name}' not found. "
                f"Is the mod loaded? Available: {sorted(self._namespaces.keys())}"
            )
        return self._namespaces[name]

    def __contains__(self, name: str) -> bool:
        return name in self._namespaces

    def init_all(self):
        """Init all registered namespaces before exec()."""
        for ns in self._namespaces.values():
            ns.init()

    def destroy_all(self):
        """Destroy all namespaces after exec()."""
        for ns in self._namespaces.values():
            ns.destroy()

    def list(self) -> list:
        return sorted(self._namespaces.keys())


# Module-level singleton
_registry = NamespaceRegistry()


def get_namespace_registry() -> NamespaceRegistry:
    return _registry


def reset_registry():
    """Reset for testing."""
    global _registry
    _registry = NamespaceRegistry()
