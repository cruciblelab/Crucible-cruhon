"""
cruhon/core/transpiler.py
=========================
AST → Python source code

Each Node type has a visit_* method.
Mods can add new visit methods via register_visitor().

v0.5: _interpolate() and _as_string() replaced by a single
      _eval_value(value, context) method.
"""

from __future__ import annotations
import re
from typing import List, Callable
from .ast_nodes import *


class TranspileError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(f"[TranspileError] Line {line} — {msg}")
        self.line = line


class Transpiler:
    """
    Converts an AST to Python code.

    Mod system:
      - register_visitor(node_class, fn) for new node support
      - pre_hooks: AST manipulation before code generation
      - post_hooks: manipulation of generated Python code

    Line mapping:
      _line_map maps generated Python line numbers → Cruhon source lines.
      Used by runner.py to produce helpful error messages.
    """

    def __init__(self):
        self._indent = 0
        self._custom_visitors: dict = {}
        self._block_visitors: dict = {}   # plugin_name → visitor_fn for PluginBlockNode
        self._pre_hooks: list = []
        self._post_hooks: list = []
        # Line map: python_line (1-based) → cruhon_line
        self._line_map: dict[int, int] = {}
        self._python_line: int = 1

    # ── Mod API ───────────────────────────────────────────────

    def register_visitor(self, node_class: type, fn: Callable):
        """
        Register a visitor for a new node type.

        Example:
            def visit_db_get(transpiler, node):
                return transpiler._line(f"db.get({node.table!r}, {node.key!r})")

            transpiler.register_visitor(DbGetNode, visit_db_get)
        """
        self._custom_visitors[node_class.__name__] = fn

    def add_pre_hook(self, fn: Callable):
        self._pre_hooks.append(fn)

    def add_post_hook(self, fn: Callable):
        self._post_hooks.append(fn)

    # ── Main transpile ────────────────────────────────────────

    def transpile(self, ast: ProgramNode) -> str:
        self._indent = 0
        self._line_map = {}
        self._python_line = 1

        # Pre-hooks
        for hook in self._pre_hooks:
            ast = hook(ast)

        lines = []

        # Collect lib imports at top
        import_lines = self._collect_imports(ast)
        if import_lines:
            lines.extend(import_lines)
            # Count the import lines to keep _python_line in sync
            self._python_line += len(import_lines) + 1  # +1 for blank line
            lines.append("")

        # Main code
        for node in ast.body:
            if not isinstance(node, (ImportNode, IncludeNode)):
                result = node.accept(self)
                if result:
                    lines.append(result)

        code = "\n".join(lines)

        # Post-hooks
        for hook in self._post_hooks:
            code = hook(code)

        return code

    def _collect_imports(self, ast: ProgramNode) -> List[str]:
        """Collect ImportNodes and any auto-required imports."""
        from .registry import get_lib
        lines = []
        seen = set()

        # Explicit @import statements
        for node in ast.body:
            if isinstance(node, ImportNode):
                lib_module = get_lib(node.lib)
                if lib_module is None:
                    raise TranspileError(
                        f"Library '{node.lib}' is not yet supported in Cruhon. "
                        f"See library.md for the full list.",
                        node.line
                    )
                alias = f" as {node.alias}" if node.alias else ""
                stmt = f"import {lib_module}{alias}"
                if stmt not in seen:
                    seen.add(stmt)
                    lines.append(stmt)

        # Auto-inject os when @env is used
        if _needs_os_import(ast):
            stmt = "import os"
            if stmt not in seen:
                seen.add(stmt)
                lines.insert(0, stmt)

        # Auto-inject requests when @fetch is used
        if _needs_requests_import(ast):
            stmt = "import requests"
            if stmt not in seen:
                seen.add(stmt)
                lines.append(stmt)

        # Auto-inject store helpers when @store.* is used
        store_helpers = _needs_store_helpers(ast)
        if store_helpers:
            for hl in store_helpers.splitlines():
                lines.append(hl)

        return lines

    # ── Line emit ─────────────────────────────────────────────

    def _line(self, code: str, cruhon_line: int = 0) -> str:
        """Emit one indented line of Python, recording its source map entry."""
        if cruhon_line > 0:
            self._line_map[self._python_line] = cruhon_line
        self._python_line += 1
        return "    " * self._indent + code

    def _block(self, nodes: List[Node]) -> str:
        self._indent += 1
        lines = []
        for node in nodes:
            result = node.accept(self)
            if result:
                lines.append(result)
        self._indent -= 1
        return "\n".join(lines) if lines else self._line("pass")

    # ── Single evaluation rule ────────────────────────────────

    def _eval_value(self, value: str, context: str = "expr") -> str:
        """
        Single evaluation rule for all values in Cruhon.

        context:
          "expr"    — right-hand side of @var, @return, @const, @fetch url
                      identifiers remain as Python identifiers (variable references)
          "display" — @print value, @assert message
                      bare identifiers become string literals

        Priority order (strict):

          1. Quoted string without {} → string literal as-is
          2. Quoted string with {}    → f-string
          3. Numeric literal          → as-is
          4. True / False / None      → as-is
          5. Collection literal       → as-is (starts with [ { ( )
          6. Python expression        → as-is (contains operator/call/dot/subscript)
          7a. [expr]    Single identifier → Python identifier (variable reference)
          7b. [display] Single identifier → string literal "ident"
          8. Bare text (anything else) → string literal "text"
        """
        v = value.strip()

        # ── Rule 1: quoted string, no interpolation ───────────
        if (v.startswith('"') and v.endswith('"') and len(v) >= 2) or \
           (v.startswith("'") and v.endswith("'") and len(v) >= 2):
            inner = v[1:-1]
            if "{" in inner and "}" in inner:
                # Rule 2: quoted + {} → f-string
                return f"f{v}"
            return v

        # ── Rule 2 (unquoted): bare {var} interpolation ───────
        # Fires when value contains {} BUT is NOT a Python expression
        # with dict literals. Two helpers below make the distinction.
        if "{" in v and "}" in v:
            if self._is_python_expression(v):
                return v          # pass through as Python expression (Rule 6 territory)
            if self._is_fstring_template(v):
                return f'f"{v}"'  # wrap as f-string
            # fallthrough: ambiguous — treat as expression (safe default)
            return v

        # ── Rule 3: numeric literal ───────────────────────────
        try:
            float(v)
            return v
        except ValueError:
            pass

        # ── Rule 4: True / False / None ───────────────────────
        if v in ("True", "False", "None"):
            return v

        # ── Rule 5: collection literal ────────────────────────
        if (v.startswith("{") and v.endswith("}")) or \
           (v.startswith("[") and v.endswith("]")) or \
           (v.startswith("(") and v.endswith(")")):
            return v

        # ── Rule 6: Python expression ─────────────────────────
        # In display context, only treat as expression if it has call/subscript/dot
        # (things that unambiguously look like Python). Operators alone are not
        # enough — "x is great" contains " is " but is not a Python expression.
        operators = [
            "+", "-", "*", "/", "%", "**", "//",
            "==", "!=", ">=", "<=", ">", "<",
            " and ", " or ", " not ", " in ", " is ",
            " not in ", " is not ",
        ]
        has_operator = any(op in v for op in operators)
        has_call = "(" in v and ")" in v
        has_subscript = "[" in v and "]" in v
        has_dot = "." in v

        if context == "expr":
            if has_operator or has_call or has_subscript or has_dot:
                return v
        else:
            # display: only pass through if it has structural expression markers
            # (call, subscript, dot) — operators alone could be inside plain text
            if has_call or has_subscript or has_dot:
                return v

        # ── Rule 7: single identifier ─────────────────────────
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            if context == "expr":
                return v           # 7a: variable reference
            else:
                return f'"{v}"'    # 7b: display — treat as string

        # ── Rule 8: bare text → string literal ────────────────
        return f'"{v}"'

    def _is_fstring_template(self, value: str) -> bool:
        """
        True if value is a genuine f-string interpolation template —
        i.e. contains {identifier} or {expression} meant for substitution.

        Returns False for Python expressions that happen to contain braces
        (dict literals, sets, format specs inside function calls).
        """
        import re
        if "{" not in value or "}" not in value:
            return False
        # Python expressions are never f-string templates
        if self._is_python_expression(value):
            return False
        # Must contain at least one {identifier} or {expression} pattern
        return bool(re.search(r'\{[a-zA-Z_][a-zA-Z0-9_. ]*\}', value))

    def _is_python_expression(self, value: str) -> bool:
        """
        True if value is a Python expression containing braces as dict
        literals or function arguments — NOT f-string interpolation templates.

        Cases handled:
          func({"key": val})   — function call with dict arg
          __import__('x')(…)   — stdlib inline call with dict
          {"key": val}         — plain dict literal
          {key: val}           — dict with variable key
          await expr           — async expression
        """
        import re
        brace_pos = value.find("{")
        if brace_pos == -1:
            return False

        # Rule 1: function call ( appears before first {  → dict inside a call
        paren_pos = value.find("(")
        if paren_pos != -1 and paren_pos < brace_pos:
            return True

        # Rule 2: { immediately followed by quote → {"key": ...} dict literal
        if re.search(r'\{["\']', value):
            return True

        # Rule 3: starts with { and contains : → plain dict literal {key: val}
        if value.startswith("{") and ":" in value:
            return True

        # Rule 4: assignment (=) before the first { → var = {"key": val}
        eq_pos = value.find("=")
        if eq_pos != -1 and eq_pos < brace_pos:
            return True

        return False

    def visit_unknown(self, node: Node) -> str:
        """Unknown node — check mod visitors."""
        node_name = node.__class__.__name__
        if node_name in self._custom_visitors:
            return self._custom_visitors[node_name](self, node)
        return self._line(f"# Unknown node: {node_name}")

    # ── Core visitors ─────────────────────────────────────────

    def visit_ProgramNode(self, node: ProgramNode) -> str:
        lines = []
        for child in node.body:
            result = child.accept(self)
            if result:
                lines.append(result)
        return "\n".join(lines)

    def visit_PrintNode(self, node: PrintNode) -> str:
        value = self._eval_value(str(node.value), "display")
        return self._line(f"print({value})", node.line)

    def visit_InputNode(self, node: InputNode) -> str:
        prompt = self._eval_value(str(node.prompt), "display") if node.prompt else '""'
        return self._line(f"input({prompt})", node.line)

    def visit_VarNode(self, node: VarNode) -> str:
        value = self._eval_value(str(node.value), "expr")
        return self._line(f"{node.name} = {value}", node.line)

    def visit_ConstNode(self, node: ConstNode) -> str:
        value = self._eval_value(str(node.value), "expr")
        return self._line(f"{node.name} = {value}  # const", node.line)

    def visit_AssertNode(self, node: AssertNode) -> str:
        msg = self._eval_value(str(node.message), "display") if node.message else '""'
        return self._line(f"assert {node.condition}, {msg}", node.line)

    def visit_EnvNode(self, node: EnvNode) -> str:
        """
        @env as a statement. When nested inside @var the parser inlines it.
        """
        if node.default is not None:
            return self._line(f'os.environ.get("{node.key}", {node.default})', node.line)
        return self._line(f'os.environ.get("{node.key}")', node.line)

    def visit_IncludeNode(self, node: IncludeNode) -> str:
        """IncludeNode should have been resolved by runner.py before transpilation."""
        return self._line(f"# @include[{node.path}] — not resolved", node.line)

    def visit_RawNode(self, node) -> str:
        """
        @raw blocks pass through unchanged.
        Each line is indented to current block level.
        """
        if not node.code.strip():
            return ""
        lines = node.code.splitlines()
        indented = []
        for line in lines:
            if line.strip():
                indented.append(self._line(line, node.line))
            else:
                indented.append("")
        return "\n".join(indented)

    def visit_ListNode(self, node: ListNode) -> str:
        """@list as a statement."""
        items = ", ".join(node.items)
        return self._line(f"[{items}]", node.line)

    def visit_DictNode(self, node: DictNode) -> str:
        """@dict as a statement."""
        pairs = ", ".join(f"{k}: {v}" for k, v in node.pairs)
        return self._line("{" + pairs + "}", node.line)

    def visit_FetchNode(self, node: FetchNode) -> str:
        """@fetch as a statement."""
        url = self._eval_value(str(node.url), "expr")
        return self._line(f"requests.get({url})", node.line)

    def visit_ReturnNode(self, node: ReturnNode) -> str:
        value = self._eval_value(str(node.value), "expr")
        return self._line(f"return {value}", node.line)

    def visit_BreakNode(self, node: BreakNode) -> str:
        return self._line("break", node.line)

    def visit_ContinueNode(self, node: ContinueNode) -> str:
        return self._line("continue", node.line)

    def visit_ExprNode(self, node: ExprNode) -> str:
        return self._line(node.expr, node.line)

    def visit_AwaitNode(self, node: AwaitNode) -> str:
        return self._line(f"await {node.expr}", node.line)

    def visit_ImportNode(self, node: ImportNode) -> str:
        return ""  # handled in _collect_imports

    def visit_IfNode(self, node: IfNode) -> str:
        lines = [self._line(f"if {node.condition}:", node.line)]
        lines.append(self._block(node.body))

        for cond, body in node.elif_branches:
            lines.append(self._line(f"elif {cond}:"))
            lines.append(self._block(body))

        if node.else_body:
            lines.append(self._line("else:"))
            lines.append(self._block(node.else_body))

        return "\n".join(lines)

    def visit_ForNode(self, node: ForNode) -> str:
        lines = [self._line(f"for {node.var} in {node.iterable}:", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_WhileNode(self, node: WhileNode) -> str:
        lines = [self._line(f"while {node.condition}:", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_RepeatNode(self, node: RepeatNode) -> str:
        lines = [self._line(f"for _ in range({node.count}):", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_FuncNode(self, node: FuncNode) -> str:
        params = ", ".join(node.params)
        prefix = "async " if node.is_async else ""
        lines = [self._line(f"{prefix}def {node.name}({params}):", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_ClassNode(self, node: ClassNode) -> str:
        parent = f"({node.parent})" if node.parent else ""
        lines = [self._line(f"class {node.name}{parent}:", node.line)]
        lines.append(self._block(node.body))
        return "\n".join(lines)

    def visit_TryNode(self, node: TryNode) -> str:
        lines = [self._line("try:", node.line)]
        lines.append(self._block(node.body))
        lines.append(self._line(f"except Exception as {node.catch_var}:"))
        lines.append(self._block(node.catch_body))
        if node.finally_body:
            lines.append(self._line("finally:"))
            lines.append(self._block(node.finally_body))
        return "\n".join(lines)

    def visit_LibCallNode(self, node: LibCallNode) -> str:
        from .registry import get_lib_call
        handler = get_lib_call(node.namespace, node.method)
        if handler:
            return self._line(handler(node.args), node.line)
        # Fallback: direct Python call
        args = ", ".join(f'"{a}"' if not a.startswith('"') else a for a in node.args)
        return self._line(f"{node.namespace}.{node.method}({args})", node.line)

    def visit_PluginBlockNode(self, node) -> str:
        """
        Dispatch to the plugin's registered visitor.
        If no visitor is registered, emit a comment so the program still runs.
        """
        visitor = self._block_visitors.get(node.plugin_name)
        if visitor:
            return visitor(self, node)
        return self._line(f"# @{node.plugin_name} block (no visitor registered)", node.line)

    def visit_NamespaceCallNode(self, node) -> str:
        """
        Generates runtime namespace dispatch code.

        @discord.send["hello"]
        → __ns__["discord"].call("send", "hello")

        Args are passed as positional arguments to Namespace.call().
        """
        args_str = ", ".join(
            self._eval_value(a, "expr") for a in node.args
        )
        if args_str:
            return self._line(
                f'__ns__["{node.namespace}"].call("{node.method}", {args_str})',
                node.line
            )
        return self._line(
            f'__ns__["{node.namespace}"].call("{node.method}")',
            node.line
        )


# ─────────────────────────────────────────────────────────────
# AST WALK HELPERS (used for auto-imports)
# ─────────────────────────────────────────────────────────────

def _walk_ast(node):
    """Yield all nodes in the AST recursively."""
    yield node
    for attr in ("body", "else_body", "catch_body", "finally_body"):
        children = getattr(node, attr, None)
        if children:
            for child in children:
                yield from _walk_ast(child)
    if hasattr(node, "elif_branches"):
        for _cond, branch_body in (node.elif_branches or []):
            for child in branch_body:
                yield from _walk_ast(child)


def _needs_os_import(ast) -> bool:
    """Return True if the AST contains any EnvNode, or parser saw inline @env."""
    from .parser import get_parser
    if get_parser()._needs_os:
        return True
    return any(isinstance(n, EnvNode) for n in _walk_ast(ast))


def _needs_requests_import(ast) -> bool:
    """Return True if the AST contains any FetchNode, or parser saw inline @fetch."""
    from .parser import get_parser
    if get_parser()._needs_requests:
        return True
    return any(isinstance(n, FetchNode) for n in _walk_ast(ast))


def _needs_store_helpers(ast) -> str:
    """
    Return store helper code string if any @store.* LibCallNode is found,
    empty string otherwise.
    """
    for node in _walk_ast(ast):
        if isinstance(node, LibCallNode) and node.namespace == "store":
            return _STORE_HELPERS
    return ""


_STORE_HELPERS = """\
import json as __json
import os as __os

def __cruhon_store_path():
    return __os.path.join(__os.getcwd(), ".cruhon_store.json")

def __cruhon_store_load():
    p = __cruhon_store_path()
    if __os.path.exists(p):
        with open(p) as f:
            return __json.load(f)
    return {}

def __cruhon_store_set(key, value):
    d = __cruhon_store_load()
    d[key] = value
    with open(__cruhon_store_path(), "w") as f:
        __json.dump(d, f)

def __cruhon_store_get(key, default=None):
    return __cruhon_store_load().get(key, default)

def __cruhon_store_delete(key):
    d = __cruhon_store_load()
    d.pop(key, None)
    with open(__cruhon_store_path(), "w") as f:
        __json.dump(d, f)
"""


# ─────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────

_transpiler_instance = Transpiler()


def get_transpiler() -> Transpiler:
    return _transpiler_instance


def transpile(ast) -> str:
    return _transpiler_instance.transpile(ast)
