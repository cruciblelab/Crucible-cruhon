"""
cruhon/core/ast_nodes.py
========================
All AST node definitions. Every syntax element is a node.
Mods can add new node types via register_node().
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ─────────────────────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────────────────────

@dataclass
class Node:
    """Base class for all AST nodes."""
    line: int = 0

    def accept(self, visitor):
        """Visitor pattern — the transpiler uses this to process each node."""
        method = f"visit_{self.__class__.__name__}"
        visitor_fn = getattr(visitor, method, visitor.visit_unknown)
        return visitor_fn(self)


# ─────────────────────────────────────────────────────────────
# CORE NODES
# ─────────────────────────────────────────────────────────────

@dataclass
class ProgramNode(Node):
    """Root node — the entire program."""
    body: List[Node] = field(default_factory=list)


@dataclass
class VarNode(Node):
    """@var[name; value]"""
    name: str = ""
    value: Any = None


@dataclass
class ConstNode(Node):
    """@const[NAME; value] — constant declaration (convention: uppercase)"""
    name: str = ""
    value: Any = None


@dataclass
class PrintNode(Node):
    """@print[value]"""
    value: Any = None


@dataclass
class InputNode(Node):
    """@input[prompt]"""
    prompt: str = ""


@dataclass
class ReturnNode(Node):
    """@return[value]"""
    value: Any = None


@dataclass
class BreakNode(Node):
    """@break"""
    pass


@dataclass
class ContinueNode(Node):
    """@continue"""
    pass


@dataclass
class ExprNode(Node):
    """Raw expression — arithmetic, comparisons, etc."""
    expr: str = ""


@dataclass
class AssertNode(Node):
    """@assert[condition; message]"""
    condition: str = ""
    message: str = ""


@dataclass
class EnvNode(Node):
    """@env[KEY] or @env[KEY; default] — reads an environment variable."""
    key: str = ""
    default: Optional[str] = None


@dataclass
class IncludeNode(Node):
    """@include[filepath.clpy] — inline-include another .clpy file."""
    path: str = ""


@dataclass
class ModuleNode(Node):
    """@module[name] ... @end — encapsulated module with its own scope."""
    name: str = ""
    body: List[Node] = field(default_factory=list)


@dataclass
class ExportNode(Node):
    """@export[name1; name2; ...] — mark symbols as public in a module."""
    names: List[str] = field(default_factory=list)


@dataclass
class UseNode(Node):
    """@use[path] or @use[path as alias] — load a module file."""
    path: str = ""
    alias: str = ""


@dataclass
class FromNode(Node):
    """@from[module; name1; name2 as alias; ...] — selective import from module."""
    module: str = ""
    imports: List[tuple] = field(default_factory=list)  # [(name, alias), ...]


@dataclass
class RawNode(Node):
    """
    @raw
        # any Python code here
    @end

    Passes content through to Python unchanged.
    The ultimate escape hatch — no Cruhon processing.
    """
    code: str = ""


@dataclass
class ListNode(Node):
    """@list[item1; item2; item3] — creates a Python list literal."""
    items: List[str] = field(default_factory=list)


@dataclass
class DictNode(Node):
    """@dict[key1; val1; key2; val2] — creates a Python dict literal."""
    pairs: List[tuple] = field(default_factory=list)  # [(key, val), ...]


@dataclass
class FetchNode(Node):
    """@fetch[url] — single-line HTTP GET."""
    url: str = ""


# ─────────────────────────────────────────────────────────────
# BLOCK NODES
# ─────────────────────────────────────────────────────────────

@dataclass
class IfNode(Node):
    """@if[cond] ... @elif[cond] ... @else ... @end"""
    condition: str = ""
    body: List[Node] = field(default_factory=list)
    elif_branches: List[tuple] = field(default_factory=list)  # [(condition, body), ...]
    else_body: List[Node] = field(default_factory=list)


@dataclass
class ForNode(Node):
    """@for[i; range(10)] or @for[x; list]"""
    var: str = ""
    iterable: str = ""
    body: List[Node] = field(default_factory=list)


@dataclass
class WhileNode(Node):
    """@while[condition]"""
    condition: str = ""
    body: List[Node] = field(default_factory=list)


@dataclass
class RepeatNode(Node):
    """@repeat[n] — run body n times, no loop variable exposed."""
    count: str = ""
    body: List[Node] = field(default_factory=list)


@dataclass
class FuncNode(Node):
    """@func[name; param1; param2] ... @end"""
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: List[Node] = field(default_factory=list)
    is_async: bool = False


@dataclass
class ClassNode(Node):
    """@class[name; parent?] ... @end"""
    name: str = ""
    parent: Optional[str] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class TryNode(Node):
    """@try ... @catch[e] ... @finally ... @end"""
    body: List[Node] = field(default_factory=list)
    catch_var: str = "e"
    catch_type: Optional[str] = None          # @catch[TypeError; e] or @catch[TypeError]
    catch_body: List[Node] = field(default_factory=list)
    finally_body: List[Node] = field(default_factory=list)


@dataclass
class WithNode(Node):
    """@with[expr as var] ... @end  or  @with[expr] ... @end"""
    expr: str = ""
    var: Optional[str] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class MatchNode(Node):
    """
    @match[value]
        @case[pattern]
            ...
        @default
            ...
    @end
    """
    value: str = ""
    cases: List[tuple] = field(default_factory=list)   # [(pattern, body), ...]
    default_body: List[Node] = field(default_factory=list)


@dataclass
class DelNode(Node):
    """@del[var1; var2]"""
    targets: List[str] = field(default_factory=list)


@dataclass
class RaiseNode(Node):
    """@raise[ExceptionType; message]  or  @raise  (re-raise)"""
    exception: str = ""
    message: Optional[str] = None


@dataclass
class AwaitNode(Node):
    """@await[expr]"""
    expr: str = ""


@dataclass
class AsyncForNode(Node):
    """@async.for[var; iterable] ... @end"""
    var: str = ""
    iterable: str = ""
    body: List[Node] = field(default_factory=list)


@dataclass
class AsyncWithNode(Node):
    """@async.with[expr as var] ... @end  or  @async.with[expr] ... @end"""
    expr: str = ""
    var: Optional[str] = None
    body: List[Node] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# IMPORT / LIB NODES
# ─────────────────────────────────────────────────────────────

@dataclass
class ImportNode(Node):
    """@import[lib] or @import[lib; alias]"""
    lib: str = ""
    alias: Optional[str] = None


@dataclass
class LibCallNode(Node):
    """@requests.get[url] — namespaced library calls"""
    namespace: str = ""
    method: str = ""
    args: List[str] = field(default_factory=list)


@dataclass
class NamespaceCallNode(Node):
    """
    @discord.send["hello"] — mod namespace method call.

    Different from LibCallNode:
    - LibCallNode: stateless, compile-time resolution (stdlib)
    - NamespaceCallNode: stateful, runtime resolution (mods)

    Transpiles to: __ns__["namespace"].call("method", arg1, arg2)
    """
    namespace: str = ""
    method: str = ""
    args: list = field(default_factory=list)


@dataclass
class PassNode(Node):
    """@pass"""
    pass


@dataclass
class GlobalNode(Node):
    """@global[x; y; z]"""
    names: List[str] = field(default_factory=list)


@dataclass
class NonlocalNode(Node):
    """@nonlocal[x; y]"""
    names: List[str] = field(default_factory=list)


@dataclass
class YieldNode(Node):
    """@yield[expr]  or  @yield  or  @yield.from[expr]"""
    value: Optional[str] = None
    is_from: bool = False


@dataclass
class DecorateNode(Node):
    """@decorate[expr] — places @expr above the next function/class."""
    expr: str = ""


@dataclass
class ForeachNode(Node):
    """@foreach[index; var; iterable]  or  @foreach[index; var; iterable; start]"""
    index: str = ""
    var: str = ""
    iterable: str = ""
    start: str = "0"
    body: List[Node] = field(default_factory=list)


@dataclass
class IncNode(Node):
    """@inc[x]  or  @inc[x; n] — augmented add (x += n)"""
    target: str = ""
    amount: str = "1"


@dataclass
class DecNode(Node):
    """@dec[x]  or  @dec[x; n] — augmented subtract (x -= n)"""
    target: str = ""
    amount: str = "1"


@dataclass
class SwapNode(Node):
    """@swap[a; b] — tuple swap (a, b = b, a)"""
    left: str = ""
    right: str = ""


@dataclass
class PluginBlockNode(Node):
    """
    Generic block node for plugin-defined block commands.

    Plugins that use api.block_command() get their body wrapped in
    this node without needing to define a custom dataclass.

    plugin_name: full command name as registered (e.g. "route", "todo")
    args: positional arguments from the command header
    kwargs: keyword arguments from the command header
    body: parsed child nodes between header and @end
    """
    plugin_name: str = ""
    args: List[str] = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)
    body: List[Node] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# MOD SYSTEM — dynamic node registration
# ─────────────────────────────────────────────────────────────

_CUSTOM_NODES: dict[str, type] = {}


def register_node(name: str, node_class: type):
    """
    Mods can register new AST node types.

    Example (inside a mod):
        from cruhon.core.ast_nodes import register_node, Node

        @dataclass
        class DbGetNode(Node):
            table: str = ""
            key: str = ""

        register_node("db_get", DbGetNode)
    """
    _CUSTOM_NODES[name] = node_class


def get_custom_node(name: str) -> Optional[type]:
    return _CUSTOM_NODES.get(name)


def all_nodes() -> dict:
    """All nodes — core + mod nodes."""
    return {**globals(), **_CUSTOM_NODES}
